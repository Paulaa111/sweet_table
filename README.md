# 🎂 Konfigurator Słodkich Stołów

Elegancka aplikacja Streamlit dla cukierni umożliwiająca klientom samodzielne konfigurowanie i zamawianie słodkich stołów. Zamówienia trafiają automatycznie do **Google Sheets** i na **maila cukierni** oraz klienta.

---

## ✨ Funkcje

- **4-krokowy konfigurator** — data, wybór słodkości, podsumowanie, potwierdzenie
- **8 kategorii produktów** — torty, cupcakes, makaroniki, ciasteczka, pralinki, mini desery, candy bar, napoje
- **Automatyczny zapis do Google Sheets** — 2 zakładki: Zamówienia + Produkty
- **E-maile automatyczne** — HTML do klienta + powiadomienie do cukierni
- **Responsywny design** — działa na telefonie i komputerze
- **Unikalny numer zamówienia** — format `SS-20251217-A3X9`

---

## 🚀 Wdrożenie na Streamlit Cloud

### 1. Przygotuj repozytorium GitHub

```bash
git init
git add .
git commit -m "Initial commit: Konfigurator Słodkich Stołów"
git branch -M main
git remote add origin https://github.com/TWOJ_LOGIN/NAZWA_REPO.git
git push -u origin main
```

> ⚠️ **Upewnij się, że plik `.streamlit/secrets.toml` jest w `.gitignore`** — nigdy nie commituj go!

---

### 2. Skonfiguruj Google Sheets

1. Wejdź na [console.cloud.google.com](https://console.cloud.google.com)
2. Utwórz nowy projekt (np. `cukiernia-konfigurator`)
3. Włącz **Google Sheets API** i **Google Drive API**
4. Przejdź do **IAM & Admin → Service Accounts**
5. Utwórz nowe konto serwisowe → pobierz klucz jako **JSON**
6. Utwórz nowy arkusz Google na swoim Drive
7. **Udostępnij arkusz** na e-mail service account (np. `cukiernia@projekt.iam.gserviceaccount.com`) z rolą **Edytor**
8. Skopiuj ID arkusza z URL: `docs.google.com/spreadsheets/d/`**`TU_JEST_ID`**`/edit`

---

### 3. Skonfiguruj Gmail

1. Wejdź na [myaccount.google.com](https://myaccount.google.com)
2. **Bezpieczeństwo** → włącz **Weryfikację dwuetapową**
3. Szukaj **„Hasła aplikacji"** → utwórz nowe dla Mail
4. Skopiuj wygenerowane 16-znakowe hasło

---

### 4. Dodaj Secrets na Streamlit Cloud

1. Wejdź na [share.streamlit.io](https://share.streamlit.io) → zaloguj się przez GitHub
2. Kliknij **New app** → wybierz repozytorium
3. Main file path: `app.py`
4. Kliknij **Advanced settings → Secrets** i wklej (uzupełnij swoimi danymi):

```toml
GOOGLE_SHEET_ID = "wklej_id_arkusza"

[gcp_service_account]
type = "service_account"
project_id = "twoj-projekt"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "nazwa@twoj-projekt.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[email]
sender_email    = "twoja.cukiernia@gmail.com"
sender_password = "xxxx xxxx xxxx xxxx"
bakery_email    = "zamowienia@cukiernia.pl"
```

5. Kliknij **Deploy** 🎉

---

## 🛠️ Lokalne uruchomienie (testowanie)

```bash
# 1. Zainstaluj zależności
pip install -r requirements.txt

# 2. Uzupełnij .streamlit/secrets.toml swoimi danymi

# 3. Uruchom
streamlit run app.py
```

---

## 📁 Struktura plików

```
sweet_table_app/
├── app.py                    # Główna aplikacja
├── requirements.txt          # Zależności Python
├── .gitignore                # Wyklucza secrets.toml z Git
├── assets/
│   └── style.css             # Elegancki styl CSS
├── utils/
│   ├── __init__.py
│   ├── google_sheets.py      # Zapis do arkusza
│   ├── email_sender.py       # Wysyłanie e-maili
│   └── order_utils.py        # Pomocnicze funkcje
└── .streamlit/
    ├── config.toml           # Konfiguracja motywu Streamlit
    └── secrets.toml          # 🔒 LOKALNE — nie commituj!
```

---

## 🎨 Personalizacja — co zmienić przed uruchomieniem

### ① Dane cukierni (szukaj i zamień wszędzie)

| Placeholder | Zamień na |
|---|---|
| `NAZWA TWOJEJ CUKIERNI` | np. Cukiernia Róża |
| `ul. Twoja Ulica 1, Twoje Miasto` | Twój adres |
| `+48 XXX XXX XXX` | Twój numer telefonu |
| `kontakt@twoja-cukiernia.pl` | Twój e-mail |
| `Twoja Cukiernia` | Krótka nazwa do nagłówka |

Placeholdery występują w: `app.py` (hero, footer) i `utils/email_sender.py` (e-maile HTML).

### ② Dodaj/zmień produkty

W `app.py` w sekcji `PRODUCTS` możesz dodawać kategorie i produkty wg wzoru:

```python
"Nowa Kategoria": {
    "icon": "🍩",
    "items": {
        "Nazwa produktu": {
            "price": 15,      # cena w zł
            "unit": "szt.",   # jednostka
            "min": 10,        # minimalna ilość
            "desc": "Opis"    # opis dla klienta
        }
    }
}
```

---

## 💡 Wsparcie

Masz pytania? Skontaktuj się z osobą, która przygotowała aplikację. ✨
