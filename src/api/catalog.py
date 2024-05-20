import sqlalchemy
from src import database as db
from fastapi import APIRouter
from src.api.bottler import get_bottle_plan

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combination must have only a single price."""
    with db.engine.begin() as connection:
        made_pot = get_bottle_plan()
        print("Bottler Plan: ")
        print(made_pot)
        made_as_dictionary = {}
        for p in made_pot:
            sku = connection.execute(sqlalchemy.text("SELECT sku FROM potion_inventory WHERE potion_type = :potion_type"), {"potion_type": p["potion_type"]}).scalar_one()
            made_as_dictionary[sku] = p["quantity"]

        catalog = []
        result = connection.execute(sqlalchemy.text("""
            SELECT price, sku, potion_type, quantity
            FROM potion_inventory_view
            WHERE sku != 'dark_green'
            ORDER BY (CASE WHEN sku IN ('green', 'red', 'blue', 'dark') THEN 0 ELSE random() + 1 END)
            LIMIT 6
        """))

        numItems = 0
        for x in result:
            if x.sku in made_as_dictionary.keys():
                just_made = made_as_dictionary[x.sku]
            else:
                just_made = 0

            if x.quantity + just_made > 0:
                catalog.append({
                    "sku": x.sku,
                    "name": x.sku,
                    "quantity": x.quantity + just_made,
                    "price": x.price,
                    "potion_type": x.potion_type
                })
                numItems += 1
            if numItems == 6:
                break

        return catalog