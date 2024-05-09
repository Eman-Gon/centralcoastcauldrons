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
        mlUsed = [0, 0, 0, 0]

        # Insert into transactions, returning id
        transaction_id = connection.execute(sqlalchemy.text("""
            INSERT INTO transactions (description)
            VALUES ('Deliver potions')
            RETURNING id
        """)).scalar()

        for p in potions_delivered:
            for i in range(0, 4):
                mlUsed[i] += p.potion_type[i] * p.quantity

            # Insert entry into potion_ledger_entries
            potion_id = connection.execute(sqlalchemy.text("""
                SELECT id FROM potion_inventory
                WHERE potion_type = :potion_type
            """), {"potion_type": p.potion_type}).scalar()

            connection.execute(sqlalchemy.text("""
                INSERT INTO potion_ledger_entries (potion_id, change_in_potion, transaction_id)
                VALUES (:potion_id, :change_in_potion, :transaction_id)
            """), {"potion_id": potion_id, "change_in_potion": p.quantity, "transaction_id": transaction_id})

        # Insert entries into ml_ledger_entries
        colors = ['red', 'green', 'blue', 'dark']
        for i, color in enumerate(colors):
            connection.execute(sqlalchemy.text("""
                INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)
                VALUES (:transaction_id, :color, :change_in_ml)
            """), {"transaction_id": transaction_id, "color": color, "change_in_ml": mlUsed[i] * -1})

    return "OK"


@router.post("/plan")
def get_bottle_plan():
    """Go from barrel to bottle."""
    with db.engine.begin() as connection:
        # Find amount of space left in potion_capacity
        ml_inventory = [0,0,0,0]
        potion_capacity, total_potions, ml_inventory[0], ml_inventory[1], ml_inventory[2], ml_inventory[3] = connection.execute(sqlalchemy.text(
                """
                SELECT 
                    (
                        SELECT potion_capacity FROM global_values
                    ) as potion_capacity,
                    (
                        SELECT total_potions FROM inventory_summary_view
                    ) as total_potions,
                    (
                        SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'red'
                    ) as red_ml,
                    (
                        SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'green'
                    ) as green_ml,
                    (
                        SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'blue'
                    ) as blue_ml,
                    (
                        SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'dark'
                    ) as dark_ml
                                            

                """
            )
        ).fetchone()
        space_available = potion_capacity - total_potions

        # Query ml_inventory_view
        # ml_inventory = connection.execute(sqlalchemy.text("SELECT color, total_ml FROM ml_ledger_entries_view")).fetchall()
        # ml_inventory_dict = {row.color: row.total_ml for row in ml_inventory}

        # Query total gold
        # total_gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar()

        # Query potion_type from potion_inventory (make sure it's a list)
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potion_inventory")).fetchall()

        # Make dictionary: <k,v> [id, 0]
        potion_inventory_dict = {potion.id: 0 for potion in potions}

        made_one = True
        while made_one:
            made_one = False
            for potion in potions:
                # Check if the potion can be made (have enough ml and space)
                can_make_potion = True
                for i in range(0,4):
                    if ml_inventory[i] < potion.potion_type[i]:
                        can_make_potion = False
                        break
                if can_make_potion and space_available > 0:
                    # Subtract the required ml from the ml_inventory_dict
                    for i in range(0,4):
                        ml_inventory[i] -= potion.potion_type[i]
                    potion_inventory_dict[potion.id] += 1
                    space_available -= 1
                    made_one = True

        # Create the plan
        plan = []
    for potion_id, quantity in potion_inventory_dict.items():  # Iterate over the key-value pairs in potion_inventory_dict
        potion_type = next(potion.potion_type for potion in potions if potion.id == potion_id)  # Find the potion_type for the current potion_id
    
        if quantity > 0:
            plan.append({"potion_type": potion_type, "quantity": quantity})

    return plan
if __name__ == "__main__":
    print(get_bottle_plan())



#      make dictionary :<k,v>[id,0]
#     madeone = Truewhile made one = True
#     madeone = False
#     for potion in potionList:
#     if you can make it:
# if you can make it:(have enough ml and have enough space things to cosnider)
# subtract from ml PotionInventorydict[potion id] + =1
# madeone=True

# #after loop
# plan =[]

# for potion in potionList:
#     plan.append(["potion_type":potion.potiontype,"quuantity": potion.quantity])
#     return plan

# So also make sure Id as key in dict and only id and potion type