import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combination must have only a single price."""
    with db.engine.begin() as connection:
        # Retrieve potion information from the potion_inventory table
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potion_inventory"))
        catalog = []
        unique_potions = set()
        counter = 0



        for potion in potions:
            if potion.quantity > 0:
                potion_type = potion.num_red_potions,
                potion.num_green_potions,
                potion.num_blue_potions,
                potion.num_dark_potions
                
                if potion_type not in unique_potions and counter < 6:
                    unique_potions.add(potion_type)
                    catalog.append({
                        "sku": potion.sku,
                        "name": potion.sku,
                        "quantity": potion.quantity,
                        "price": potion.price,
                        "potion_type": [potion.num_red_potions,
                potion.num_green_potions,
                potion.num_blue_potions,
                potion.num_dark_potions],
                
                    })
                    print(potion_type)
                
                    counter += 1

    return catalog

    
# have ever cahngin catolog where you would 

    #can only sell up to sic using counter