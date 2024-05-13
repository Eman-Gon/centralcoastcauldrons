import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    total_used = {
        "green": 0,
        "red": 0,
        "blue": 0,
        "dark": 0
    }
    total_price = 0

    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 1, 0, 0]:
            total_used["green"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [1, 0, 0, 0]:
            total_used["red"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]:
            total_used["blue"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 0, 1]:
            total_used["dark"] += barrel.ml_per_barrel * barrel.quantity
        total_price += barrel.price * barrel.quantity

    with db.engine.begin() as connection:
        # Add a new transaction
        transaction_id = connection.execute(
            sqlalchemy.text(
                "INSERT INTO transactions (description) VALUES (:description) RETURNING id"
            ), 
            {"description": f"Delivery of barrels (order {order_id})"}
        ).scalar_one()

        for color in total_used:
            if total_used[color] > 0:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, :color, :change_in_ml)"),
                                    {
                                        "transaction_id": transaction_id,
                                        "color": color,
                                        "change_in_ml": total_used[color]
                                    }
                                   )

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'green', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_green_ml})

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'red', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_red_ml})

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'blue', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_blue_ml})

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'dark', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_dark_ml})
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change_in_gold) VALUES (:transaction_id, :total_price)"),
                                    {
                                        "transaction_id": transaction_id,
                                        "total_price": total_price * -1
                                    }
                                   )
        
#if qunaity greater 0 then dont put table
    print(f"Total Green ML: {total_used['green']}, Total Red ML: {total_used['red']}, Total Blue ML: {total_used['blue']}, Total Dark ML: {total_used['dark']}, Total Price: {total_price}")
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        # Calculate the current inventory levels from the ledger tables
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar_one() or 0
        total_ml_inventory = connection.execute(sqlalchemy.text("SELECT total_ml FROM inventory_summary_view")).scalar_one() or 0

        # Get the ML capacity and capacity units from the global_values table
        ml_capacity, ml_capacity_units = connection.execute(sqlalchemy.text("SELECT ml_capacity, ml_capacity_units FROM global_values LIMIT 1")).fetchone() or (0, 0)

        # Calculate the available ML capacity
        available_ml_capacity = ml_capacity - total_ml_inventory

        barrel_plan = []

        for size in ['LARGE', 'MEDIUM', 'SMALL']:
            # Sort barrels by ascending ml_per_barrel for the current size
            sorted_barrels = sorted((barrel for barrel in wholesale_catalog if size in barrel.sku), key=lambda barrel: barrel.ml_per_barrel)

            for barrel in sorted_barrels:
                if available_ml_capacity >= barrel.ml_per_barrel and gold >= barrel.price:
                    barrel_plan.append({"sku": barrel.sku, "quantity": 1})
                    gold -= barrel.price
                    available_ml_capacity -= barrel.ml_per_barrel

    return barrel_plan

# @router.post("/plan")
# def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
#     with db.engine.begin() as connection:
#         # Calculate the current inventory levels from the ledger tables
#         gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar_one() or 0
#         total_ml_inventory = connection.execute(sqlalchemy.text("SELECT total_ml FROM inventory_summary_view")).scalar_one() or 0

#         # Get the ML capacity and capacity units from the global_values table
#         ml_capacity, ml_capacity_units = connection.execute(sqlalchemy.text("SELECT ml_capacity, ml_capacity_units FROM global_values LIMIT 1")).fetchone() or (0, 0)

#         # Calculate the available ML capacity
#         available_ml_capacity = ml_capacity - total_ml_inventory

#         print(f"Initial available ML capacity: {available_ml_capacity}")
#         print(f"Initial gold: {gold}")

#         barrel_plan = []

#         # Check if LARGE barrels are available
#         large_barrels = [barrel for barrel in wholesale_catalog if 'LARGE' in barrel.sku]
#         if large_barrels:
#             print("LARGE barrels available")
#             # Sort LARGE barrels by ascending ml_per_barrel
#             sorted_large_barrels = sorted(large_barrels, key=lambda barrel: barrel.ml_per_barrel)
#             for barrel in sorted_large_barrels:
#                 if available_ml_capacity >= barrel.ml_per_barrel and gold >= barrel.price:
#                     barrel_plan.append({"sku": barrel.sku, "quantity": 1})
#                     gold -= barrel.price
#                     available_ml_capacity -= barrel.ml_per_barrel
#                     print(f"Bought LARGE barrel: {barrel.sku}")
#                     print(f"Updated available ML capacity: {available_ml_capacity}")
#                     print(f"Updated gold: {gold}")
#         else:
#             print("No LARGE barrels available")
#             # Check if MEDIUM barrels are available
#             medium_barrels = [barrel for barrel in wholesale_catalog if 'MEDIUM' in barrel.sku]
#             if medium_barrels:
#                 print("MEDIUM barrels available")
#                 # Sort MEDIUM barrels by ascending ml_per_barrel
#                 sorted_medium_barrels = sorted(medium_barrels, key=lambda barrel: barrel.ml_per_barrel)
#                 for barrel in sorted_medium_barrels:
#                     if available_ml_capacity >= barrel.ml_per_barrel and gold >= barrel.price:
#                         barrel_plan.append({"sku": barrel.sku, "quantity": 1})
#                         gold -= barrel.price
#                         available_ml_capacity -= barrel.ml_per_barrel
#                         print(f"Bought MEDIUM barrel: {barrel.sku}")
#                         print(f"Updated available ML capacity: {available_ml_capacity}")
#                         print(f"Updated gold: {gold}")
#             else:
#                 print("No MEDIUM barrels available")
#                 # Check if SMALL barrels are available
#                 small_barrels = [barrel for barrel in wholesale_catalog if 'SMALL' in barrel.sku]
#                 if small_barrels:
#                     print("SMALL barrels available")
#                     # Sort SMALL barrels by ascending ml_per_barrel
#                     sorted_small_barrels = sorted(small_barrels, key=lambda barrel: barrel.ml_per_barrel)
#                     for barrel in sorted_small_barrels:
#                         if available_ml_capacity >= barrel.ml_per_barrel and gold >= barrel.price:
#                             barrel_plan.append({"sku": barrel.sku, "quantity": 1})
#                             gold -= barrel.price
#                             available_ml_capacity -= barrel.ml_per_barrel
#                             print(f"Bought SMALL barrel: {barrel.sku}")
#                             print(f"Updated available ML capacity: {available_ml_capacity}")
#                             print(f"Updated gold: {gold}")
#                 else:
#                     print("No SMALL barrels available")

#     print(f"Final barrel plan: {barrel_plan}")
#     return barrel_plan


