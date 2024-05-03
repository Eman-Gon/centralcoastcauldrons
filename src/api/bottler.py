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
        # Query the current inventory levels from the global_inventory table
        inventory_result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory")).fetchone()
        num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold = inventory_result

        # Query the potion types and quantities from the potion_inventory table
        potion_inventory_result = connection.execute(sqlalchemy.text("SELECT id, potion_type, quantity FROM potion_inventory"))
        potion_inventory = {row[0]: {'potion_type': row[1], 'quantity': row[2]} for row in potion_inventory_result}

    potion_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
    potion_counts = {potion_id: 0 for potion_id in potion_inventory.keys()}

    while True:
        made_potion = False
        for potion_id, potion_data in potion_inventory.items():
            potion_type = potion_data['potion_type']
            if potion_type == [100, 0, 0, 0] and potion_types[0] >= 100:  # Red
                potion_counts[potion_id] += 1
                potion_types[0] -= 100
                made_potion = True
            elif potion_type == [0, 100, 0, 0] and potion_types[1] >= 100:  # Green
                potion_counts[potion_id] += 1
                potion_types[1] -= 100
                made_potion = True
            elif potion_type == [0, 0, 100, 0] and potion_types[2] >= 100:  # Blue
                potion_counts[potion_id] += 1
                potion_types[2] -= 100
                made_potion = True
            elif potion_type == [0, 0, 0, 100] and potion_types[3] >= 100 and gold >= 100:  # Dark
                potion_counts[potion_id] += 1
                potion_types[3] -= 100
                gold -= 100
                made_potion = True
            elif potion_type == [50, 50, 0, 0] and potion_types[0] >= 50 and potion_types[1] >= 50:  # Yellow
                potion_counts[potion_id] += 1
                potion_types[0] -= 50
                potion_types[1] -= 50
                made_potion = True

        if not made_potion:
            break

    # Update the potion_inventory table with the new quantities
    with db.engine.begin() as connection:
        for potion_id, quantity in potion_counts.items():
            if quantity > 0:
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {quantity} WHERE id = {potion_id}"))

    # Convert potion_counts to a list of dictionaries
    potion_plan = [{"potion_id": potion_id, "quantity": quantity} for potion_id, quantity in potion_counts.items() if quantity > 0]

    return potion_plan

if __name__ == "__main__":
    print(get_bottle_plan())