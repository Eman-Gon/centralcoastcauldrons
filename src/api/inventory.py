import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    with db.engine.begin() as connection:
        # Retrieve potion quantities from the potion_inventory table
        total_number_of_potions = sum(connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory_view")).scalars())

        # Calculate the current inventory levels from the ledger tables
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar_one() or 0
        num_green_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'green'")).scalar_one() or 0
        num_red_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'red'")).scalar_one() or 0
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'blue'")).scalar_one() or 0
        num_dark_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'dark'")).scalar_one() or 0
        total_ml_in_barrels = num_green_ml + num_red_ml + num_blue_ml + num_dark_ml

        return {
            "number_of_potions": total_number_of_potions,
            "ml_in_barrels": total_ml_in_barrels,
            "gold": gold
        }


# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. 
    Each additional capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        # Calculate the current gold from the ledger tables
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar_one() or 0

        # # Calculate the total capacity units that can be purchased
        # total_capacity_units = gold // 1000

        # # Calculate the potion capacity and ml capacity
        # potion_capacity = min(total_capacity_units, 1) * 50
        # ml_capacity = min(total_capacity_units, 1) * 10000

        capacity = 0

        if(gold > 2000):
            capacity = 1

        return {
            "potion_capacity":capacity,
            "ml_capacity": capacity
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion.
    Each additional capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        # Calculate the current gold from the ledger tables
        gold = connection.execute(sqlalchemy.text("SELECT gold from inventory_summary_view")).scalar_one() or 0

        # Calculate the total cost of the capacity purchase
        total_cost = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity 

        if total_cost > gold:
            return "Insufficient gold to purchase the capacity plan."

        # Add a new transaction
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), {"description": f"Delivery of capacity plan (order {order_id})"})
        transaction_id = result.scalar_one()

        # Record changes in the ledger tables
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change_in_gold) VALUES (:transaction_id, :change_in_gold)"), {"transaction_id": transaction_id, "change_in_gold": -1000 * total_cost})
        
        #Uodate global_values
        connection.execute(sqlalchemy.text(
                """UPDATE global_Values 
                    SET ml_capacity_units = ml_capacity_units + :ml_units,
                    ml_capacity = ml_capacity + 10000 * :ml_units,
                    potion_capacity_units = potion_capacity_units + :p_units,
                    potion_capacity = potion_capacity + 50 * :p_units
                """
            ),
            {
                "ml_units": capacity_purchase.ml_capacity,
                "p_units": capacity_purchase.potion_capacity
            }

        )

    return "OK"