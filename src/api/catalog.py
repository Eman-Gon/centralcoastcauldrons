# import sqlalchemy
# from src import database as db
# from fastapi import APIRouter

# router = APIRouter()

# @router.get("/catalog/", tags=["catalog"])
# def get_catalog():
#     """
#     Each unique item combination must have only a single price.
#     """
#     with db.engine.begin() as connection:
#         num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
#         num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
#         num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()

#         catalog = []
#         if num_green_potions > 0:
#             catalog.append(
#                 {
#                     "sku": "GREEN_POTION",
#                     "name": "Green Potion",
#                     "quantity": 1,
#                     "price": 50,
#                     "potion_type": [0, 100, 0, 0],
#                 }
#             )
#         if num_red_potions > 0:
#             catalog.append(
#                 {
#                     "sku": "RED_POTION",
#                     "name": "Red Potion",
#                     "quantity": 1,
#                     "price": 50,
#                     "potion_type": [0, 0, 100, 0],
#                 }
#             )
#         if num_blue_potions > 0:
#             catalog.append(
#                 {
#                     "sku": "BLUE_POTION",
#                     "name": "Blue Potion",
#                     "quantity": 1,
#                     "price": 50,
#                     "potion_type": [0, 0, 0, 100],
#                 }
#             )
#         return catalog


# import sqlalchemy
# from src import database as db
# from fastapi import APIRouter

# router = APIRouter()

# @router.get("/catalog/", tags=["catalog"])
# def get_catalog():
#     """
#     Each unique item combination must have only a single price.
#     """
#     with db.engine.begin() as connection:
#         # Retrieve potion information from the potion_inventory table
#         potions = connection.execute(sqlalchemy.text("SELECT sku, price, num_green_potions, num_red_potions, num_blue_potions, num_dark_potions FROM potion_inventory")).fetchall()

#         catalog = []
#         for potion in potions:
#             sku, price, num_green, num_red, num_blue, num_dark = potion
#             if num_green + num_red + num_blue + num_dark > 0:
#                 catalog.append({
#                     "sku": sku,
#                     "name": sku,
#                     "quantity": 1,
#                     "price": price,
#                     "potion_type": [num_red, num_green, num_blue, num_dark],
#                 })

#         return catalog

import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combination must have only a single price."""
    catalog = []
    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text("SELECT inventory, sku, type, price FROM potion_inventory"))
        for row in results:
            catalog.append({
                "sku": row.sku,
                "quantity": row.inventory,
                "price": row.price,
                "potion_type": row.type
            })
    return catalog