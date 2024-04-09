import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions From global_inventory")).scalor_one()
        if (result != 0):
         return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": 0,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
