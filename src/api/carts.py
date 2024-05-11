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

    # Build the base query
    query = """
        SELECT
            cart_sales.cart_id,
            cart_sales.potion_id,
            potion_inventory.sku AS item_sku,
            carts.customer AS customer_name,
            CAST(potion_inventory.price * cart_sales.quantity AS INTEGER) AS line_item_total,
            cart_sales.created_at AS timestamp
        FROM
            cart_sales
            JOIN potion_inventory ON cart_sales.potion_id = potion_inventory.id
            JOIN carts ON cart_sales.cart_id = carts.id
    """

    params = {}

    # Apply filters
    if sort_col is search_sort_options.customer_name:
        order_by = sqlalchemy.text("carts.customer")
    elif sort_col is search_sort_options.item_sku:
        order_by = sqlalchemy.text("potion_inventory.sku")
    elif sort_col is search_sort_options.line_item_total:
        order_by = sqlalchemy.text("CAST(potion_inventory.price * cart_sales.quantity AS INTEGER)")
    elif sort_col is search_sort_options.timestamp:
        order_by = sqlalchemy.text("cart_sales.created_at")
    else:
        assert False

    if sort_order is search_sort_order.desc:
        order_by = sqlalchemy.desc(order_by)

    limit = 5
    offset = 0
    if search_page:
        offset = int(search_page)

    stmt = (
        sqlalchemy.select(
            sqlalchemy.text("cart_sales.cart_id"),
            sqlalchemy.text("cart_sales.potion_id"),
            sqlalchemy.text("potion_inventory.sku AS item_sku"),
            sqlalchemy.text("carts.customer AS customer_name"),
            sqlalchemy.text("CAST(potion_inventory.price * cart_sales.quantity AS INTEGER) AS line_item_total"),
            sqlalchemy.text("cart_sales.created_at AS timestamp")
        )
        .select_from(sqlalchemy.text("cart_sales"))
        .join(sqlalchemy.text("potion_inventory"), sqlalchemy.text("cart_sales.potion_id = potion_inventory.id"))
        .join(sqlalchemy.text("carts"), sqlalchemy.text("cart_sales.cart_id = carts.id"))
        .limit(limit)
        .offset(offset)
        .order_by(order_by)
    )

    if customer_name:
        stmt = stmt.where(sqlalchemy.text("carts.customer ILIKE :customer_name")).params(customer_name=f"%{customer_name}%")

    if potion_sku:
        stmt = stmt.where(sqlalchemy.text("potion_inventory.sku ILIKE :potion_sku")).params(potion_sku=f"%{potion_sku}%")

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        line_items = result.fetchall()

    # Prepare the response
    previous_page = offset - limit if offset > 0 else None
    next_page = offset + limit if len(line_items) == limit else None

    return {
        "previous": str(previous_page) if previous_page is not None else "",
        "next": str(next_page) if next_page is not None else "",
        "results": [
            {
                "line_item_id": f"{row.cart_id}-{row.potion_id}",
                "item_sku": row.item_sku,
                "customer_name": row.customer_name,
                "line_item_total": row.line_item_total,
                "timestamp": row.timestamp.isoformat(),
            }
            for row in line_items
        ]
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

    
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        # Add a new transaction
        result = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) VALUES (:description) RETURNING id"), {"description": f"Checkout for cart {cart_id}"})
        transaction_id = result.scalar_one()

        potions_in_cart = connection.execute(sqlalchemy.text("SELECT potion_id, quantity FROM cart_sales WHERE cart_id = :cart_id "), {"cart_id": cart_id})

        total_gold_paid = 0
        total_potions_bought = 0

        for potion_id, quantity in potions_in_cart:
            price = connection.execute(sqlalchemy.text("SELECT price FROM potion_inventory WHERE id = :potion_id"), {"potion_id": potion_id}).scalar_one()

            # Record changes in the ledger tables
            connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (transaction_id, potion_id, change_in_potion) VALUES (:transaction_id, :potion_id, :change_in_potion)"), {"transaction_id": transaction_id, "potion_id": potion_id, "change_in_potion": -quantity})
            connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (transaction_id, change_in_gold) VALUES (:transaction_id, :change_in_gold)"), {"transaction_id": transaction_id, "change_in_gold": price * quantity})

            total_gold_paid += price * quantity
            total_potions_bought += quantity

    return {"total_gold_paid": total_gold_paid, "total_potions_bought": total_potions_bought}