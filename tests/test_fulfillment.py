import pytest
from fulfillment.fulfillment import FulfillmentSystem, MAX_PACKAGE_G


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
