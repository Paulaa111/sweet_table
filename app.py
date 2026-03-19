import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import os
from utils.google_sheets import save_order_to_sheets
from utils.email_sender import send_order_emails
from utils.order_utils import generate_order_id, calculate_total, format_order_summary

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Słodki Stół | Konfigurator",
    page_icon="🍰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Load CSS ────────────────────────────────────────────────────────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Session state init ──────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = 1
if "order" not in st.session_state:
    st.session_state.order = {}
if "cart" not in st.session_state:
    st.session_state.cart = {}

# ─── Product catalogue ───────────────────────────────────────────────────────
PRODUCTS = {
    "🧁 Cupcakes & Muffiny": {
        "icon": "🧁",
        "items": {
            "Cupcakes waniliowe": {"price": 8, "unit": "szt.", "min": 12, "desc": "Klasyczne cupcakes z kremem maślanym, dekorowane posypkami"},
            "Cupcakes czekoladowe": {"price": 9, "unit": "szt.", "min": 12, "desc": "Intensywnie czekoladowe z aksamitnym ganache"},
            "Cupcakes sezonowe": {"price": 10, "unit": "szt.", "min": 12, "desc": "Smak i dekoracja dopasowana do okazji i pory roku"},
            "Muffiny jagodowe": {"price": 7, "unit": "szt.", "min": 12, "desc": "Puszyste muffiny ze świeżymi jagodami i kruszonką"},
            "Muffiny cytrynowe": {"price": 7, "unit": "szt.", "min": 12, "desc": "Lekkie muffiny z kremem cytrynowym i skórką"},
        }
    },
    "🌈 Makaroniki": {
        "icon": "🌈",
        "items": {
            "Makaroniki mix smaków": {"price": 5, "unit": "szt.", "min": 24, "desc": "Klasyczne makaroniki paryskie – min. 6 smaków do wyboru"},
            "Makaroniki sezonowe": {"price": 6, "unit": "szt.", "min": 24, "desc": "Specjalne smaki dopasowane do sezonu i okazji"},
            "Makaroniki tematyczne": {"price": 7, "unit": "szt.", "min": 24, "desc": "Barwione w kolorystyce Twojego wydarzenia"},
        }
    },
    "🍪 Ciasteczka & Wypieki": {
        "icon": "🍪",
        "items": {
            "Ciasteczka kruche dekorowane": {"price": 4, "unit": "szt.", "min": 20, "desc": "Ręcznie dekorowane ciasteczka z kolorowym lukrem królewskim"},
            "Ciasteczka maślane": {"price": 3, "unit": "szt.", "min": 30, "desc": "Tradycyjne ciasteczka maślane w różnych kształtach"},
            "Brownie czekoladowe": {"price": 7, "unit": "szt.", "min": 12, "desc": "Wilgotne brownie z belgijską czekoladą i orzechami"},
            "Blondie waniliowe": {"price": 7, "unit": "szt.", "min": 12, "desc": "Jasne brownie z białą czekoladą i nugatem"},
            "Financiers migdałowe": {"price": 5, "unit": "szt.", "min": 20, "desc": "Delikatne francuskie ciasteczka migdałowe"},
        }
    },
    "🍫 Pralinki & Czekoladki": {
        "icon": "🍫",
        "items": {
            "Pralinki ręcznie robione": {"price": 6, "unit": "szt.", "min": 20, "desc": "Czekoladki belgijskie z różnorodnymi nadzieniami"},
            "Trufle czekoladowe": {"price": 5, "unit": "szt.", "min": 20, "desc": "Klasyczne trufle obtaczane w kakao, orzechach lub kokosie"},
            "Czekolada na patyku": {"price": 8, "unit": "szt.", "min": 10, "desc": "Dekoracyjne czekolady z posypkami — idealne do stołu"},
            "Mendianty czekoladowe": {"price": 5, "unit": "szt.", "min": 20, "desc": "Płaskie krążki czekolady z suszonymi owocami i orzechami"},
        }
    },
    "🍮 Mini Desery": {
        "icon": "🍮",
        "items": {
            "Panna cotta": {"price": 10, "unit": "szt.", "min": 10, "desc": "Kremowa panna cotta z sosem owocowym w szklanym kieliszku"},
            "Tartaletki owocowe": {"price": 9, "unit": "szt.", "min": 12, "desc": "Kruche tartaletki z kremem patissière i świeżymi owocami"},
            "Cheesecake w słoiku": {"price": 11, "unit": "szt.", "min": 10, "desc": "Sernik na zimno w dekoracyjnym słoiczku z owocem sezonowym"},
            "Bezy": {"price": 4, "unit": "szt.", "min": 20, "desc": "Chrupiące bezy w kolorach dopasowanych do dekoracji"},
            "Éclair": {"price": 8, "unit": "szt.", "min": 12, "desc": "Klasyczne eklery z kremem waniliowym i polewą czekoladową"},
            "Mus czekoladowy w kieliszku": {"price": 9, "unit": "szt.", "min": 10, "desc": "Aksamitny mus z ciemnej czekolady z bitą śmietaną"},
        }
    },
    "🍬 Candy Bar": {
        "icon": "🍬",
        "items": {
            "Żelki i pianki (taca)": {"price": 45, "unit": "taca", "min": 1, "desc": "Dekoracyjna taca kolorowych słodyczy sypanych"},
            "Lizaki dekoracyjne": {"price": 3, "unit": "szt.", "min": 20, "desc": "Lizaki na patyku — świetna dekoracja stołu"},
            "Cukierki w słoiczkach": {"price": 25, "unit": "słoik", "min": 3, "desc": "Dekoracyjne słoiki z kolorowymi cukierkami do wyboru"},
            "Drażetki czekoladowe (miska)": {"price": 35, "unit": "miska", "min": 1, "desc": "Kolorowe drażetki M&M lub Smarties — efekt wow"},
            "Toffi i krówki (taca)": {"price": 40, "unit": "taca", "min": 1, "desc": "Domowe krówki i toffi w papilotach — klimatyczna taca"},
        }
    },
}

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">✦ Twoja Cukiernia ✦</div>
    <h1 class="hero-title">Słodki Stół</h1>
    <p class="hero-subtitle">Skomponuj wyjątkowy stół słodkości na Twoje wydarzenie</p>
</div>
""", unsafe_allow_html=True)

# ─── Progress bar ────────────────────────────────────────────────────────────
steps = ["Wydarzenie", "Słodkości", "Podsumowanie", "Zamówienie"]
progress_html = '<div class="progress-bar">'
for i, s in enumerate(steps, 1):
    active = "active" if i == st.session_state.step else ""
    done = "done" if i < st.session_state.step else ""
    progress_html += f'<div class="progress-step {active} {done}"><span class="step-num">{i}</span><span class="step-label">{s}</span></div>'
    if i < len(steps):
        progress_html += f'<div class="progress-line {done}"></div>'
progress_html += '</div>'
st.markdown(progress_html, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════
# STEP 1 – Szczegóły wydarzenia
# ══════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown('<h2 class="section-title">📅 Twoje Wydarzenie</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Kiedy i gdzie?")
        event_date = st.date_input(
            "Data wydarzenia",
            min_value=date.today() + timedelta(days=7),
            value=date.today() + timedelta(days=30),
            help="Zamówienie przyjmujemy min. 7 dni przed wydarzeniem"
        )
        event_type = st.selectbox(
            "Rodzaj wydarzenia",
            ["Wesele 💍", "Urodziny 🎂", "Chrzest 👶", "Komunia ✝️", "Rocznica 💕", "Eventy firmowe 🏢", "Inne 🎊"]
        )
        guest_count = st.number_input(
            "Liczba gości",
            min_value=10, max_value=500, value=50, step=5,
            help="Pomożemy dobrać ilości do liczby gości"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Twoje oczekiwania")
        theme = st.text_input("Motyw / kolorystyka (opcjonalne)", placeholder="np. boho, rustykalny, różowo-złoty...")
        budget = st.selectbox(
            "Orientacyjny budżet",
            ["do 500 zł", "500–1000 zł", "1000–2000 zł", "2000–3500 zł", "powyżej 3500 zł"]
        )
        notes = st.text_area(
            "Dodatkowe informacje",
            placeholder="Alergie, specjalne życzenia, inspiracje...",
            height=100
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("Dalej →", key="step1_next", use_container_width=True):
            st.session_state.order.update({
                "event_date": str(event_date),
                "event_type": event_type,
                "guest_count": guest_count,
                "theme": theme,
                "budget": budget,
                "notes": notes,
            })
            st.session_state.step = 2
            st.rerun()

# ══════════════════════════════════════════════════════════
# STEP 2 – Wybór słodkości
# ══════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown('<h2 class="section-title">🍰 Wybierz Słodkości</h2>', unsafe_allow_html=True)
    
    guests = st.session_state.order.get("guest_count", 50)
    st.markdown(f'<p class="info-note">💡 Kalkulacja dla <strong>{guests} gości</strong> — możesz dowolnie modyfikować ilości.</p>', unsafe_allow_html=True)

    for category, data in PRODUCTS.items():
        with st.expander(f"{category}", expanded=False):
            for product_name, product_data in data["items"].items():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{product_name}**")
                    st.caption(product_data["desc"])
                with col2:
                    st.markdown(f"**{product_data['price']} zł** / {product_data['unit']}")
                    st.caption(f"min. {product_data['min']} {product_data['unit']}")
                with col3:
                    key = f"qty_{product_name}"
                    current = st.session_state.cart.get(product_name, 0)
                    qty = st.number_input(
                        "Ilość",
                        min_value=0,
                        value=current,
                        step=product_data['min'] if product_data['min'] > 1 else 1,
                        key=key,
                        label_visibility="collapsed"
                    )
                    if qty > 0:
                        st.session_state.cart[product_name] = qty
                    elif product_name in st.session_state.cart:
                        del st.session_state.cart[product_name]

    # Floating cart summary
    if st.session_state.cart:
        total = calculate_total(st.session_state.cart, PRODUCTS)
        items_count = sum(st.session_state.cart.values())
        st.markdown(f"""
        <div class="cart-summary">
            🛒 <strong>{len(st.session_state.cart)} produktów</strong> · {items_count} szt. łącznie · 
            <strong>{total:.0f} zł</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Wstecz", key="step2_back"):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("Podsumowanie →", key="step2_next", use_container_width=True):
            if not st.session_state.cart:
                st.error("Dodaj przynajmniej jeden produkt do koszyka!")
            else:
                st.session_state.step = 3
                st.rerun()

# ══════════════════════════════════════════════════════════
# STEP 3 – Podsumowanie zamówienia
# ══════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown('<h2 class="section-title">📋 Podsumowanie</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🗓️ Szczegóły wydarzenia")
        order = st.session_state.order
        st.markdown(f"""
        | | |
        |---|---|
        | **Data** | {order.get('event_date', '–')} |
        | **Rodzaj** | {order.get('event_type', '–')} |
        | **Goście** | {order.get('guest_count', '–')} |
        | **Motyw** | {order.get('theme', 'brak') or 'brak'} |
        | **Budżet** | {order.get('budget', '–')} |
        """)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🍰 Wybrane produkty")
        total = 0
        for product, qty in st.session_state.cart.items():
            for cat_data in PRODUCTS.values():
                if product in cat_data["items"]:
                    price = cat_data["items"][product]["price"]
                    unit = cat_data["items"][product]["unit"]
                    subtotal = price * qty
                    total += subtotal
                    st.markdown(f"- **{product}** – {qty} {unit} × {price} zł = **{subtotal} zł**")
        st.markdown(f"<hr><h4>Łączna szacunkowa wycena: {total:.0f} zł</h4>", unsafe_allow_html=True)
        st.markdown('<small>⚠️ Ostateczna cena zostanie potwierdzona przez cukiernię po kontakcie.</small>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📬 Twoje dane kontaktowe")
        client_name = st.text_input("Imię i nazwisko *", placeholder="Anna Kowalska")
        client_email = st.text_input("E-mail *", placeholder="anna@przykład.pl")
        client_phone = st.text_input("Telefon *", placeholder="+48 600 000 000")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card rodo-card">', unsafe_allow_html=True)
        rodo = st.checkbox(
            "Wyrażam zgodę na przetwarzanie moich danych osobowych w celu realizacji zamówienia. *",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Wstecz", key="step3_back"):
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("✨ Wyślij Zamówienie", key="step3_submit", use_container_width=True):
            if not client_name or not client_email or not client_phone:
                st.error("Wypełnij wszystkie wymagane pola (*)")
            elif not rodo:
                st.error("Zaakceptuj zgodę na przetwarzanie danych")
            elif "@" not in client_email:
                st.error("Podaj prawidłowy adres e-mail")
            else:
                # Save client data
                st.session_state.order.update({
                    "client_name": client_name,
                    "client_email": client_email,
                    "client_phone": client_phone,
                    "order_id": generate_order_id(),
                    "total": calculate_total(st.session_state.cart, PRODUCTS),
                    "cart": dict(st.session_state.cart),
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

                with st.spinner("Wysyłamy Twoje zamówienie..."):
                    sheets_ok = save_order_to_sheets(st.session_state.order, PRODUCTS)
                    emails_ok = send_order_emails(st.session_state.order, PRODUCTS)
                
                st.write("Sheets:", sheets_ok)
                st.write("Email:", emails_ok)
                
                if sheets_ok and emails_ok:
                    st.session_state.step = 4
                    st.rerun()
                elif emails_ok:
                    st.warning("⚠️ E-maile wysłane, ale arkusz się nie zapisał. Sprawdź konfigurację Google Sheets.")
                elif sheets_ok:
                    st.warning("⚠️ Arkusz zapisany, ale e-maile nie zostały wysłane.")
                else:
                    st.error("Wystąpił błąd. Sprawdź logi.")

# ══════════════════════════════════════════════════════════
# STEP 4 – Potwierdzenie
# ══════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    order = st.session_state.order
    st.markdown(f"""
    <div class="success-screen">
        <div class="success-icon">🎉</div>
        <h2>Zamówienie przyjęte!</h2>
        <p class="order-id">Nr zamówienia: <strong>{order.get('order_id', '–')}</strong></p>
        <p>Wysłaliśmy potwierdzenie na adres <strong>{order.get('client_email', '')}</strong></p>
        <p>Nasz cukiernik skontaktuje się z Tobą w ciągu 24 godzin, aby potwierdzić szczegóły.</p>
        <div class="success-details">
            <p>📅 Data: {order.get('event_date', '–')}</p>
            <p>💰 Szacunkowa wycena: {order.get('total', 0):.0f} zł</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Nowe zamówienie", use_container_width=True):
            for key in ["step", "order", "cart"]:
                del st.session_state[key]
            st.rerun()

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <p>✦ <strong>NAZWA TWOJEJ CUKIERNI</strong> ✦</p>
    <p>ul. Twoja Ulica 1, Twoje Miasto &nbsp;·&nbsp; Tel: +48 XXX XXX XXX &nbsp;·&nbsp; kontakt@twoja-cukiernia.pl</p>
    <p style="font-size:0.75rem; opacity:0.5; margin-top:8px;">© 2025 Wszelkie prawa zastrzeżone</p>
</div>
""", unsafe_allow_html=True)
