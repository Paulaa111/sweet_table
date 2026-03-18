import random
import string
from datetime import datetime


def generate_order_id() -> str:
    """Generuje unikalny numer zamówienia np. SS-20251217-A3X9"""
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SS-{date_part}-{random_part}"


def calculate_total(cart: dict, products: dict) -> float:
    """Oblicza sumę zamówienia na podstawie koszyka i katalogu."""
    total = 0.0
    for product_name, qty in cart.items():
        for cat_data in products.values():
            if product_name in cat_data["items"]:
                total += cat_data["items"][product_name]["price"] * qty
                break
    return total


def format_order_summary(order: dict, products: dict) -> str:
    """Formatuje zamówienie do czytelnego tekstu (np. do logów)."""
    lines = [
        f"=== ZAMÓWIENIE {order.get('order_id', '')} ===",
        f"Klient: {order.get('client_name')} | {order.get('client_email')} | {order.get('client_phone')}",
        f"Wydarzenie: {order.get('event_type')} · {order.get('event_date')} · {order.get('guest_count')} gości",
        "",
        "Produkty:",
    ]
    for product, qty in order.get("cart", {}).items():
        for cat_data in products.values():
            if product in cat_data["items"]:
                price = cat_data["items"][product]["price"]
                lines.append(f"  - {product}: {qty} × {price} zł = {qty * price} zł")
    lines.append(f"\nŁączna wycena: {order.get('total', 0):.0f} zł")
    return "\n".join(lines)
