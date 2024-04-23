import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

from sqlalchemy.exc import IntegrityError

from typing import List, Tuple

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list [int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    total_dark_ml = 0
    total_price = 0

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            if barrel.potion_type == [0,1,0,0]:
                total_green_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [1,0,0,0]:
                total_red_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0,0,1,0]:
                total_blue_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0,0,0,1]:
                total_dark_ml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {total_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {total_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml + {total_dark_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {total_price}"))

    print(f"Total Green ML: {total_green_ml}, Total Red ML: {total_red_ml}, Total Blue ML: {total_blue_ml}, Total Dark ML: {total_dark_ml}, Total Price: {total_price}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: List[Barrel]):
   print(wholesale_catalog)
   with db.engine.begin() as connection:
       num_green_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory WHERE id = 2")).scalar_one()
       num_red_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory WHERE id = 1")).scalar_one()
       num_blue_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory WHERE id = 3")).scalar_one()
       num_dark_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_inventory WHERE id = 4")).scalar_one()
       gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()

       # Sort small barrels by ascending ml_per_barrel
       sorted_small_barrels = sorted([barrel for barrel in wholesale_catalog if 'small' in barrel.sku.lower()], key=lambda x: x.ml_per_barrel)

       potion_quantities: List[Tuple[Barrel, int]] = [
           (barrel, num_green_potion) for barrel in sorted_small_barrels if barrel.potion_type == [0, 1, 0, 0]
       ] + [
           (barrel, num_red_potion) for barrel in sorted_small_barrels if barrel.potion_type == [1, 0, 0, 0]
       ] + [
           (barrel, num_blue_potion) for barrel in sorted_small_barrels if barrel.potion_type == [0, 0, 1, 0]
       ] + [
           (barrel, num_dark_potion) for barrel in sorted_small_barrels if barrel.potion_type == [0, 0, 0, 1]
       ]
#must be invenotry for ml but i still going by potion but for version 3 itll be better to quary from ml and should be based just on the logic if im going to have multiple potions
       barrel_plan = []

       for barrel, potion_qty in potion_quantities:
           if potion_qty < 10 and gold >= barrel.price:
               barrel_plan.append({"sku": barrel.sku, "quantity": 1})
               gold -= barrel.price
           else:
               break

       return barrel_plan




# find small barrels first list or dictanry 


# find all small barrels first ->small barrels
# for 'color' in sorted 
# if barrel of potion_type
# exist in small post_deliver_barrels:
# if (buyable):
#     buy gold -= Priceelse break



#         return barrel_plan
    
#         query all color mL 
#     sort by ascending order

#     for each color:
#         try to buy a small barrel with your gold
#         update gold in hand accordingly
#         if you don't have enough gold, break out of loop
    
#     return plan

#     qury them all then sort it see if you can buy that barrel first small barrel





# check if there if not continue and try to buy it

# find small barrels first with list or dictanry 


# find all small barrels first ->small barrels
# for 'color' in sorted 
# if barrel of potion_type
# exist in small post_deliver_barrels:
# if (buyable):
#     buy gold -= Price break