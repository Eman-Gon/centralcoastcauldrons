import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    with db.engine.begin() as connection:
    
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = 0, num_red_potions = 0, num_blue_potions = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = 0, num_red_ml = 0, num_blue_ml = 0"))
        # connection.execute(sqlalchemy.text("DELETE FROM carts"))
        # connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
    return "OK"

#okay i want to rest my whole thing