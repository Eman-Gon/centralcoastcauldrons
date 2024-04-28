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
    """Go from barrel to bottle."""
    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
        num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
        num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
        num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()

        plan = []

        # Handle pure potion types
        if num_red_ml and num_green_ml >= 50:
            plan.append({
                "potion_type": [50, 50, 0, 0],
                "quantity": min(num_red_ml, num_green_ml) 
            })
        if num_green_ml >= 100:
            plan.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": num_green_ml // 100
            })
        if num_red_ml >= 100:
            plan.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": num_red_ml // 100
            })
        if num_blue_ml >= 100:
            plan.append({
                "potion_type": [0, 0, 100, 0],
                "quantity": num_blue_ml // 100
            })
        if num_dark_ml >= 100:
            plan.append({
                "potion_type": [0, 0, 0, 100],
                "quantity": num_dark_ml // 100
            })

        # This part iterates over the potion type in potions list from the potion_inventory table. calculates the quantities
        for potion in potions:
            potion_type = [potion[3] * 50, potion[2] * 50, potion[1] * 50, potion[0] * 50]
            print(potions)

           # checks if quantities in the global_inventory are greater than or equal to the
           # quantities for (potion_type). If not met there are not enough quantities in the global inventory to create the current potion type
            if num_red_ml >= potion_type[0] and num_green_ml >= potion_type[1] and num_blue_ml >= potion_type[2] and num_dark_ml >= potion_type[3]:
            #  so creates a list of current qunntities in the global inventory.  
              #  calculates the maximum quantity 
                available_quantities = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
                max_quantities = []
                for i in range(4):
                    if potion_type[i] > 0 and available_quantities[i] >= potion_type[i]:
                        max_quantities.append(available_quantities[i] // potion_type[i])
                    else:
                        max_quantities.append(0)
                       # if quantity is less  appends 0 to the max_quantities list.
                max_quantity = min(max_quantities)
                # Find the max quantity that can be produced without going over the available quantity
                if max_quantity > 0:
                    plan.append({
                        "potion_type": potion_type,
                        "quantity": max_quantity
                    })
                    num_red_ml -= max_quantity * potion_type[0]
                    num_green_ml -= max_quantity * potion_type[1]
                    num_blue_ml -= max_quantity * potion_type[2]
                    num_dark_ml -= max_quantity * potion_type[3]
                   # appends a dictionary to the plan list with the potion_type and the calculated max_quantity

        return plan
    
if __name__ == "__main__":
    print(get_bottle_plan())