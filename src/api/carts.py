# import sqlalchemy
# from src import database as db
# from fastapi import APIRouter, Depends, Request
# from pydantic import BaseModel
# from src.api import auth
# from enum import Enum

# router = APIRouter(
#     prefix="/carts",
#     tags=["cart"],
#     dependencies=[Depends(auth.get_api_key)],
# )
# customer_orders = {}

# class search_sort_options(str, Enum):
#     customer_name = "customer_name"
#     item_sku = "item_sku"
#     line_item_total = "line_item_total"
#     timestamp = "timestamp"

# class search_sort_order(str, Enum):
#     asc = "asc"
#     desc = "desc"   

# @router.get("/search/", tags=["search"])
# def search_orders(
#     customer_name: str = "",
#     potion_sku: str = "",
#     search_page: str = "",
#     sort_col: search_sort_options = search_sort_options.timestamp,
#     sort_order: search_sort_order = search_sort_order.desc,
# ):
#     """
#     Search for cart line items by customer name and/or potion sku.

#     Customer name and potion sku filter to orders that contain the 
#     string (case insensitive). If the filters aren't provided, no
#     filtering occurs on the respective search term.

#     Search page is a cursor for pagination. The response to this
#     search endpoint will return previous or next if there is a
#     previous or next page of results available. The token passed
#     in that search response can be passed in the next search request
#     as search page to get that page of results.

#     Sort col is which column to sort by and sort order is the direction
#     of the search. They default to searching by timestamp of the order
#     in descending order.

#     The response itself contains a previous and next page token (if
#     such pages exist) and the results as an array of line items. Each
#     line item contains the line item id (must be unique), item sku, 
#     customer name, line item total (in gold), and timestamp of the order.
#     Your results must be paginated, the max results you can return at any
#     time is 5 total line items.
#     """

#     return {
#         "previous": "",
#         "next": "",
#         "results": [
#             {
#                 "line_item_id": 1,
#                 "item_sku": "1 oblivion potion",
#                 "customer_name": "Scaramouche",
#                 "line_item_total": 50,
#                 "timestamp": "2021-01-01T00:00:00Z",
#             }
#         ],
#     }


# class Customer(BaseModel):
#     customer_name: str
#     character_class: str
#     level: int

# @router.post("/visits/{visit_id}")
# def post_visits(visit_id: int, customers: list[Customer]):
#     """
#     Which customers visited the shop today?
#     """
#     print(customers)

#     return "OK"


# @router.post("/")
# def create_cart(new_cart: Customer):
#     """ """
#     return {"cart_id": 1}


# class CartItem(BaseModel):
#     quantity: int


# @router.post("/{cart_id}/items/{item_sku}")
# def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
#     with db.engine.begin() as connection:
#         connection.execute(sqlalchemy.text(
#             "INSERT INTO cart_items (cart_id, potion_type, quantity, price) VALUES (:cart_id, :potion_type, :quantity, :price)"
#         ), {"cart_id": cart_id, "potion_type": item_sku, "quantity": cart_item.quantity, "price": 50})

#     return "OK"


# class CartCheckout(BaseModel):
#     payment: str

# @router.post("/{cart_id}/checkout")
# def checkout(cart_id: int, cart_checkout: CartCheckout):
#     with db.engine.begin() as connection:
#         cart_items = connection.execute(sqlalchemy.text(
#             "SELECT potion_type, quantity, price FROM cart_items WHERE cart_id = :cart_id"
#         ), {"cart_id": cart_id}).fetchall()

#         total_potions_bought = 0
#         total_gold_paid = 0

#         for item in cart_items:
#             potion_type = item[0]
#             quantity = item[1]
#             price = item[2]

#             if potion_type == "GREEN":
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions - {quantity}"))
#             elif potion_type == "RED":
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions - {quantity}"))
#             elif potion_type == "BLUE":
#                 connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions - {quantity}"))

#             total_potions_bought += quantity
#             total_gold_paid += price * quantity

#         connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_gold_paid}"))

#     return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}

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
        sql = "INSERT INTO carts (customer_name, cart_name) VALUES (:customer_name, :cart_name) RETURNING id"
        result = connection.execute(sqlalchemy.text(sql), customer_name=new_cart.customer_name, cart_name=new_cart.cart_name)
        cart_id = result.scalar()
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    try:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT id FROM potion_inventory WHERE sku = :item_sku"), item_sku=item_sku)
            potion_id = result.scalar()

            if potion_id:
                connection.execute(sqlalchemy.text("INSERT INTO cart_sales (cart_id, potion_id, quantity) VALUES (:cart_id, :potion_id, :quantity) "
                                                   "ON CONFLICT (cart_id, potion_id) DO UPDATE SET quantity = :quantity"),cart_id=cart_id, potion_id=potion_id, quantity=cart_item.quantity)
                return "OK"
            else:
                return "Potion not found"
    except Exception as e:
        return str(e)


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    try:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM cart_sales WHERE cart_id = :cart_id"), cart_id=cart_id)

            total_potions_bought = 0
            total_gold_paid = 0

            for potion_id, quantity in result:
                result = connection.execute(sqlalchemy.text("SELECT price, quantity_column FROM potion_inventory WHERE id = :potion_id"), potion_id=potion_id)
                price, quantity_column = result.first()

                if price and quantity_column:
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {quantity_column} = {quantity_column} - :quantity"), quantity=quantity)
                    total_potions_bought += quantity
                    total_gold_paid += price * quantity

            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + :total_gold_paid"), total_gold_paid=total_gold_paid)
            connection.execute(sqlalchemy.text("DELETE FROM cart_sales WHERE cart_id = :cart_id"), cart_id=cart_id)

        return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
    except Exception as e:
        return {"error": str(e)}