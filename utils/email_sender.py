"""
Wysyłanie e-maili przez Gmail SMTP.

KONFIGURACJA w .streamlit/secrets.toml:
[email]
sender_email    = "twoja.cukiernia@gmail.com"
sender_password = "haslo-aplikacji-gmail"   # App Password z Google Account
bakery_email    = "zamowienia@cukiernia.pl"  # dokąd idą kopie

Jak wygenerować App Password w Gmail:
1. Wejdź na myaccount.google.com → Bezpieczeństwo
2. Włącz weryfikację dwuetapową
3. Szukaj „Hasła aplikacji" → utwórz nowe dla „Poczta"
4. Wklej wygenerowane hasło jako sender_password
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st


# ─── HTML Templates ──────────────────────────────────────────────────────────

def _client_email_html(order: dict, products: dict) -> str:
    cart = order.get("cart", {})
    rows = ""
    total = 0
    for product_name, qty in cart.items():
        for cat_data in products.values():
            if product_name in cat_data["items"]:
                price = cat_data["items"][product_name]["price"]
                unit = cat_data["items"][product_name]["unit"]
                subtotal = price * qty
                total += subtotal
                rows += f"""
                <tr>
                    <td style="padding:10px 12px; border-bottom:1px solid #f0e6e6;">{product_name}</td>
                    <td style="padding:10px 12px; border-bottom:1px solid #f0e6e6; text-align:center;">{qty} {unit}</td>
                    <td style="padding:10px 12px; border-bottom:1px solid #f0e6e6; text-align:right;">{price} zł</td>
                    <td style="padding:10px 12px; border-bottom:1px solid #f0e6e6; text-align:right; font-weight:600;">{subtotal} zł</td>
                </tr>
                """

    return f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0; padding:0; background:#fdf6f0; font-family:'Georgia', serif;">
    <div style="max-width:620px; margin:40px auto; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">

        <!-- Header -->
        <div style="background:linear-gradient(135deg, #8B2252 0%, #C4547A 100%); padding:40px 40px 32px; text-align:center;">
            <p style="color:rgba(255,255,255,0.7); font-size:13px; letter-spacing:3px; margin:0 0 8px;">✦ NAZWA TWOJEJ CUKIERNI ✦</p>
            <h1 style="color:#fff; margin:0; font-size:28px; font-weight:400; letter-spacing:1px;">Potwierdzenie Zamówienia</h1>
            <p style="color:rgba(255,255,255,0.85); margin:12px 0 0; font-size:15px;">Nr: <strong>{order.get('order_id')}</strong></p>
        </div>

        <!-- Body -->
        <div style="padding:40px;">
            <p style="color:#5a3a3a; font-size:16px; line-height:1.7;">
                Droga <strong>{order.get('client_name', '')}</strong>,<br><br>
                Dziękujemy za złożenie zamówienia! 🌸 Nasz cukiernik zapozna się z Twoim wyborem 
                i skontaktuje się w ciągu <strong>24 godzin</strong>, aby potwierdzić szczegóły i ustalić ostateczną cenę.
            </p>

            <!-- Event details -->
            <div style="background:#fdf0f4; border-radius:12px; padding:20px 24px; margin:24px 0;">
                <h3 style="color:#8B2252; margin:0 0 12px; font-size:16px;">📅 Szczegóły wydarzenia</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <tr><td style="color:#777; padding:4px 0; width:140px;">Data:</td><td style="color:#333; font-weight:600;">{order.get('event_date')}</td></tr>
                    <tr><td style="color:#777; padding:4px 0;">Rodzaj:</td><td style="color:#333; font-weight:600;">{order.get('event_type')}</td></tr>
                    <tr><td style="color:#777; padding:4px 0;">Liczba gości:</td><td style="color:#333; font-weight:600;">{order.get('guest_count')}</td></tr>
                    {f'<tr><td style="color:#777; padding:4px 0;">Motyw:</td><td style="color:#333; font-weight:600;">{order.get("theme")}</td></tr>' if order.get('theme') else ''}
                </table>
            </div>

            <!-- Products table -->
            <h3 style="color:#8B2252; font-size:16px; margin:28px 0 12px;">🍰 Wybrane produkty</h3>
            <table style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr style="background:#8B2252;">
                        <th style="padding:10px 12px; text-align:left; color:#fff; font-weight:600; font-size:13px; border-radius:8px 0 0 0;">Produkt</th>
                        <th style="padding:10px 12px; text-align:center; color:#fff; font-weight:600; font-size:13px;">Ilość</th>
                        <th style="padding:10px 12px; text-align:right; color:#fff; font-weight:600; font-size:13px;">Cena jedn.</th>
                        <th style="padding:10px 12px; text-align:right; color:#fff; font-weight:600; font-size:13px; border-radius:0 8px 0 0;">Wartość</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
                <tfoot>
                    <tr style="background:#fdf0f4;">
                        <td colspan="3" style="padding:14px 12px; font-size:15px; color:#5a3a3a;"><strong>Szacunkowa wycena razem:</strong></td>
                        <td style="padding:14px 12px; text-align:right; font-size:18px; color:#8B2252; font-weight:700;">{total} zł</td>
                    </tr>
                </tfoot>
            </table>
            <p style="color:#aaa; font-size:12px; margin-top:8px;">⚠️ Cena jest orientacyjna i zostanie potwierdzona przez cukiernię.</p>

            <!-- Notes -->
            {f'<div style="background:#fffbf0; border-left:3px solid #f0c040; padding:14px 18px; border-radius:0 8px 8px 0; margin:24px 0;"><p style="margin:0; color:#7a5a00; font-size:14px;">📝 Uwagi: {order.get("notes")}</p></div>' if order.get('notes') else ''}

            <p style="color:#5a3a3a; font-size:15px; line-height:1.7; margin-top:28px;">
                W razie pytań zadzwoń lub napisz:<br>
                📞 <strong>+48 XXX XXX XXX</strong><br>
                ✉️ <strong>kontakt@twoja-cukiernia.pl</strong>
            </p>
        </div>

        <!-- Footer -->
        <div style="background:#2d1a1a; padding:24px 40px; text-align:center;">
            <p style="color:rgba(255,255,255,0.5); font-size:12px; margin:0;">✦ NAZWA TWOJEJ CUKIERNI · ul. Twoja Ulica 1 · Twoje Miasto ✦</p>
        </div>
    </div>
    </body>
    </html>
    """


def _bakery_email_html(order: dict, products: dict) -> str:
    cart = order.get("cart", {})
    rows = ""
    for product_name, qty in cart.items():
        for cat_name, cat_data in products.items():
            if product_name in cat_data["items"]:
                price = cat_data["items"][product_name]["price"]
                unit = cat_data["items"][product_name]["unit"]
                rows += f"<tr><td style='padding:8px;border-bottom:1px solid #eee;'>{product_name}</td><td style='padding:8px;border-bottom:1px solid #eee;text-align:center;'>{qty} {unit}</td><td style='padding:8px;border-bottom:1px solid #eee;text-align:right;'>{qty*price} zł</td></tr>"

    return f"""
    <html><body style="font-family:sans-serif; color:#333; padding:20px;">
    <h2 style="color:#8B2252;">🎂 Nowe zamówienie — {order.get('order_id')}</h2>
    <p><strong>Złożone:</strong> {order.get('submitted_at')}</p>
    <hr>
    <h3>Klient</h3>
    <p>👤 {order.get('client_name')}<br>
    ✉️ {order.get('client_email')}<br>
    📞 {order.get('client_phone')}</p>
    <h3>Wydarzenie</h3>
    <p>📅 {order.get('event_date')} · {order.get('event_type')} · {order.get('guest_count')} gości<br>
    🎨 Motyw: {order.get('theme') or '—'}<br>
    💰 Budżet: {order.get('budget')}</p>
    {f"<p>📝 Uwagi: {order.get('notes')}</p>" if order.get('notes') else ''}
    <h3>Zamówione produkty</h3>
    <table style="width:100%;border-collapse:collapse;">
    <thead><tr style="background:#8B2252;color:white;"><th style="padding:8px;text-align:left;">Produkt</th><th style="padding:8px;">Ilość</th><th style="padding:8px;text-align:right;">Wartość</th></tr></thead>
    <tbody>{rows}</tbody>
    </table>
    <p style="font-size:18px; margin-top:16px;"><strong>Łączna wycena: {order.get('total', 0):.0f} zł</strong></p>
    </body></html>
    """


# ─── Send emails ─────────────────────────────────────────────────────────────

def send_order_emails(order: dict, products: dict) -> bool:
    """Wysyła e-mail do klienta i do cukierni. Zwraca True jeśli sukces."""
    try:
        sender = st.secrets["email"]["sender_email"]
        password = st.secrets["email"]["sender_password"]
        bakery_email = st.secrets["email"]["bakery_email"]
    except KeyError as e:
        st.warning(f"⚠️ Brakuje konfiguracji e-mail w Secrets: {e}. E-maile nie zostały wysłane.")
        return False

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, password)

            # ── E-mail do klienta ──────────────────────────────────────────
            msg_client = MIMEMultipart("alternative")
            msg_client["Subject"] = f"✨ Potwierdzenie zamówienia słodkiego stołu | {order.get('order_id')}"
            msg_client["From"] = f"Cukiernia Artystyczna <{sender}>"
            msg_client["To"] = order.get("client_email", "")
            msg_client.attach(MIMEText(_client_email_html(order, products), "html"))
            server.sendmail(sender, order.get("client_email", ""), msg_client.as_string())

            # ── E-mail do cukierni ─────────────────────────────────────────
            msg_bakery = MIMEMultipart("alternative")
            msg_bakery["Subject"] = f"🎂 NOWE ZAMÓWIENIE | {order.get('order_id')} | {order.get('event_date')} | {order.get('client_name')}"
            msg_bakery["From"] = f"Konfigurator Słodkich Stołów <{sender}>"
            msg_bakery["To"] = bakery_email
            msg_bakery.attach(MIMEText(_bakery_email_html(order, products), "html"))
            server.sendmail(sender, bakery_email, msg_bakery.as_string())

        return True

    except smtplib.SMTPAuthenticationError:
        st.error("❌ Błąd logowania do Gmail. Sprawdź dane w secrets.toml (czy używasz App Password?).")
        return False
    except Exception as e:
        st.error(f"❌ Błąd wysyłania e-mail: {e}")
        return False
