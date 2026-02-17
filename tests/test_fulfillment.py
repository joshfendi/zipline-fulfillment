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
