import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:customer) RETURNING id"), {"customer":new_cart.customer_name})
        cart_id = result.scalar()
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT id FROM potion_inventory WHERE sku = :item_sku"), {"item_sku": item_sku})
        potion_id = result.scalar()

        if potion_id:
            result = connection.execute(sqlalchemy.text("SELECT quantity FROM cart_sales WHERE cart_id = :cart_id AND potion_id = :potion_id"),
                                        {"cart_id": cart_id, "potion_id": potion_id})
            existing_quantity = result.scalar()

            if existing_quantity:
                # Update the quantity if the item already exists
                connection.execute(sqlalchemy.text("UPDATE cart_sales SET quantity = :quantity WHERE cart_id = :cart_id AND potion_id = :potion_id"),
                                   {"quantity": cart_item.quantity, "cart_id": cart_id, "potion_id": potion_id})
            else:
                # Insert a new entry if the item doesn't exist
                connection.execute(sqlalchemy.text("INSERT INTO cart_sales (cart_id, potion_id, quantity) VALUES (:cart_id, :potion_id, :quantity)"),
                                   {"cart_id": cart_id, "potion_id": potion_id, "quantity": cart_item.quantity})

            return "OK"
        else:
            return "Potion not found"

class CartCheckout(BaseModel):
    payment: str

# @router.post("/{cart_id}/checkout")
# def checkout(cart_id: int, cart_checkout: CartCheckout):
#     with db.engine.begin() as connection:
    #     # Select potion_id and quantity from cart_sales table for the given cart_id
    #     result = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM cart_sales WHERE cart_id = :cart_id"), {"cart_id": cart_id})
        
    #     total_potions_bought = 0
    #     total_gold_earned = 0

        
    #     for potion_id, quantity in result:
    #         # Select the current quantity from the potion_inventory table for the potion_id
    #         result = connection.execute(sqlalchemy.text("SELECT COALESCE(quantity, 0) FROM potion_inventory WHERE id = :potion_id"), {"potion_id": potion_id})
    #         current_quantity = result.scalar()

    #         # Calculate the new quantity by subtracting the purchased quantity from the current quantity
    #         new_quantity = current_quantity - quantity

    #         # Update the quantity in the potion_inventory table
    #         connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = :new_quantity WHERE id = :potion_id"),
    #                            {"new_quantity": new_quantity, "potion_id": potion_id})

    #         total_potions_bought += quantity
    #         total_gold_earned += quantity * gold

    #     # Get the current total_gold from the global_inventory table
    #     result = connection.execute(sqlalchemy.text("SELECT total_gold FROM global_inventory"))
    #     current_total_gold = result.scalar() or 0

    #     # Update the total_gold in the global_inventory table
    #     new_total_gold = current_total_gold + total_gold_earned
    #     connection.execute(sqlalchemy.text("UPDATE global_inventory SET total_gold = :new_total_gold"),
    #                        {"new_total_gold": new_total_gold})

    # return {"total_potions_bought": total_potions_bought, "total_gold": new_total_gold}


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        potions_in_cart = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM cart_sales WHERE cart_id = :cart_id "), {"cart_id": cart_id})

        total_gold = 0
        total_potions_bought = 0

        for potion_id, quantity in potions_in_cart:

            price = connection.execute(sqlalchemy.text("SELECT price FROM potion_inventory WHERE id = :potion_id"), {"potion_id": potion_id}).scalar_one()

            connection.execute(sqlalchemy.text("UPDATE potion_inventory SET quantity = quantity - :num_bought WHERE id = :potion_id"), {"num_bought": quantity, "potion_id": potion_id})
            total_gold += price * quantity
            total_potions_bought += quantity
       

        connection.execute(sqlalchemy.text(" UPDATE global_inventory SET gold = gold + :total_gold "), {"total_gold": total_gold})

    return {"total_gold": total_gold, "total_potions_bought": total_potions_bought}



# results =[{"potion_id"}], "qunatity"},]
# total gold = 0
# total potions = 0
# for each loop on results:
#     Query price
# Update potion qunatity in global_inventory
# "update potion_inventory set quantity = quantity - :num bought" {"num_bought:}"}
# update total gold 
# total gold+= price
# update total_potions_boughttotalpotions += set_item_quantityupdate gold in invenotory :"update
# return total gold 
# return totoal potions"