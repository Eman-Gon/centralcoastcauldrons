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
        total_number_of_potions = sum(connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory")).scalars())

        #result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM global_inventory")).one()
        num_green_ml, num_red_ml, num_blue_ml, num_dark_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM global_inventory")).one()
        total_ml_in_barrels = num_green_ml + num_red_ml + num_blue_ml + num_dark_ml
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
    
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
        # Get the current gold from the global_inventory table
        gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar_one()

    # Calculate the total capacity units that can be purchased
    total_capacity_units = gold // 1000

    # Calculate the potion capacity and ml capacity
    potion_capacity = min(total_capacity_units, 1) * 50
    ml_capacity = min(total_capacity_units, 1) * 10000

    return {
        "potion_capacity": potion_capacity,
        "ml_capacity": ml_capacity
    }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
