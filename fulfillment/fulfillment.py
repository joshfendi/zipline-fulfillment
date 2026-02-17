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

MAX_PACKAGE_G = 1800

class FulfillmentSystem:
    """
    Lightweight in-memory fulfillment system for a Zipline "nest".

    State:
      - catalog: product_id -> {"mass_g": int, "product_name": str}
      - inventory: product_id -> quantity (int)
      - pending_orders: deque of {"order_id": int, "remaining": {product_id: qty}}

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
        # each entry: {"order_id": int, "remaining": {product_id: qty}}
        self.pending_orders: Deque[Dict[str, Any]] = deque()

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

      Expected order shape:
      {
        "order_id": 123,
        "requested": [
          {"product_id": 0, "quantity": 2},
          {"product_id": 10, "quantity": 4}
        ]
      }

      Behavior:
        - Validate each line via self._validate_line_item(product_id, quantity)
        - Allocate available inventory immediately and create packages (via _pack_shipments)
        - Call ship_package for each package
        - If items remain unfulfilled, add a pending order entry
      """
      # Extract fields from incoming order
      order_id = order.get("order_id")
      requested_lines = order.get("requested", [])

      # Build maps of what to ship now and what remains
      to_ship_now: Dict[int, int] = {}     # product_id -> qty to ship immediately
      remaining: Dict[int, int] = {}       # product_id -> qty that couldn't be fulfilled

      # Validate and allocate from inventory for each requested line
      for line in requested_lines:
          pid = int(line["product_id"])
          qty = int(line["quantity"])

          # Validate per rules: unknown -> ValueError, negative -> ValueError, zero -> ignore
          should_process = self._validate_line_item(pid, qty)
          if not should_process:
              # zero-quantity: ignore silently
              continue

          # Determine how much to allocate from inventory
          available = self.inventory.get(pid, 0)
          allocate = min(qty, available)

          if allocate > 0:
              to_ship_now[pid] = to_ship_now.get(pid, 0) + allocate
              # Decrease inventory immediately, commit allocation now
              self.inventory[pid] = available - allocate

          # Can not satisfy the requested qty, record the remaining amount
          if qty - allocate > 0:
              remaining[pid] = remaining.get(pid, 0) + (qty - allocate)

      # If there are items to ship now, pack them into packages and ship
      if to_ship_now:
          packages = self._pack_shipments(to_ship_now)  # returns list of {pid: qty} packages
          for pkg in packages:
              # Shape package into the expected ship_package format
              shipped_items = []

              for pid, qty in pkg.items():
                  shipped_item = {
                      "product_id": int(pid),
                      "quantity": int(qty)
                  }
                  shipped_items.append(shipped_item)

              shipment = {"order_id": order_id, "shipped": shipped_items}
              self.ship_package(shipment)

      # If anything remains unfulfilled, enqueue as a pending order entry
      if remaining:
          pending_entry = {"order_id": order_id, "remaining": dict(remaining)}
          self.pending_orders.append(pending_entry)

    def process_restock(self, restock: List[Dict[str, Any]]) -> None:
        """
        Add inventory from a restock and re-attempt pending orders.

        Example restock:
        [
          {"product_id": 0, "quantity": 30},
          {"product_id": 10, "quantity": 5}
        ]

        Responsibilities (to be implemented):
          - Validate each line via self._validate_line_item(product_id, quantity)
          - Increment self.inventory for each restock item
          - Iterate pending orders (FIFO) and attempt to fulfill them,
            shipping available items and updating/removing pending entries
        """
        # Validate and add new inventory
        for line in restock:
            pid = int(line["product_id"])
            qty = int(line["quantity"])

            should_process = self._validate_line_item(pid, qty)
            if not should_process:
                continue

            self.inventory[pid] += qty

        # Re-attempt pending orders by replaying them through process_order
        current_pending = self.pending_orders
        self.pending_orders = deque()

        while current_pending:
            order = current_pending.popleft()
            self.process_order({
                "order_id": order["order_id"],
                "requested": [
                    {"product_id": pid, "quantity": qty}
                    for pid, qty in order["remaining"].items()
                ]
            })

    def ship_package(self, shipment: Dict[str, Any]) -> None:
        """
        Stub for shipping a package. In production this would integrate with the packing UI.

        Example shipment:
        {
          "order_id": 123,
          "shipped": [
            {"product_id": 0, "quantity": 1},
            {"product_id": 10, "quantity": 2}
          ]
        }

        Behavior:
          - Print the shipment
        """
        print(shipment)

    # ----- Helper methods (private) -----

    def _validate_line_item(self, product_id: int,quantity: int) -> bool:
      """
      Validate a single order/restock line item according to module rules.

      Rules:
        - Unknown product_id -> raise ValueError
        - Negative quantity -> raise ValueError
        - Zero quantity -> ignore (return False)
        - Positive quantity -> valid (return True)

      Returns:
          True if the item should be processed.
          False if the quantity is zero and should be ignored.

      Raises:
          ValueError if validation fails.
      """

      # Unknown product_id
      if product_id not in self.catalog:
          raise ValueError(f"Unknown product_id: {product_id}")

      # Negative quantity
      if quantity < 0:
          raise ValueError(f"Negative quantity not allowed: {quantity}")

      # Zero quantity → ignore
      if quantity == 0:
          return False

      # Valid positive quantity
      return True


    def _pack_shipments(self, items_to_ship: Dict[int, int]) -> List[Dict[str, int]]:
        """
        Split items_to_ship (product_id -> quantity) into a list of packages where
        each package is a list of {"product_id": int, "quantity": int} and the
        total mass of each package does not exceed MAX_PACKAGE_G.

        Greedy packing strategy
        """
        packages = []
        current_package = {}   # product_id -> quantity in this package
        current_weight = 0

        # Pack all items
        for product_id, quantity in items_to_ship.items():
            mass_g = self.catalog[product_id]["mass_g"]

            for _ in range(quantity):
                # Open a new package if this unit doesn't fit
                if current_weight + mass_g > MAX_PACKAGE_G:
                    packages.append(current_package)
                    current_package = {}
                    current_weight = 0

                if product_id not in current_package:
                    current_package[product_id] = 0
                current_package[product_id] += 1
                
                current_weight += mass_g

        # Add last package
        if current_package:
            packages.append(current_package)

        return packages