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
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries_view (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'green', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 2, "change_in_potion": potion.quantity})
            elif potion.potion_type == [100, 0, 0, 0]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries_view (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'red', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 1, "change_in_potion": potion.quantity})
            elif potion.potion_type == [0, 0, 100, 0]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries_view (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'blue', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 3, "change_in_potion": potion.quantity})
            elif potion.potion_type == [0, 0, 0, 100]:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries_view (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'dark', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})
                connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": 4, "change_in_potion": potion.quantity})

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """Go from barrel to bottle."""
    with db.engine.begin() as connection:
        # Find amount of space left in potion_capacity
        potion_capacity = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(quantity), 0) FROM potion_inventory_view")).scalar()

        # Query ml_inventory_view
        ml_inventory = connection.execute(sqlalchemy.text("SELECT potion_type FROM ml_ledger_entries_view")).fetchall()
        ml_inventory_dict = {row.potion_type: 0 for row in ml_inventory}

        # Query total gold
        total_gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change_in_gold), 0) FROM gold_ledger_entries")).scalar()

        # Query potion_type from potion_inventory (make sure it's a list)
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potion_inventory")).fetchall()

        # Sort potions based on potion_type
        potions.sort(key=lambda potion: (potion.potion_type[1], potion.potion_type[0], potion.potion_type[2], potion.potion_type[3]))

        # Make dictionary: <k,v>[potion_type, 0]
        potion_counts = {}
        for potion in potions:
            potion_counts[tuple(potion.potion_type)] = 0

        made_one = True
        while made_one:
            made_one = False
            for potion in potions:
                # Check if you can make the potion (have enough ml and have enough space)
                potion_type = potion.potion_type
                if (potion_type[0] <= ml_inventory_dict.get(potion_type, 0) and
                    potion_type[1] <= ml_inventory_dict.get(potion_type, 0) and
                    potion_type[2] <= ml_inventory_dict.get(potion_type, 0) and
                    (potion_type[3] <= ml_inventory_dict.get(potion_type, 0) or total_gold < 7000) and
                    potion_counts[tuple(potion_type)] < potion_capacity):
                    # Subtract from ml_inventory_dict
                    ml_inventory_dict[potion_type] -= potion_type[0] + potion_type[1] + potion_type[2]
                    if total_gold >= 7000:
                        ml_inventory_dict[potion_type] -= potion_type[3]
                    # Increment potion count in dictionary
                    potion_counts[tuple(potion_type)] += 1
                    made_one = True

        # Create the plan
        plan = []
        for potion in potions:
            if potion_counts[tuple(potion.potion_type)] > 0:
                plan.append({
                    "potion_type": potion.potion_type,
                    "quantity": potion_counts[tuple(potion.potion_type)]
                })
        return plan

if __name__ == "__main__":
    print(get_bottle_plan())