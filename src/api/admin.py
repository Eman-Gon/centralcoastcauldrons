import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    with db.engine.begin() as connection:
        # Reset potion_inventory table
        connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = 0"))
        
        # Reset ml_ledger_entries table
        connection.execute(sqlalchemy.text("TRUNCATE ml_ledger_entries"))
        
        # Reset gold_ledger_entries table
        connection.execute(sqlalchemy.text("TRUNCATE gold_ledger_entries"))
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (change_in_gold) VALUES (100)"))
        
        # Reset carts table
        connection.execute(sqlalchemy.text("TRUNCATE carts CASCADE"))
        
        # Reset cart_sales table
        connection.execute(sqlalchemy.text("TRUNCATE cart_sales CASCADE"))
        
        # Reset transactions table
        connection.execute(sqlalchemy.text("TRUNCATE transactions CASCADE"))
        
    return "OK"