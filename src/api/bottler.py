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
    potion_id: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        # Query the potion_type from the potion_inventory table
        potion_types_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type FROM potion_inventory"))
        potion_types_map = {potion_id: potion_type for potion_id, potion_type in potion_types_result}

        for potion in potions_delivered:
            if potion.potion_id in potion_types_map:
                potion_type = potion_types_map[potion.potion_id]
                if potion_type == [1, 0, 0, 0]:  # Red
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {100 * potion.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = {potion.potion_id}"))
                elif potion_type == [0, 1, 0, 0]:  # Green
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {100 * potion.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = {potion.potion_id}"))
                elif potion_type == [0, 0, 1, 0]:  # Blue
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - {100 * potion.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = {potion.potion_id}"))
                elif potion_type == [0, 0, 0, 1]:  # Dark
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml - {100 * potion.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = {potion.potion_id}"))
                elif potion_type == [0, 1, 1, 0]:  # Yellow
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {50 * potion.quantity}, num_blue_ml = num_blue_ml - {50 * potion.quantity}"))
                    connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = {potion.potion_id}"))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
        num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
        num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
        num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar_one()

        # Query the potion_type from the potion_inventory table
        potion_types_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type FROM potion_inventory"))
        potion_types_map = {potion_id: potion_type for potion_id, potion_type in potion_types_result}

    potion_types = [num_green_ml, num_red_ml, num_blue_ml, num_dark_ml]
    plan = []

    while True:
        made_potion = False
        # Yellow (id: 5)
        if 5 in potion_types_map and potion_types[2] >= 50 and potion_types[1] >= 50:
            plan.append({
                "quantity": 1,
                "potion_type": potion_types_map[5]
            })
            potion_types[2] -= 50
            potion_types[1] -= 50
            made_potion = True

        # Green (id: 2)
        elif 2 in potion_types_map and potion_types[0] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": potion_types_map[2]
            })
            potion_types[0] -= 100
            made_potion = True

        # Red (id: 1)
        elif 1 in potion_types_map and potion_types[1] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": potion_types_map[1]
            })
            potion_types[1] -= 100
            made_potion = True

        # Blue (id: 3)
        elif 3 in potion_types_map and potion_types[2] >= 100:
            plan.append({
                "quantity": 1,
                "potion_type": potion_types_map[3]
            })
            potion_types[2] -= 100
            made_potion = True

        # Dark (id: 4)
        elif 4 in potion_types_map and potion_types[3] >= 100 and gold >= 700:
            plan.append({
                "quantity": 1,
                "potion_type": potion_types_map[4]
            })
            potion_types[3] -= 100
            made_potion = True

        if not made_potion:
            break

    return plan


if __name__ == "__main__":
    print(get_bottle_plan())