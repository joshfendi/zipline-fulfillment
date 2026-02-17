# driver.py
"""
Simple driver script to exercise FulfillmentSystem manually.

Run from repo root:
    source venv/bin/activate   # if using venv
    python driver.py

This script:
- Initializes catalog using provided example product_info
- Restocks inventory
- Runs a few order scenarios:
  * full fulfillment
  * splitting due to weight limit
  * partial fulfillment -> pending, then restock to complete pending
- Prints inventory, pending orders, and shipment output to console

Note: driver overrides `ship_package` to print shipments to console so you can
see them regardless of logger configuration in the class.
"""

from typing import List, Dict, Any
from pprint import pprint
from collections import deque

from fulfillment.fulfillment import FulfillmentSystem

EXAMPLE_PRODUCT_INFO: List[Dict[str, Any]] = [
    {"mass_g": 700, "product_name": "RBC A+ Adult", "product_id": 0},
    {"mass_g": 700, "product_name": "RBC B+ Adult", "product_id": 1},
    {"mass_g": 750, "product_name": "RBC AB+ Adult", "product_id": 2},
    {"mass_g": 680, "product_name": "RBC O- Adult", "product_id": 3},
    {"mass_g": 350, "product_name": "RBC A+ Child", "product_id": 4},
    {"mass_g": 200, "product_name": "RBC AB+ Child", "product_id": 5},
    {"mass_g": 120, "product_name": "PLT AB+", "product_id": 6},
    {"mass_g": 80, "product_name": "PLT O+", "product_id": 7},
    {"mass_g": 40, "product_name": "CRYO A+", "product_id": 8},
    {"mass_g": 80, "product_name": "CRYO AB+", "product_id": 9},
    {"mass_g": 300, "product_name": "FFP A+", "product_id": 10},
    {"mass_g": 300, "product_name": "FFP B+", "product_id": 11},
    {"mass_g": 300, "product_name": "FFP AB+", "product_id": 12},
]


def main() -> None:
    system = FulfillmentSystem()

    # ensure ship_package prints to console for manual inspection
    def print_ship(shipment: Dict[str, Any]) -> None:
        print("SHIPMENT:", shipment)

    system.ship_package = print_ship

    print("=== Initializing catalog ===")
    system.init_catalog(EXAMPLE_PRODUCT_INFO)
    print("Catalog product_ids:", sorted(system.catalog.keys()))
    print()

    # Scenario 1: simple restock so we can fulfill some orders immediately
    print("=== Restock scenario 1 ===")
    restock_1 = [{"product_id": 10, "quantity": 5}, {"product_id": 0, "quantity": 1}]
    print("Restocking:", restock_1)
    system.process_restock(restock_1)
    print("Inventory after restock 1:")
    pprint(system.inventory)
    print("Pending orders:", list(system.pending_orders))
    print()

    # Scenario 2: full fulfillment: order that fits in inventory
    print("=== Full fulfillment (order 100) ===")
    order_full = {"order_id": 100, "requested": [{"product_id": 10, "quantity": 2}]}
    print("Order:", order_full)
    system.process_order(order_full)
    print("Inventory after order 100:")
    pprint(system.inventory)
    print("Pending orders:", list(system.pending_orders))
    print()

    # Scenario 3: splitting due to weight: 3 * 700g -> needs 2 packages
    print("=== Prepare splitting test: restock product 0 qty=3 ===")
    system.process_restock([{"product_id": 0, "quantity": 3}])
    print("Inventory after restock for splitting test:")
    pprint(system.inventory)
    print()

    print("=== Split-required order (order 101): 3 x product 0 (700g each) ===")
    order_split = {"order_id": 101, "requested": [{"product_id": 0, "quantity": 3}]}
    system.process_order(order_split)
    print("Inventory after order 101:")
    pprint(system.inventory)
    print("Pending orders:", list(system.pending_orders))
    print()

    # Scenario 4: partial fulfillment -> pending, then restock completes pending
    print("=== Partial fulfillment (order 102) requesting product 1 qty=4 ===")
    order_partial = {"order_id": 102, "requested": [{"product_id": 1, "quantity": 4}]}
    system.process_order(order_partial)
    print("Inventory after order 102:")
    pprint(system.inventory)
    print("Pending orders:", list(system.pending_orders))
    print()

    print("=== Restock to complete pending (product 1 qty=4) ===")
    system.process_restock([{"product_id": 1, "quantity": 4}])
    print("Inventory after completing restock:")
    pprint(system.inventory)
    print("Pending orders:", list(system.pending_orders))
    print()

    # Scenario 5: demonstrate zero/negative handling (will raise for negative)
    print("=== Zero-quantity restock/order are ignored; negative raises ===")
    try:
        print("Attempting restock with zero qty (should be ignored):")
        system.process_restock([{"product_id": 10, "quantity": 0}])
        print("Inventory (unchanged):")
        pprint(system.inventory)
    except Exception as e:
        print("Unexpected error for zero qty restock:", e)

    try:
        print("Attempting to process an order with negative quantity (should raise):")
        system.process_order({"order_id": 200, "requested": [{"product_id": 10, "quantity": -1}]})
    except Exception as e:
        print("Expected error for negative quantity:", type(e).__name__, str(e))
    print()

    # Final state snapshot
    print("=== Final inventory snapshot ===")
    pprint(system.inventory)
    print("=== Final pending orders ===")
    pprint(list(system.pending_orders))
    print("=== Done ===")


if __name__ == "__main__":
    main()
