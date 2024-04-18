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
    total_ml = 0
    total_price = 0
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            total_ml += barrel.ml_per_barrel * barrel.quantity  
            total_price += barrel.price * barrel.quantity 
            
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {total_ml}")) #, {'total_ml': total_ml})
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {total_price}")) #, {'total_price'}) #: total_price})
    print(f"Total ML per Barrel: {total_ml}, Total Price: {total_price}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        gold, num_green_potion = connection.execute(sqlalchemy.text("SELECT gold, num_green_potions FROM global_inventory")).first()
     
    barrel_plan = []
    for barrel in wholesale_catalog:
        if (num_green_potion < 10 and gold >= barrel.price and barrel.sku == 'SMALL_GREEN_BARREL'):
            barrel_plan.append(
                {
                    "sku": barrel.sku,
                    "quantity": 1,
                }
            )
    
    return barrel_plan



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
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    total_price = 0
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            if barrel.sku == 'SMALL_GREEN_BARREL':
                total_green_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.sku == 'SMALL_RED_BARELL':
                total_red_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.sku == 'SMALL_BLUE_BARREL':
                total_blue_ml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {total_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {total_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {total_price}"))
    print(f"Total Green ML: {total_green_ml}, Total Red ML: {total_red_ml}, Total Blue ML: {total_blue_ml}, Total Price: {total_price}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        num_green_potion = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        num_red_potion = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        num_blue_potion = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()

        barrel_plan = []
        for barrel in wholesale_catalog:
            if (num_green_potion < 10 and gold >= barrel.price and barrel.sku == 'SMALL_GREEN_BARREL'):
                barrel_plan.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                )
            elif (num_red_potion < 10 and gold >= barrel.price and barrel.sku == 'SMALL_RED_BARREL'):
                barrel_plan.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                )
            elif (num_blue_potion < 10 and gold >= barrel.price and barrel.sku == 'SMALL_BLUE_BARREL'):
                barrel_plan.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                )
        return barrel_plan