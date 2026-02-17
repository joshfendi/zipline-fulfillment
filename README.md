# Zipline Fulfillment System

## Overview

This project implements a lightweight inventory management and order fulfillment backend for a Zipline distribution center ("nest").

The system:
- Manages a catalog of medical products
- Tracks inventory
- Processes hospital orders
- Splits shipments under a 1.8kg limit
- Defers partial orders until restock

## Design Goals

- Simplicity and clarity
- Deterministic packing logic
- Clean separation of state
- Extensibility for production use

## Architecture (High Level)

- catalog
- inventory
- pending_orders
- process_order
- process_restock
- ship_package

## Assumptions

- In-memory only
- Single-threaded
- No persistence layer
- Greedy packing strategy
