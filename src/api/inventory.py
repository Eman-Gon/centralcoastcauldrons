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
        potion_query = sqlalchemy.text("SELECT sku, quantity FROM potion_inventory")
        potion_result = connection.execute(potion_query)
        potion_counts = {}
        potion_rows = potion_result.fetchall()
        for sku, quantity in potion_rows:
            potion_counts[sku] = quantity

        #result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM global_inventory")).one()
        num_green_ml, num_red_ml, num_blue_ml, num_dark_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM global_inventory")).one()
        total_number_of_potions = sum(potion_counts.values())
        total_ml_in_barrels = num_green_ml + num_red_ml + num_blue_ml + num_dark_ml
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
    
    return {
            "number_of_potions": total_number_of_potions,
            "ml_in_barrels": total_ml_in_barrels,
            "gold": gold
        }
    # return {
    #     "number_of_potions": 0,#sum up potion
    #     "ml_in_barrels": 0,#sum up ml           SUM FUNCTION((query ml).scalars())
    #     "gold": 0#gold 
    # }
# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
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
