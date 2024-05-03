import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list [int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0
    total_dark_ml = 0
    total_price = 0

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            if barrel.potion_type == [0,1,0,0]:
                total_green_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [1,0,0,0]:
                total_red_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0,0,1,0]:
                total_blue_ml += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0,0,0,1]:
                total_dark_ml += barrel.ml_per_barrel * barrel.quantity
            total_price += barrel.price * barrel.quantity

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {total_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {total_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_dark_ml = num_dark_ml + {total_dark_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {total_price}"))

    print(f"Total Green ML: {total_green_ml}, Total Red ML: {total_red_ml}, Total Blue ML: {total_blue_ml}, Total Dark ML: {total_dark_ml}, Total Price: {total_price}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        # Query the current inventory levels and capacities from the global_inventory table
        inventory_result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold, capacity_ml, capacity_potion FROM global_inventory")).fetchone()
        num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold, capacity_ml, capacity_potion = inventory_result

        # Query the potion types and quantities from the potion_inventory table
        potion_inventory_result = connection.execute(sqlalchemy.text("SELECT id, potion_type, quantity FROM potion_inventory"))
        potion_inventory = {row[0]: {'potion_type': row[1], 'quantity': row[2]} for row in potion_inventory_result}

    potion_types = [num_red_ml, num_green_ml, num_blue_ml, num_dark_ml]
    potion_counts = {potion_id: 0 for potion_id in potion_inventory.keys()}

    while True:
        made_potion = False
        # Yellow (id: 5)
        if 5 in potion_inventory and potion_types[2] >= 50 and potion_types[1] >= 50 and sum(potion_counts.values()) < capacity_potion:
            potion_counts[5] += 1
            potion_types[2] -= 50
            potion_types[1] -= 50
            made_potion = True

        # Green (id: 2)
        elif 2 in potion_inventory and potion_types[0] >= 100 and sum(potion_counts.values()) < capacity_potion:
            potion_counts[2] += 1
            potion_types[0] -= 100
            made_potion = True

        # Red (id: 1)
        elif 1 in potion_inventory and potion_types[1] >= 100 and sum(potion_counts.values()) < capacity_potion:
            potion_counts[1] += 1
            potion_types[1] -= 100
            made_potion = True

        # Blue (id: 3)
        elif 3 in potion_inventory and potion_types[2] >= 100 and sum(potion_counts.values()) < capacity_potion:
            potion_counts[3] += 1
            potion_types[2] -= 100
            made_potion = True

        # Dark (id: 4)
        elif 4 in potion_inventory and potion_types[3] >= 100 and gold >= 700 and sum(potion_counts.values()) < capacity_potion:
            potion_counts[4] += 1
            potion_types[3] -= 100
            made_potion = True

        if not made_potion:
            break

    return potion_counts

if __name__ == "__main__":
    print(get_bottle_plan())