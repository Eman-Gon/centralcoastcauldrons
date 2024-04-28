import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity where id = 2"))
            elif potion.potion_type == [100, 0, 0, 0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity where id = 1"))
            elif potion.potion_type == [0, 0, 100, 0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity where id = 3"))
            elif potion.potion_type == [0, 0, 0, 100]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity where id = 4"))
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
        num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
        num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
        num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()

    potion_types = [num_green_ml, num_red_ml, num_blue_ml, num_dark_ml]
    plan = []

    while True:
        made_potion = False
        # Yellow
        if potion_types[2] >= 50 and potion_types[1] >= 50:
            plan.append({
                "quantity": 1,
                "potion_type": [50, 50, 0, 0]
            })
            potion_types[2] -= 50
            potion_types[1] -= 50
            made_potion = True

        # Green
        elif potion_types[0] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": [100, 0, 0, 0]
            })
            potion_types[0] -= 100
            made_potion = True

        # Red
        elif potion_types[1] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": [0, 100, 0, 0]
            })
            potion_types[1] -= 100
            made_potion = True

        # Blue
        elif potion_types[2] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": [0, 0, 100, 0]
            })
            potion_types[2] -= 100
            made_potion = True

        # Dark
        elif potion_types[3] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": [0, 0, 0, 100]
            })
            potion_types[3] -= 100
            made_potion = True

        if not made_potion:
            break

    return plan

if __name__ == "__main__":
    plan = get_bottle_plan()
    print("Plan:", plan)