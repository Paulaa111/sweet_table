"""
Google Sheets integration via gspread + service account.

KONFIGURACJA:
1. Wejdź na https://console.cloud.google.com
2. Utwórz nowy projekt → włącz Google Sheets API i Google Drive API
3. Utwórz Service Account (IAM & Admin → Service Accounts)
4. Pobierz klucz JSON i wgraj do Streamlit Secrets jako [gcp_service_account]
5. Utwórz arkusz Google i udostępnij go na e-mail service account (rola: Editor)
6. Wklej ID arkusza do Streamlit Secrets jako GOOGLE_SHEET_ID
"""

import streamlit as st
import json
from datetime import datetime


def save_order_to_sheets(order: dict, products: dict) -> bool:
    """
    Zapisuje zamówienie do Google Sheets.
    Zwraca True jeśli sukces, False jeśli błąd.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Pobierz credentials z Streamlit Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        sheet_id = st.secrets["GOOGLE_SHEET_ID"]

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_key(sheet_id)

        # ── Arkusz 1: Zamówienia (główny) ──────────────────────────────────
        try:
            ws_orders = spreadsheet.worksheet("Zamówienia")
        except gspread.WorksheetNotFound:
            ws_orders = spreadsheet.add_worksheet("Zamówienia", rows=1000, cols=20)
            # Nagłówki
            ws_orders.append_row([
                "Nr zamówienia", "Data złożenia", "Data wydarzenia",
                "Rodzaj wydarzenia", "Liczba gości", "Motyw",
                "Budżet", "Imię i nazwisko", "E-mail", "Telefon",
                "Łączna wycena (zł)", "Uwagi", "Status"
            ])
            # Formatowanie nagłówka (pogrubienie)
            ws_orders.format("A1:M1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.98, "green": 0.93, "blue": 0.93}
            })

        ws_orders.append_row([
            order.get("order_id", ""),
            order.get("submitted_at", ""),
            order.get("event_date", ""),
            order.get("event_type", ""),
            order.get("guest_count", ""),
            order.get("theme", ""),
            order.get("budget", ""),
            order.get("client_name", ""),
            order.get("client_email", ""),
            order.get("client_phone", ""),
            order.get("total", 0),
            order.get("notes", ""),
            "Nowe",
        ])

        # ── Arkusz 2: Szczegóły zamówień ──────────────────────────────────
        try:
            ws_items = spreadsheet.worksheet("Produkty")
        except gspread.WorksheetNotFound:
            ws_items = spreadsheet.add_worksheet("Produkty", rows=5000, cols=8)
            ws_items.append_row([
                "Nr zamówienia", "Data wydarzenia", "Klient",
                "Produkt", "Kategoria", "Ilość", "Cena jedn. (zł)", "Wartość (zł)"
            ])
            ws_items.format("A1:H1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.93, "green": 0.96, "blue": 0.98}
            })

        cart = order.get("cart", {})
        for product_name, qty in cart.items():
            category = ""
            price = 0
            unit = ""
            for cat_name, cat_data in products.items():
                if product_name in cat_data["items"]:
                    category = cat_name
                    price = cat_data["items"][product_name]["price"]
                    unit = cat_data["items"][product_name]["unit"]
                    break

            ws_items.append_row([
                order.get("order_id", ""),
                order.get("event_date", ""),
                order.get("client_name", ""),
                product_name,
                category,
                qty,
                price,
                qty * price,
            ])

        return True

    except ImportError:
        st.warning("⚠️ Biblioteka gspread nie jest zainstalowana. Zamówienie nie zostało zapisane do arkusza.")
        return False
    except KeyError as e:
        st.warning(f"⚠️ Brakuje konfiguracji w Secrets: {e}. Sprawdź plik .streamlit/secrets.toml")
        return False
    except Exception as e:
        st.error(f"Błąd Google Sheets: {e}")
        return False
