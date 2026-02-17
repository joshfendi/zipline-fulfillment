"""
FulfillmentSystem scaffold for Zipline take-home.

Validation rules:
- Unknown product_id in an orders/restocks: **raise ValueError**.
- Negative quantities in orders/restocks: **raise ValueError**.
- Zero quantities in orders/restocks: **ignore** (no-op).

Packing constraint:
- MAX_PACKAGE_G = 1800  # grams (1.8kg); no single package shipped may exceed this.
"""

from typing import List, Dict, Deque, Any
from collections import deque
import logging

MAX_PACKAGE_G = 1800

# Configure module-level logger (consumers may reconfigure as needed)
logger = logging.getLogger("fulfillment")
if not logger.handlers:
    # Basic configuration only for development/demo purposes
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class FulfillmentSystem:
    """
    Lightweight in-memory fulfillment system for a Zipline "nest".

    State:
      - catalog: product_id -> {"mass_g": int, "product_name": str}
      - inventory: product_id -> quantity (int)
      - pending_orders: deque of {"order_id": int, "remaining": {product_id: qty}}
      - orders_log: product-order audit/history useful for debugging

    Input validation rules (see module docstring):
      - Unknown product_id -> raise ValueError
      - Negative quantity -> raise ValueError
      - Zero quantity -> ignore
    """

    def __init__(self) -> None:
        """Initialize empty state. Call init_catalog(...) before processing orders/restocks."""
        # product_id -> {"mass_g": int, "product_name": str}
        self.catalog: Dict[int, Dict[str, Any]] = {}

        # product_id -> available_qty
        self.inventory: Dict[int, int] = {}

        # deque of pending orders, FIFO:
        # each entry: {"order_id": int, "remaining": {product_id: qty}, "original": {...}}
        self.pending_orders: Deque[Dict[str, Any]] = deque()

        # orders_log: order_id -> metadata for debugging (requested, shipped_history, status)
        # Lightweight in-memory for the take-home; in prod this would be persisted.
        self.orders_log: Dict[int, Dict[str, Any]] = {}

    def init_catalog(self, product_info: List[Dict[str, Any]]) -> None:
        """
        Initialize the product catalog. Called once at startup.

        Example product_info:
        [
          {"mass_g":700,"product_name":"RBC A+ Adult","product_id":0},
          {"mass_g":300,"product_name":"FFP A+","product_id":10},
          ...
        ]

        After this call:
          - self.catalog populated with product metadata
          - self.inventory initialized with 0 for every product_id in catalog

        Raises:
          - ValueError if duplicate product_id or if mass_g exceeds MAX_PACKAGE_G.
        """

        # Reset state in case of re-initialization
        self.catalog.clear()
        self.inventory.clear()

        for product in product_info:
            pid = int(product["product_id"])
            mass = int(product["mass_g"])
            name = product["product_name"]

            # Validate catalog entries
            if pid in self.catalog:
                raise ValueError(f"Duplicate product_id in catalog: {pid}")
            if mass > MAX_PACKAGE_G:
                raise ValueError(f"Product {pid} mass {mass}g exceeds MAX_PACKAGE_G {MAX_PACKAGE_G}g")
            
            # Initialize catalog and inventory
            self.catalog[pid] = {"mass_g": mass, "product_name": name}
            self.inventory[pid] = 0  # Initialize inventory to 0 for each product_id

    def process_order(self, order: Dict[str, Any]) -> None:
        """
        Process an incoming order.

        Example order:
        {
          "order_id": 123,
          "requested": [
            {"product_id": 0, "quantity": 2},
            {"product_id": 10, "quantity": 4}
          ]
        }

        Responsibilities (to be implemented):
          - Validate inputs per module rules (unknown id -> ValueError; negative -> ValueError; zero -> ignore)
          - Attempt to allocate from self.inventory
          - Ship available items immediately via ship_package (may require multiple packages)
          - Ensure no package exceeds MAX_PACKAGE_G
          - If some items cannot be fulfilled, append a pending order entry to self.pending_orders
          - Record request/ship events in self.orders_log for debugging/audit
        """
        pass

    def process_restock(self, restock: List[Dict[str, Any]]) -> None:
        """
        Add inventory from a restock and re-attempt pending orders.

        Example restock:
        [
          {"product_id": 0, "quantity": 30},
          {"product_id": 10, "quantity": 5}
        ]

        Responsibilities (to be implemented):
          - Validate inputs per module rules (unknown id -> ValueError; negative -> ValueError; zero -> ignore)
          - Increment self.inventory for each restock item
          - Iterate pending orders (FIFO) and attempt to fulfill them,
            shipping available items and updating/removing pending entries
          - Update self.orders_log with shipping events
        """
        # TODO: implement restock handling and pending order reprocessing
        pass

    def ship_package(self, shipment: Dict[str, Any]) -> None:
        """
        Stub for shipping a package. In production this would integrate with the packing UI.

        Example shipment:
        {
          "order_id": 123,
          "shipped": [
            {"product_id": 0, "quantity": 1},
            {"product_id": 10, "quantity": 2}
          ],
          "package_id": "optional-id"
        }

        Current behavior (scaffold):
          - Log the shipment at INFO level using the module logger.
          - Tests can capture/inspect logger output instead of stdout.

        Note: use logging in place of print so outputs can be redirected and structured.
        """
        # Minimal logging behavior for scaffold. Implementation may include richer metadata.
        logger.info("ship_package: %s", shipment)

    # ----- Helper methods (private) -----

    def _pack_shipments(self, items_to_ship: Dict[int, int]) -> List[List[Dict[str, int]]]:
        """
        Split items_to_ship (product_id -> quantity) into a list of packages where
        each package is a list of {"product_id": int, "quantity": int} and the
        total mass of each package does not exceed MAX_PACKAGE_G.

        Use a simple greedy packing strategy (unit-aware). Do NOT implement optimal
        bin packing for the take-home.

        NOTE: this is a stub in the scaffold. Implement the algorithm in the main task.
        """
        # TODO: implement greedy unit-aware packing to respect MAX_PACKAGE_G
        return []

    def _record_order_request(self, order: Dict[str, Any]) -> None:
        """
        Add an entry to orders_log for a newly received order.

        Suggested structure (not enforced here):
          self.orders_log[order_id] = {
              "requested": {pid: qty, ...},
              "shipped_history": [],  # list of shipments
              "status": "pending" | "completed"
          }

        This helper keeps the logging/audit concern separate from allocation logic.
        """
        # TODO: implement lightweight orders_log recording for debugging/audit
        pass
