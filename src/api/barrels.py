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
        "red": 0,
        "green": 0,
        "blue": 0,
        "dark": 0
    }
    total_price = 0

    for barrel in barrels_delivered:
        
        if barrel.potion_type == [1, 0, 0, 0]:
            total_used["red"] += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 1, 0, 0]:
            total_used["green"] += barrel.ml_per_barrel * barrel.quantity
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

        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change_in_gold) VALUES (:transaction_id, :total_price)"),
                                    {
                                        "transaction_id": transaction_id,
                                        "total_price": total_price * -1
                                    }
                                   )
        
    print(f"Total Red ML: {total_used['red']}, Total Green ML: {total_used['green']}, Total Blue ML: {total_used['blue']}, Total Dark ML: {total_used['dark']}, Total Price: {total_price}")
    return "OK"

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    with db.engine.begin() as connection:
        # Query current mL for each color
        current_ml = {}
        for color in ['red', 'green', 'blue', 'dark']:
            current_ml[color] = connection.execute(sqlalchemy.text(f"SELECT COALESCE(SUM(ml_ledger_entries.change_in_ml), 0) FROM ml_ledger_entries WHERE color = '{color}'")).scalar_one() or 0

        # Query total mL capacity
        total_ml_capacity = connection.execute(sqlalchemy.text("SELECT ml_capacity FROM global_values LIMIT 1")).scalar_one() or 0

        # Query the gold available
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM inventory_summary_view")).scalar_one() or 0

        barrel_plan = []

        for color in ['red', 'green', 'blue', 'dark']:
            color_threshold = total_ml_capacity // 4
            remaining_color_capacity = color_threshold - current_ml[color]
            overall_remaining_capacity = total_ml_capacity - sum(current_ml.values())

            # Check for large barrels first
            large_barrels = [b for b in wholesale_catalog if 'LARGE' in b.sku and b.potion_type[['red','green', 'blue', 'dark'].index(color)]]
            if large_barrels:
                for b in large_barrels:
                    qty = min(
                        gold // b.price,
                        remaining_color_capacity // b.ml_per_barrel,
                        overall_remaining_capacity // b.ml_per_barrel,
                        b.quantity
                    )

                    if qty > 0:
                        barrel_plan.append({"sku": b.sku, "quantity": qty})
                        gold -= b.price * qty
                        current_ml[color] += b.ml_per_barrel * qty
                        remaining_color_capacity -= b.ml_per_barrel * qty
                        overall_remaining_capacity -= b.ml_per_barrel * qty

            # If no large barrels, check for medium barrels
            else:
                medium_barrels = [b for b in wholesale_catalog if 'MEDIUM' in b.sku and b.potion_type[[ 'red', 'green','blue', 'dark'].index(color)]]
                if medium_barrels:
                    for b in medium_barrels:
                        qty = min(
                            gold // b.price,
                            remaining_color_capacity // b.ml_per_barrel,
                            overall_remaining_capacity // b.ml_per_barrel,
                            b.quantity
                        )

                        if qty > 0:
                            barrel_plan.append({"sku": b.sku, "quantity": qty})
                            gold -= b.price * qty
                            current_ml[color] += b.ml_per_barrel * qty
                            remaining_color_capacity -= b.ml_per_barrel * qty
                            overall_remaining_capacity -= b.ml_per_barrel * qty

    return barrel_plan