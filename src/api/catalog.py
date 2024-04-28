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
                    "potion_type": [
                        x.num_red_potions,
                        x.num_green_potions,
                        x.num_blue_potions,
                        x.num_dark_potions,
                        x.num_yellow_potions
                    ]

                })
                numItems += 1
                if (numItems == 6):
                    break



        
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