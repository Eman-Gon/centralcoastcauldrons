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
        for potion in potions_delivered:
            if potion.potion_id == 1:  # Red
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = 1"))
            elif potion.potion_id == 2:  # Green
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = 2"))
            elif potion.potion_id == 3:  # Blue
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = 3"))
            elif potion.potion_id == 4:  # Dark
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml - {100 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = 4"))
            elif potion.potion_id == 5:  # Yellow
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {50 * potion.quantity}, num_blue_ml = num_blue_ml - {50 * potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = quantity + {potion.quantity} WHERE id = 5"))
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
        # Yellow (id: 5)
        if potion_types[2] >= 50 and potion_types[1] >= 50:
            plan.append({
                "quantity": 1,
                "potion_id": 5
            })
            potion_types[2] -= 50
            potion_types[1] -= 50
            made_potion = True

        # Green (id: 2)
        elif potion_types[0] >= 100:
            plan.append({
                "quantity": 1,
                "potion_id": 2
            })
            potion_types[0] -= 100
            made_potion = True

        # Red (id: 1)
        elif potion_types[1] >= 100:
            plan.append({
                "quantity": 1,
                "potion_id": 1
            })
            potion_types[1] -= 100
            made_potion = True

        # Blue (id: 3)
        elif potion_types[2] >= 100:
            plan.append({
                "quantity": 1,
                "potion_id": 3
            })
            potion_types[2] -= 100
            made_potion = True

        # Dark (id: 4)
        elif potion_types[3] >= 100:
            plan.append({
                "quantity": 1,
                "potion_id": 4
            })
            potion_types[3] -= 100
            made_potion = True

        if not made_potion:
            break

    return plan

if __name__ == "__main__":
    plan = get_bottle_plan()
    print("Plan:", plan)






















    
# import sqlalchemy
# from src import database as db
# from fastapi import APIRouter, Depends
# from enum import Enum
# from pydantic import BaseModel
# from src.api import auth

# router = APIRouter(
#     prefix="/bottler",
#     tags=["bottler"],
#     dependencies=[Depends(auth.get_api_key)],
# )

# class PotionInventory(BaseModel):
#     potion_type: list[int]
#     quantity: int

# @router.post("/deliver/{order_id}")
# def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
#     print(f"potions delivered: {potions_delivered} order_id: {order_id}")

#     with db.engine.begin() as connection:
#      potion_type_result = db.engine.execute(sqlalchemy.text("SELECT potion_type, id FROM potion_inventory"))
#      potion_type_map = {row.potion_type: row.id for row in potion_type_result}

   
#     for potion in potions_delivered:
#             potion_type_id = potion_type_map.get(potion.potion_type)


#             if potion_type_id == 1:  
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - {100 * potion.quantity}"))
#                 connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity WHERE id = 1"))
#             elif potion_type_id == 2:  
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {100 * potion.quantity}"))
#                 connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity WHERE id = 2"))
#             elif potion_type_id == 3:  
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - {100 * potion.quantity}"))
#                 connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity WHERE id = 3"))
#             elif potion_type_id == 4:  
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml - {100 * potion.quantity}"))
#                 connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET quantity = {potion.quantity} + quantity WHERE id = 4"))

#     return "OK"


# @router.post("/plan")
# def get_bottle_plan():
#     """ Go from barrel to bottle. """
#     with db.engine.begin() as connection:
#         num_green_ml = connection.execute(sqlalchemy.text(f"SELECT num_green_ml FROM global_inventory")).scalar_one()
#         num_red_ml = connection.execute(sqlalchemy.text(f"SELECT num_red_ml FROM global_inventory")).scalar_one()
#         num_blue_ml = connection.execute(sqlalchemy.text(f"SELECT num_blue_ml FROM global_inventory")).scalar_one()
#         num_dark_ml = connection.execute(sqlalchemy.text(f"SELECT num_dark_ml FROM global_inventory")).scalar_one()

#         print(f"Available milliliters: Green={num_green_ml}, Red={num_red_ml}, Blue={num_blue_ml}, Dark={num_dark_ml}")

#         potion_type_query = sqlalchemy.text("SELECT id, potion_type FROM potion_inventory ORDER BY id")
#         result = connection.execute(potion_type_query)
#         potion_types = []
#         for row in result:
#             potion_type = row.potion_type
#             potion_id = row.id
#             potion_types.append([potion_type, potion_id])

#         print("Potion types fetched from the database:")
#         for potion_type_entry in potion_types:
#             print(potion_type_entry)

#         plan = []

#         for potion_type_entry in potion_types:
#             potion_type, potion_id = potion_type_entry
#             green_qty, red_qty, blue_qty, dark_qty = potion_type

#             # Skip potion types with zero required quantities
#             if green_qty == 0 or red_qty == 0 or blue_qty == 0 or dark_qty == 0:
#                 continue

#             print(f"Potion type: {potion_type}, Required quantities: Green={green_qty}, Red={red_qty}, Blue={blue_qty}, Dark={dark_qty}")

#             # Calculate the maximum quantity that can be made
#             max_quantity = min(
#                 num_green_ml // green_qty,
#                 num_red_ml // red_qty,
#                 num_blue_ml // blue_qty,
#                 num_dark_ml // dark_qty,
#             )

#             print(f"Maximum quantity that can be made: {max_quantity}")

#             # Update the milliliter amounts
#             num_green_ml -= green_qty * max_quantity
#             num_red_ml -= red_qty * max_quantity
#             num_blue_ml -= blue_qty * max_quantity
#             num_dark_ml -= dark_qty * max_quantity

#             # Append the plan with the desired quantity
#             if max_quantity > 0:
#                 plan.append({"quantity": max_quantity, "potion_id": potion_id})

#     print("Final plan:", plan)
#     return plan

# if __name__ == "__main__":
#     plan = get_bottle_plan()
#     print("Plan:", plan)
# #updating quantity varvable outside the while loop then
# #it would update the ml 
# #then you would have the quqanities you want to make 
# #then add them to plan and  append



#     #each time you have a update glbal invenort ml,gold, potion_qunrity youll insert into the ledger table from the specific thing your changing 