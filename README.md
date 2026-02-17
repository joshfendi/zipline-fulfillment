# Zipline Fulfillment System

## Overview

A lightweight inventory and order fulfillment backend for a Zipline distribution center ("nest"). The system manages a product catalog, tracks inventory, processes hospital orders, splits shipments to stay under **1.8kg (1800g)**, and supports partial fulfillment with deferred completion after restock.

## Design

### Core State
- `catalog`: `product_id → { mass_g, product_name }`
- `inventory`: `product_id → quantity`
- `pending_orders`: FIFO queue of `{ order_id, remaining: { product_id: quantity } }`

### Order Flow
Validate → allocate inventory → pack shipments → ship → defer remainder to pending

### Restock Flow
Validate → increase inventory → re-process pending orders (FIFO) → ship what's now fulfillable

### Packing Strategy
Greedy unit-aware algorithm: fill the current package unit-by-unit, open a new one when the next unit would exceed 1800g. Simple and deterministic over optimal.

## Validation Rules
- Unknown `product_id` → `ValueError`
- Negative quantity → `ValueError`
- Zero quantity → ignored
- Duplicate `product_id` in catalog → `ValueError`
- Product mass > 1800g → `ValueError`

## Running the Project
```bash
# Setup
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Tests
python -m pytest -q       # quiet
python -m pytest -s       # with shipment output

# Demo
python driver.py
```

## Problem Decomposition

I split the problem into three concerns: what inventory exists, what can be shipped now, and what needs to be deferred. That framing made the core loop straightforward: validate, allocate, pack, ship, queue the remainder.

For restocking, rather than duplicating allocation logic, I replayed pending orders through `process_order` directly, which kept the fulfillment logic in one place.

## Main Focus

The primary focus of this implementation was correct and predictable state management.

This system is inherently stateful: inventory changes over time, orders may be partially fulfilled, and pending orders must be replayed when new inventory arrives. I prioritized making these state transitions explicit, deterministic, and easy to reason about.

In particular, I focused on:
- Ensuring inventory is mutated at the correct time to avoid double allocation
- Preserving FIFO behavior when replaying pending orders
- Maintaining invariants (no negative inventory, no overweight shipments)
- Making shipment splitting predictable and testable

Rather than optimizing for performance or implementing advanced packing heuristics, I chose clarity and correctness under the given constraints.

## Extensibility

Each method has a single responsibility, the state shape is plain dicts with documented structure, and the two most likely extension points (`ship_package` and `_pack_shipments`) are isolated so either can be swapped out without touching the rest of the system.

## Stakeholder Thinking

I considered two groups: fulfillment operators packing shipments, and hospitals placing orders. Operators need predictable, deterministic output so I kept the packing strategy simple and consistent. Hospitals need confidence their orders will eventually be filled, and the FIFO pending queue ensures nothing is silently dropped when inventory is short.

## Production Priorities

The main gaps from production-ready are persistence (state doesn't survive restarts), idempotency (duplicate order IDs could cause double-shipping), and concurrency (inventory updates aren't transactional). Structured logging on state transitions and stricter input validation would also be early priorities.

## How I Would Extend This

If productionized, I would:
- Add transactional inventory updates
- Introduce an event-driven shipment pipeline
- Implement structured logging and metrics
- Replace in-memory storage with a database
- Add concurrency controls to prevent race conditions
- Optimize the packing algorithm (the current greedy strategy is simple and deterministic, but a first-fit decreasing or dynamic programming approach would reduce the number of packages for large mixed-product orders)

## AI Usage

I used AI selectively as a productivity tool, primarily to accelerate scaffolding and test drafting. The system design, state modeling, and core logic were developed manually.

Before writing any code, I worked through the full system design: the state model, the lifecycle of an order across multiple calls, how partial fulfillment should behave, when inventory should be mutated to avoid double allocation, how pending orders should be replayed during restock, and whether to attempt optimal bin packing.

AI was then used to generate initial scaffolding (method stubs, docstrings, type hints) and draft early unit tests. The time saved on boilerplate was reinvested into reasoning through inventory mutation timing, validating that pending order replay wouldn't cause duplicate shipments, and writing targeted tests around edge cases like weight splitting and partial fulfillment.