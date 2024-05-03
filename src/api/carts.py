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
    # ...

    with db.engine.connect() as conn:
        # Build the base query
        query = sqlalchemy.select(
            db.cart_sales.c.id.label("line_item_id"),
            db.potion_inventory.c.sku.label("item_sku"),
            db.carts.c.customer.label("customer_name"),
            (db.cart_sales.c.quantity * db.potion_inventory.c.price).label("line_item_total"),
            db.cart_sales.c.created_at.label("timestamp"),
        ).select_from(
            db.cart_sales.join(db.potion_inventory, db.cart_sales.c.potion_id == db.potion_inventory.c.id)
            .join(db.carts, db.cart_sales.c.cart_id == db.carts.c.id)
        )

        # Apply filters
        if customer_name:
            query = query.where(db.carts.c.customer.ilike(f"%{customer_name}%"))
        if potion_sku:
            query = query.where(db.potion_inventory.c.sku.ilike(f"%{potion_sku}%"))

        # Apply sorting
        if sort_col == search_sort_options.customer_name:
            order_by_column = db.carts.c.customer
        elif sort_col == search_sort_options.item_sku:
            order_by_column = db.potion_inventory.c.sku
        elif sort_col == search_sort_options.line_item_total:
            order_by_column = (db.cart_sales.c.quantity * db.potion_inventory.c.price)
        else:  # Default to timestamp
            order_by_column = db.cart_sales.c.created_at

        if sort_order == search_sort_order.asc:
            query = query.order_by(order_by_column)
        else:  # Default to descending order
            query = query.order_by(order_by_column.desc())

        # Pagination
        if search_page:
            offset = int(search_page) * 5
        else:
            offset = 0

        query = query.limit(5).offset(offset)

        # Execute the query
        result = conn.execute(query)

        # Process the results
        results = []
        for row in result:
            results.append({
                "line_item_id": row.line_item_id,
                "item_sku": row.item_sku,
                "customer_name": row.customer_name,
                "line_item_total": row.line_item_total,
                "timestamp": row.timestamp.isoformat(),
            })

        # Determine previous and next page tokens
        previous_page = offset // 5 - 1 if offset > 0 else None
        next_page = offset // 5 + 1 if len(results) == 5 else None

    return {
        "previous": str(previous_page) if previous_page is not None else "",
        "next": str(next_page) if next_page is not None else "",
        "results": results,
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
