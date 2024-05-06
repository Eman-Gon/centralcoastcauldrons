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
        # Add a new transaction
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), {"description": f"Delivery of bottled potions (order {order_id})"})
        transaction_id = result.scalar_one()

        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'green', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 2, "change_in_potion": potion.quantity})
            elif potion.potion_type == [100, 0, 0, 0]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'red', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 1, "change_in_potion": potion.quantity})
            elif potion.potion_type == [0, 0, 100, 0]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'blue', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 3, "change_in_potion": potion.quantity})
            elif potion.potion_type == [0, 0, 0, 100]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'dark', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 4, "change_in_potion": potion.quantity})

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    with db.engine.begin() as connection:
        # Calculate the current ml levels from the ledger tables
        num_green_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_in_ml) FROM ml_ledger_entries WHERE color = 'green'")).scalar_one() or 0
        num_red_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_in_ml) FROM ml_ledger_entries WHERE color = 'red'")).scalar_one() or 0
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_in_ml) FROM ml_ledger_entries WHERE color = 'blue'")).scalar_one() or 0
        num_dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(change_in_ml) FROM ml_ledger_entries WHERE color = 'dark'")).scalar_one() or 0
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change_in_gold) FROM gold_ledger_entries")).scalar_one() or 0

        # Query the potion_type from the potion_inventory table
        potion_types_result = connection.execute(sqlalchemy.text("SELECT id, potion_type FROM potion_inventory")).fetchall()
        potion_types_map = {potion_id: potion_type for potion_id, potion_type in potion_types_result}

    potion_types = [num_green_ml, num_red_ml, num_blue_ml, num_dark_ml]
    plan = []

    while True:
        made_potion = False
        # Yellow (id: 5)
        if 5 in potion_types_map and potion_types[2] >= 250 and potion_types[1] >= 250:
            plan.append({
                "quantity": 5,
                "potion_type": potion_types_map[5]
            })
            potion_types[2] -= 250
            potion_types[1] -= 250
            made_potion = True

        # Green (id: 2)
        elif 2 in potion_types_map and potion_types[0] >= 500:
            plan.append({
                "quantity": 5,
                "potion_type": potion_types_map[2]
            })
            potion_types[0] -= 500
            made_potion = True

        # Red (id: 1)
        elif 1 in potion_types_map and potion_types[1] >= 500:
            plan.append({
                "quantity": 5,
                "potion_type": potion_types_map[1]
            })
            potion_types[1] -= 500
            made_potion = True

        # Blue (id: 3)
        elif 3 in potion_types_map and potion_types[2] >= 500:
            plan.append({
                "quantity": 5,
                "potion_type": potion_types_map[3]
            })
            potion_types[2] -= 500
            made_potion = True

        # Dark (id: 4)
        elif 4 in potion_types_map and potion_types[3] >= 500 and gold >= 3500:
            plan.append({
                "quantity": 5,
                "potion_type": potion_types_map[4]
            })
            potion_types[3] -= 500
            made_potion = True

        if not made_potion:
            break

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
