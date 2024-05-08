import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    total_used = {
        "green": 0,
        "red": 0,
        "blue": 0,
        "dark": 0
    }
    total_price = 0

    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 1, 0, 0]:
            total_used["green"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [1, 0, 0, 0]:
            total_used["red"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]:
            total_used["blue"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 0, 1]:
            total_used["dark"] += barrel.ml_per_barrel * barrel.quantity
        total_price += barrel.price * barrel.quantity

    with db.engine.begin() as connection:
        # Add a new transaction
        transaction_id = connection.execute(
            sqlalchemy.text(
                "INSERT INTO transactions (description) VALUES (:description) RETURNING id"
            ), 
            {"description": f"Delivery of barrels (order {order_id})"}
        ).scalar_one()

        for color in total_used:
            if total_used[color] > 0:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, :color, :change_in_ml)"),
                                    {
                                        "transaction_id": transaction_id,
                                        "color": color,
                                        "change_in_ml": total_used[color]
                                    }
                                   )

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'green', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_green_ml})

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'red', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_red_ml})

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'blue', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_blue_ml})

        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml)VALUES (:transaction_id, 'dark', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_dark_ml})
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change_in_gold) VALUES (:transaction_id, :total_price)"),
                                    {
                                        "transaction_id": transaction_id,
                                        "total_price": total_price * -1
                                    }
                                   )
        
#if qunaity greater 0 then dont put table
    print(f"Total Green ML: {total_used['green']}, Total Red ML: {total_used['red']}, Total Blue ML: {total_used['blue']}, Total Dark ML: {total_used['dark']}, Total Price: {total_price}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        # Calculate the current inventory levels from the ledger tables
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar_one() or 0
        num_green_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'green'")).scalar_one() or 0
        num_red_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'red'")).scalar_one() or 0
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'blue'")).scalar_one() or 0
        num_dark_ml = connection.execute(sqlalchemy.text("SELECT total_ml FROM ml_ledger_entries_view WHERE color = 'dark'")).scalar_one() or 0

        # Retrieve potion quantities from the potion_inventory table
        potion_quantities = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM potion_inventory_view")).fetchall()
        potion_quantities = {potion_id: quantity for potion_id, quantity in potion_quantities}
        

        # Sort small barrels by ascending ml_per_barrel
        sorted_small_barrels = sorted((barrel for barrel in wholesale_catalog if 'SMALL' in barrel.sku), key=lambda barrel: barrel.ml_per_barrel)

        # Query all color potions in order of ml_per_barrel
        potion_quantities_list = []
        for barrel in sorted_small_barrels:
            if barrel.potion_type == [0, 1, 0, 0]:
                potion_quantities_list.append((barrel, potion_quantities.get(2, 0)))
            elif barrel.potion_type == [1, 0, 0, 0]:
                potion_quantities_list.append((barrel, potion_quantities.get(1, 0)))
            elif barrel.potion_type == [0, 0, 1, 0]:
                potion_quantities_list.append((barrel, potion_quantities.get(3, 0)))
            elif barrel.potion_type == [0, 0, 0, 1]:
                potion_quantities_list.append((barrel, potion_quantities.get(4, 0)))

        # Sort the barrels in ascending order based on ml_per_barrel
        potion_quantities_list.sort(key=lambda x: x[0].ml_per_barrel)

        barrel_plan = []
        for barrel, potion_qty in potion_quantities_list:
            if potion_qty < 10 and gold >= barrel.price:
                barrel_plan.append({"sku": barrel.sku, "quantity": 1})
                gold -= barrel.price
            else:
                break

    return barrel_plan





        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'green', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_green_ml})
        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'red', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_red_ml})
        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'blue', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_blue_ml})
        # connection.execute(sqlalchemy.text("INSERT INTO ml_ledger_entries (transaction_id, color, change_in_ml) VALUES (:transaction_id, 'dark', :change_in_ml)"), {"transaction_id": transaction_id, "change_in_ml": total_dark_ml})
