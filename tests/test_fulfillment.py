# tests/test_fulfillment.py
import pytest
from fulfillment.fulfillment import FulfillmentSystem, MAX_PACKAGE_G

# ---------------------------------------------------------------------
# init_catalog tests
# ---------------------------------------------------------------------


def test_init_catalog_sets_inventory_zero():
    system = FulfillmentSystem()

    product_info = [
        {"product_id": 1, "mass_g": 500, "product_name": "Test Product A"},
        {"product_id": 2, "mass_g": 300, "product_name": "Test Product B"},
    ]

    system.init_catalog(product_info)

    # catalog entries exist and have the right mass
    assert 1 in system.catalog
    assert system.catalog[1]["mass_g"] == 500
    assert 2 in system.catalog
    assert system.catalog[2]["mass_g"] == 300

    # inventory initialized to zero for each product_id
    assert system.inventory[1] == 0
    assert system.inventory[2] == 0


def test_init_catalog_rejects_heavy_product():
    system = FulfillmentSystem()

    heavy_product = {"product_id": 99, "mass_g": MAX_PACKAGE_G + 1, "product_name": "Too Heavy"}

    with pytest.raises(ValueError):
        system.init_catalog([heavy_product])


# ---------------------------------------------------------------------
# _pack_shipments tests
# ---------------------------------------------------------------------


def test_pack_shipments_splits_when_exceeds_max_weight():
    system = FulfillmentSystem()

    # Minimal catalog setup
    system.catalog = {
        1: {"mass_g": 700, "product_name": "A"},
        2: {"mass_g": 300, "product_name": "B"},
    }

    # 3 units of product 1 → 3 * 700 = 2100g
    # Since MAX_PACKAGE_G = 1800, this should split into 2 packages
    items_to_ship = {1: 3}

    packages = system._pack_shipments(items_to_ship)

    # Expect 2 packages
    assert len(packages) == 2

    # First package should contain 2 units (1400g)
    assert packages[0][1] == 2

    # Second package should contain 1 unit (700g)
    assert packages[1][1] == 1

    # Verify no package exceeds MAX_PACKAGE_G
    for package in packages:
        total_weight = 0
        for pid, qty in package.items():
            total_weight += system.catalog[pid]["mass_g"] * qty
        assert total_weight <= MAX_PACKAGE_G

    # Verify total quantity matches original request
    total_units = sum(pkg.get(1, 0) for pkg in packages)
    assert total_units == 3


def test_pack_shipments_multiple_products():
    system = FulfillmentSystem()

    system.catalog = {
        1: {"mass_g": 700, "product_name": "A"},
        2: {"mass_g": 300, "product_name": "B"},
    }

    # 2x700 + 2x300 = 2000g → must split
    items_to_ship = {1: 2, 2: 2}

    packages = system._pack_shipments(items_to_ship)

    # Ensure total units match
    total_1 = sum(pkg.get(1, 0) for pkg in packages)
    total_2 = sum(pkg.get(2, 0) for pkg in packages)

    assert total_1 == 2
    assert total_2 == 2

    # Ensure no package exceeds limit
    for package in packages:
        total_weight = sum(
            system.catalog[pid]["mass_g"] * qty
            for pid, qty in package.items()
        )
        assert total_weight <= MAX_PACKAGE_G


# ---------------------------------------------------------------------
# process_order tests
# ---------------------------------------------------------------------

def _simple_packer(items_to_ship):
    """
    Deterministic packer for tests: return a single package that contains the whole items_to_ship map.
    This isolates process_order behavior from packing heuristics.
    """
    if not items_to_ship:
        return []
    return [dict(items_to_ship)]


def test_process_order_full_fulfill_ships_and_decrements_inventory():
    system = FulfillmentSystem()

    # Setup catalog and inventory
    system.catalog = {1: {"mass_g": 500, "product_name": "P1"}}
    system.inventory = {1: 5}

    # Stub the packer to be deterministic
    system._pack_shipments = _simple_packer

    # Capture shipments
    shipped = []

    def capture_ship(shipment):
        shipped.append(shipment)

    system.ship_package = capture_ship

    # Order requesting 2 units -> inventory has 5 so full fulfillment
    order = {"order_id": 10, "requested": [{"product_id": 1, "quantity": 2}]}
    system.process_order(order)

    # One shipment recorded
    assert len(shipped) == 1
    assert shipped[0]["order_id"] == 10
    assert shipped[0]["shipped"] == [{"product_id": 1, "quantity": 2}]

    # Inventory decremented
    assert system.inventory[1] == 3

    # No pending orders
    assert len(system.pending_orders) == 0


def test_process_order_partial_fulfill_creates_pending():
    system = FulfillmentSystem()

    # Setup catalog and inventory (only 1 available)
    system.catalog = {1: {"mass_g": 500, "product_name": "P1"}}
    system.inventory = {1: 1}

    # Stub packer and capture shipments
    system._pack_shipments = _simple_packer
    shipped = []
    system.ship_package = lambda s: shipped.append(s)

    # Request 3 units; only 1 can be allocated -> remaining 2 pending
    order = {"order_id": 11, "requested": [{"product_id": 1, "quantity": 3}]}
    system.process_order(order)

    # One shipment with 1 unit
    assert len(shipped) == 1
    assert shipped[0]["shipped"] == [{"product_id": 1, "quantity": 1}]

    # Inventory is zero now
    assert system.inventory[1] == 0

    # Pending orders contains one entry with remaining 2
    assert len(system.pending_orders) == 1
    pending = system.pending_orders[0]
    assert pending["order_id"] == 11
    assert pending["remaining"] == {1: 2}


def test_process_order_ignores_zero_quantity_lines():
    system = FulfillmentSystem()

    system.catalog = {1: {"mass_g": 500, "product_name": "P1"}}
    system.inventory = {1: 10}
    system._pack_shipments = _simple_packer

    shipped = []
    system.ship_package = lambda s: shipped.append(s)

    # Include a zero-quantity and a normal line
    order = {
        "order_id": 12,
        "requested": [
            {"product_id": 1, "quantity": 0},
            {"product_id": 1, "quantity": 2},
        ],
    }

    system.process_order(order)

    # Only the positive line should be processed: one shipment for 2 units
    assert len(shipped) == 1
    assert shipped[0]["shipped"] == [{"product_id": 1, "quantity": 2}]
    assert system.inventory[1] == 8  # 10 - 2
    assert len(system.pending_orders) == 0


def test_process_order_unknown_product_raises():
    system = FulfillmentSystem()

    # catalog does NOT contain product 99
    system.catalog = {1: {"mass_g": 500, "product_name": "P1"}}
    system.inventory = {1: 5}

    order = {"order_id": 13, "requested": [{"product_id": 99, "quantity": 1}]}

    with pytest.raises(ValueError):
        system.process_order(order)


def test_process_order_negative_quantity_raises():
    system = FulfillmentSystem()

    system.catalog = {1: {"mass_g": 500, "product_name": "P1"}}
    system.inventory = {1: 5}

    order = {"order_id": 14, "requested": [{"product_id": 1, "quantity": -1}]}

    with pytest.raises(ValueError):
        system.process_order(order)
