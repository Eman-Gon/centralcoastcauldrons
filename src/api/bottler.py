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


# @router.post("/plan")
# def get_bottle_plan():

    
#     """Go from barrel to bottle."""
#     with db.engine.begin() as connection:
#         # Retrieve the current number of red ml from the global_inventory table
#         num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
#         # Retrieve the current number of green ml from the global_inventory table
#         num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
#         # Retrieve the current number of blue ml from the global_inventory table
#         num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
#         # Retrieve the current number of dark ml from the global_inventory table
#         num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()
#         # Retrieve the current amount of gold from the global_inventory table
#         gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar_one()
#         # Query the potion_type and quantity from the potion_inventory table
#         potion_inventory_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type, quantity FROM potion_inventory"))
#         # Create separate lists for potion_ids, potion_types, and quantities
#         potion_ids = []#This list stores the unique identifiers (id) for each potion in the potion_inventory table.
#         potion_types = []#This list stores the types of potions (e.g., 'Red', 'Green', 'Blue', etc.) corresponding to each potion_id.
#         quantities = []#This list stores the quantities or counts of each potion type corresponding to each potion_id.
#         for potion_id, potion_type, quantity in potion_inventory_result:
#             potion_ids.append(potion_id)
#             potion_types.append(potion_type)
#             quantities.append(quantity)
#         # Create a list of the current number of ml for each potion type
#         ml_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
#         # Initialize a list to keep track of the count of each potion type
#         potion_counts = [0] * 6  # Assuming potion IDs range from 1 to 5

#         while True:
#             made_potion = False
#             for i in range(len(potion_ids)):
#                 potion_id = potion_ids[i]
#                 potion_type = potion_types[i]
#                 quantity = quantities[i]
#                 # Check if it's a Yellow potion (id: 5)
#                 if potion_id == 5 and ml_types[1] >= 50 and ml_types[0] >= 50 and quantity < 5:
#                     potion_counts[5] += 1
#                     ml_types[2] -= 50
#                     ml_types[1] -= 50
#                     made_potion = True
#                 # Check if it's a Green potion (id: 2)
#                 elif potion_id == 2 and ml_types[0] >= 100 and quantity < 5:
#                     potion_counts[2] += 1
#                     ml_types[0] -= 100
#                     made_potion = True
#                 # Check if it's a Red potion (id: 1)
#                 elif potion_id == 1 and ml_types[1] >= 100 and quantity < 5:
#                     potion_counts[1] += 1
#                     ml_types[1] -= 100
#                     made_potion = True
#                 # Check if it's a Blue potion (id: 3)
#                 elif potion_id == 3 and ml_types[2] >= 100 and quantity < 5:
#                     potion_counts[3] += 1
#                     ml_types[2] -= 100
#                     made_potion = True
#                 # Check if it's a Dark potion (id: 4)
#                 elif potion_id == 4 and ml_types[3] >= 100 and gold >= 700 and quantity < 5:
#                     potion_counts[4] += 1
#                     ml_types[3] -= 100
#                     made_potion = True
#                 # If no potion was made in the current iteration, break out of the loop
#                 if not made_potion:
#                     break

#                 return potion_counts

# if __name__ == "__main__":

#     print(get_bottle_plan())



# @router.post("/plan")
# def get_bottle_plan():
#     """
#     Go from barrel to bottle.
#     """
#     with db.engine.begin() as connection:
#         num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
#         num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
#         num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
#         num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()
#         gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar_one()

#         # Query the potion_type from the potion_inventory table
#         potion_types_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type FROM potion_inventory"))
#         potion_types_map = {potion_id: potion_type for potion_id, potion_type in potion_types_result}

#     potion_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
#     potion_counts = {potion_id: 0 for potion_id in potion_types_map.keys()}

#     while True:
#         made_potion = False
#         # Yellow (id: 5)
#         if 5 in potion_types_map and potion_types[2] >= 50 and potion_types[1] >= 50:
#             potion_counts[5] += 1
#             potion_types[2] -= 50
#             potion_types[1] -= 50
#             made_potion = True

#         # Green (id: 2)
#         elif 2 in potion_types_map and potion_types[0] >= 100:
#             potion_counts[2] += 1
#             potion_types[0] -= 100
#             made_potion = True

#         # Red (id: 1)
#         elif 1 in potion_types_map and potion_types[1] >= 100:
#             potion_counts[1] += 1
#             potion_types[1] -= 100
#             made_potion = True

#         # Blue (id: 3)
#         elif 3 in potion_types_map and potion_types[2] >= 100:
#             potion_counts[3] += 1
#             potion_types[2] -= 100
#             made_potion = True

#         # Dark (id: 4)
#         elif 4 in potion_types_map and potion_types[3] >= 100 and gold >= 700:
#             potion_counts[4] += 1
#             potion_types[3] -= 100
#             made_potion = True

#         if not made_potion:
#             break

#     return potion_counts


# if __name__ == "__main__":
#     print(get_bottle_plan())

# @router.post("/plan")
# def get_bottle_plan():
#     """Go from barrel to bottle."""
#     with db.engine.begin() as connection:
#         num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
#         num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
#         num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
#         num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()
#         gold = connection.execute(sqlalchemy.text(f"SELECT gold FROM global_inventory")).scalar_one()
#         # Query the potion_type from the potion_inventory table
#         potion_types_result = connection.execute(sqlalchemy.text(f"SELECT id, potion_type FROM potion_inventory"))
#         potion_types_map = {potion_id: potion_type for potion_id, potion_type in potion_types_result}
#         potion_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
#         potion_counts = {potion_id: 0 for potion_id in potion_types_map.keys()}
#         while True:
#             made_potion = False
#             # Yellow (id: 5)
#             if 5 in potion_types_map and potion_types[2] >= 50 and potion_types[1] >= 50:
#                 for _ in range(5):  # Create 5 yellow potions with quantity 1
#                     if potion_types[2] >= 50 and potion_types[1] >= 50:
#                         potion_counts[5] += 1
#                         potion_types[2] -= 50
#                         potion_types[1] -= 50
#                     else:
#                         break
#                 made_potion = True
#             # Green (id: 2)
#             elif 2 in potion_types_map and potion_types[0] >= 100:
#                 for _ in range(5):  # Create 5 green potions with quantity 1
#                     if potion_types[0] >= 100:
#                         potion_counts[2] += 1
#                         potion_types[0] -= 100
#                     else:
#                         break
#                 made_potion = True
#             # Red (id: 1)
#             elif 1 in potion_types_map and potion_types[1] >= 100:
#                 for _ in range(5):  # Create 5 red potions with quantity 1
#                     if potion_types[1] >= 100:
#                         potion_counts[1] += 1
#                         potion_types[1] -= 100
#                     else:
#                         break
#                 made_potion = True
#             # Blue (id: 3)
#             elif 3 in potion_types_map and potion_types[2] >= 100:
#                 for _ in range(5):  # Create 5 blue potions with quantity 1
#                     if potion_types[2] >= 100:
#                         potion_counts[3] += 1
#                         potion_types[2] -= 100
#                     else:
#                         break
#                 made_potion = True
#             # Dark (id: 4)
#             elif 4 in potion_types_map and potion_types[3] >= 100 and gold >= 700:
#                 for _ in range(5):  # Create 5 dark potions with quantity 1
#                     if potion_types[3] >= 100 and gold >= 700:
#                         potion_counts[4] += 1
#                         potion_types[3] -= 100
#                         gold -= 700
#                     else:
#                         break
#                 made_potion = True
#             if not made_potion:
#                 break
#         return potion_counts

# if __name__ == "__main__":
#     print(get_bottle_plan())

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

        potion_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
        potion_counts = {potion_id: 0 for potion_id in potion_types_map.keys()}

        while True:
            made_potion = False
            min_count = min((count for potion_id, count in potion_counts.items() if potion_id != 4), default=0)
            potion_to_make = next((potion_id for potion_id, count in potion_counts.items() if count == min_count and potion_id != 4), None)

            if potion_to_make is not None:
                if potion_to_make == 5 and potion_types[2] >= 50 and potion_types[1] >= 50:
                    potion_counts[5] += 1
                    potion_types[2] -= 50
                    potion_types[1] -= 50
                    made_potion = True
                elif potion_to_make == 2 and potion_types[0] >= 100:
                    potion_counts[2] += 1
                    potion_types[0] -= 100
                    made_potion = True
                elif potion_to_make == 1 and potion_types[1] >= 100:
                    potion_counts[1] += 1
                    potion_types[1] -= 100
                    made_potion = True
                elif potion_to_make == 3 and potion_types[2] >= 100:
                    potion_counts[3] += 1
                    potion_types[2] -= 100
                    made_potion = True

            if 4 in potion_types_map and potion_types[3] >= 100 and gold >= 700:
                potion_counts[4] += 1
                potion_types[3] -= 100
                gold -= 700
                made_potion = True

            if not made_potion:
                break

        return potion_counts

if __name__ == "__main__":
    print(get_bottle_plan())