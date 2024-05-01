import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combination must have only a single price."""
    with db.engine.begin() as connection:
        catalog = []
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_inventory"))
        numItems = 0

        for x in result:
            if(x.quantity > 0):
                catalog.append({
                    "sku": x.sku,
                    "name": x.sku,
                    "quantity": x.quantity,
                    "price": x.price,
                    "potion_type": x.potion_type

                })
                numItems += 1
                if (numItems == 6):
                    break



        
        return catalog