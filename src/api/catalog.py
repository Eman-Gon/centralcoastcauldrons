import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combination must have only a single price."""
    with db.engine.begin() as connection:
        catalog = []
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory")).one()

        

        if result.num_red_ml > 0:
            catalog.append({
                "sku": "RED_POTION_0",
                "name": "red",
                "quantity": 40,
                "price": 50,
                "potion_type": [100, 0, 0, 0]
            })

        if result.num_green_ml > 0:
            catalog.append({
                "sku": "GREEN_POTION_0",
                "name": "green",
                "quantity": 40,
                "price": 50,
                "potion_type": [0, 100, 0, 0]
            })

        if result.num_blue_ml > 0:
            catalog.append({
                "sku": "BLUE_POTION_0",
                "name": "blue",
                "quantity": 40,
                "price": 50,
                "potion_type": [0, 0, 100, 0]
            })

        return catalog
        
        # unique_potions = set()
        # counter = 0



        # for potion in connection.execute(sqlalchemy.text("SELECT * FROM potion_inventory")):
        #     if potion.quantity > 0:
        #         potion_type = potion.num_red_potions,
        #         potion.num_green_potions,
        #         potion.num_blue_potions,
        #         potion.num_dark_potions
                
        #         if potion_type not in unique_potions and counter < 6:
        #             unique_potions.add(potion_type)
        #             catalog.append({
        #                 "sku": potion.sku,
        #                 "name": potion.sku,
        #                 "quantity": potion.quantity,
        #                 "price": potion.price,
        #                 "potion_type": [potion.num_red_potions,
        #         potion.num_green_potions,
        #         potion.num_blue_potions,
        #         potion.num_dark_potions],
                
        #             })
        #             print(potion_type)
                
        #             counter += 1

    #return catalog

    
# have ever cahngin catolog where you would 

    #can only sell up to sic using counter