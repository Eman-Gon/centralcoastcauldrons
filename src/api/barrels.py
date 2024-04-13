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
            
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :total_ml"), {'total_ml': total_ml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :total_price"), {'total_price': total_price})
    print(f"Total ML per Barrel: {total_ml}, Total Price: {total_price}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        num_green_potion = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
    if (num_green_potion < 10):
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
