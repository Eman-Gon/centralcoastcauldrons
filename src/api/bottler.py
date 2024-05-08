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
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                    {"description": f"Delivery of bottled potions (order {order_id})"}).scalar_one()
        #transaction_id = result.scalar_one()

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        # Add a new transaction
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), 
                                    {"description": f"Delivery of bottled potions (order {order_id})"})
        transaction_id = result.scalar_one()

        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                connection.execute(sqlalchemy.text("""
                    INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)
                    VALUES (:transaction_id, 'green', :change_in_ml)
                """), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})

            elif potion.potion_type == [100, 0, 0, 0]:
                connection.execute(sqlalchemy.text("""
                    INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)
                    VALUES (:transaction_id, 'red', :change_in_ml)
                """), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})

            elif potion.potion_type == [0, 0, 100, 0]:
                connection.execute(sqlalchemy.text("""
                    INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)
                    VALUES (:transaction_id, 'blue', :change_in_ml)
                """), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})

            elif potion.potion_type == [0, 0, 0, 100]:
                connection.execute(sqlalchemy.text("""
                    INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)
                    VALUES (:transaction_id, 'dark', :change_in_ml)
                """), {"transaction_id": transaction_id, "change_in_ml": -(100 * potion.quantity)})

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """Go from barrel to bottle."""
    with db.engine.begin() as connection:
        # Find amount of space left in potion_capacity
        potion_capacity = (connection.execute(sqlalchemy.text("SELECT potion_capacity FROM global_values")).scalar_one()
         - connection.execute(sqlalchemy.text("SELECT total_potions FROM inventory_summary_view")).scalar())

        # Query ml_inventory_view
        ml_inventory = connection.execute(sqlalchemy.text("SELECT color, total_ml FROM ml_ledger_entries_view")).fetchall()
        ml_inventory_dict = {row.color: row.total_ml for row in ml_inventory}

        # Query total gold
        total_gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar()

        # Query potion_type from potion_inventory (make sure it's a list)
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potion_inventory")).fetchall()

        # Sort potions based on potion_type
        potions.sort(key=lambda potion: (
            5 in potion.potion_type,  # Prioritize potions with type 5
            potion.potion_type.count(1),  # Sort by count of type 1
            potion.potion_type.count(2),  # Sort by count of type 2
            potion.potion_type.count(3),  # Sort by count of type 3
            potion.potion_type.count(4)   # Sort by count of type 4
        ))
        
        #priority logic the least of
        # Make dictionary: <k,v>[potion_type, 0]
        potion_counts = {}
        for potion in potions:
            potion_counts[tuple(potion.potion_type)] = 0

        made_one = True
        while made_one:
            made_one = False
            for potion in potions:
                # Check if you can make the potion (have enough ml and have enough space)
                potion_type = tuple(potion.potion_type)
                if potion.id == 5:  # Yellow potion
                    if (50 <= ml_inventory_dict.get('red', 0) and
                        50 <= ml_inventory_dict.get('blue', 0) and
                        potion_counts[potion_type] < potion_capacity):
                        # Subtract from ml_inventory_dict
                        ml_inventory_dict['red'] -= 50
                        ml_inventory_dict['blue'] -= 50
                        # Increment potion count in dictionary
                        potion_counts[potion_type] += 1
                        made_one = True
                else:
                    if ((len(potion_type) >= 1 and potion_type[0] <= ml_inventory_dict.get('red', 0)) and
                        (len(potion_type) >= 2 and potion_type[1] <= ml_inventory_dict.get('green', 0)) and
                        (len(potion_type) >= 3 and potion_type[2] <= ml_inventory_dict.get('blue', 0)) and
                        (total_gold < 7000 or (len(potion_type) >= 4 and potion_type[3] <= ml_inventory_dict.get('dark', 0))) and
                        potion_counts[potion_type] < potion_capacity):
                        # Subtract from ml_inventory_dict
                        ml_inventory_dict['red'] -= potion_type[0] if len(potion_type) >= 1 else 0
                        ml_inventory_dict['green'] -= potion_type[1] if len(potion_type) >= 2 else 0
                        ml_inventory_dict['blue'] -= potion_type[2] if len(potion_type) >= 3 else 0
                        if len(potion_type) >= 4 and total_gold >= 7000:
                            ml_inventory_dict['dark'] -= potion_type[3]
                        # Increment potion count in dictionary
                        potion_counts[potion_type] += 1
                        made_one = True

        # Create the plan
        plan = []
        for potion in potions:
            potion_type = tuple(potion.potion_type)
            if potion_counts[potion_type] > 0:
                plan.append({
                    "potion_type": potion_type,
                    "quantity": potion_counts[potion_type]
                })
        return plan

if __name__ == "__main__":
    print(get_bottle_plan())