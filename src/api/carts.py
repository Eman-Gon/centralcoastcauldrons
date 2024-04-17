import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

#global counter cart id that keeps track cart id
#create it here
#create list and access it by index same as cart id or one less

#increaments carts in create_cart
#instead hard values return the varable and return after it creates it, ex. if some has a cart it should create, cart1,cart,2. etc

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
    """ """

    return {"cart_id": 1}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Checkout the cart and update the inventory and gold based on the purchased potions.
    """
    with db.engine.begin() as connection:
        # Placeholder for getting the cart items for the given cart_id
        # Replace this with your actual implementation to retrieve the cart items from the database
        cart_items = [
            {"sku": "GREEN_POTION", "quantity": 0},#put stament in here
            {"sku": "RED_POTION", "quantity": 0},
            {"sku": "BLUE_POTION", "quantity": 0},
        ]

        total_potions_bought = 0
        total_gold_paid = 0

        for item in cart_items:
            if item["sku"] == "GREEN_POTION":
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions - {item['quantity']}"))
                total_gold_paid += 50 * item["quantity"]
            elif item["sku"] == "RED_POTION":
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions - {item['quantity']}"))
                total_gold_paid += 50 * item["quantity"]
            elif item["sku"] == "BLUE_POTION":
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions - {item['quantity']}"))
                total_gold_paid += 50 * item["quantity"]

            total_potions_bought += item["quantity"]

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_gold_paid}"))

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}