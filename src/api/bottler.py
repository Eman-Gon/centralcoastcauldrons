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
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity =  {potion.quantity} + quantity where id = 2" ))
            elif potion.potion_type == [100, 0, 0, 0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity =  {potion.quantity} + quantity where id = 1" ))
            elif potion.potion_type == [0, 0, 100, 0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity =  {potion.quantity} + quantity where id = 3" ))
            elif potion.potion_type == [0, 0, 0, 100]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity where id = 4" ))
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

        # Query the potion_type and quantity from the potion_inventory table
        potion_inventory_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type, quantity FROM potion_inventory"))
        potion_inventory = {potion_id: {'potion_type': potion_type, 'quantity': quantity} for potion_id, potion_type, quantity in potion_inventory_result}

    potion_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
    potion_counts = {potion_id: 0 for potion_id in potion_inventory.keys()}

    while True:
        made_potion = False
        for potion_id, potion_data in potion_inventory.items():
            # Yellow (id: 5)
            if potion_id == 5 and potion_types[1] >= 50 and potion_types[0] >= 50 and potion_data['quantity'] < 5:
                potion_counts[5] += 1
                potion_types[2] -= 50
                potion_types[1] -= 50
                made_potion = True

            # Green (id: 2)
            elif potion_id == 2 and potion_types[0] >= 100 and potion_data['quantity'] < 5:
                potion_counts[2] += 1
                potion_types[0] -= 100
                made_potion = True

            # Red (id: 1)
            elif potion_id == 1 and potion_types[1] >= 100 and potion_data['quantity'] < 5:
                potion_counts[1] += 1
                potion_types[1] -= 100
                made_potion = True

            # Blue (id: 3)
            elif potion_id == 3 and potion_types[2] >= 100 and potion_data['quantity'] < 5:
                potion_counts[3] += 1
                potion_types[2] -= 100
                made_potion = True

            # Dark (id: 4)
            elif potion_id == 4 and potion_types[3] >= 100 and gold >= 700 and potion_data['quantity'] < 5:
                potion_counts[4] += 1
                potion_types[3] -= 100
                made_potion = True

        if not made_potion:
            break

    return potion_counts