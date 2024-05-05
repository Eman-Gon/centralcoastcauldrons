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
    """Go from barrel to bottle."""
    with db.engine.begin() as connection:
        num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
        num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
        num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
        num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar_one()

        # Query the potion_type from the potion_inventory table
        potion_types_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type FROM potion_inventory"))
        potion_types_map = {potion_id: potion_type for potion_id, potion_type in potion_types_result}

        potion_counts = {potion_id: 0 for potion_id in potion_types_map}

        total_gold_used = 0

        while True:
            made_potion = False

            # Check if all potion types (excluding Dark) have a quantity greater than 5
            all_potions_over_5 = all(count > 5 for potion_id, count in potion_counts.items() if potion_id != 4)

            # Check if we can make a Dark potion
            if 4 in potion_counts and num_dark_ml >= 100 and gold >= 700 and all_potions_over_5:
                potion_counts[4] += 1
                num_dark_ml -= 100
                total_gold_used += 700
                made_potion = True

            # If a Dark potion was not made, create other potions based on minimum count
            if not made_potion:
                min_count = min((count for potion_id, count in potion_counts.items() if potion_id != 4), default=0)
                potion_to_make = next((potion_id for potion_id, count in potion_counts.items() if count == min_count and potion_id != 4), None)

                if potion_to_make is not None:
                    if potion_to_make == 5 and num_blue_ml >= 50 and num_green_ml >= 50:
                        potion_counts[5] += 1
                        num_blue_ml -= 50
                        num_green_ml -= 50
                        made_potion = True
                    elif potion_to_make == 2 and num_green_ml >= 100:
                        potion_counts[2] += 1
                        num_green_ml -= 100
                        made_potion = True
                    elif potion_to_make == 1 and num_red_ml >= 100:
                        potion_counts[1] += 1
                        num_red_ml -= 100
                        made_potion = True
                    elif potion_to_make == 3 and num_blue_ml >= 100:
                        potion_counts[3] += 1
                        num_blue_ml -= 100
                        made_potion = True

            if not made_potion:
                break

        # Update the gold in the database after the loop
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {total_gold_used}"))

        return potion_counts

if __name__ == "__main__":
    print(get_bottle_plan())