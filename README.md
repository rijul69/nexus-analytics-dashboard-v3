# Nexus Analytics — E-Commerce Sales Analytics Dashboard

A premium, business-intelligence-grade **E-Commerce Sales Analytics Dashboard** built with **Flask, Pandas, Plotly and Bootstrap 5**. Designed to look and feel like a production analytics product (Power BI / Tableau / Amazon Seller Central style), with a dark theme, gradient KPI cards, glassmorphism, and fully interactive charts — computed live from a real dataset with **no placeholder values**.

---

## ✨ Features

- **Executive Dashboard** — 8 KPI cards + 12 interactive Plotly charts
- **Products, Customers, Payments, Reviews, Sellers** — dedicated analytics pages
- **Dynamic Filters** — Year, Month, State, Payment Type, Category (server-side, query-string driven)
- **Premium Dark UI** — dark sidebar, gradient cards, hover animations, responsive layout
- **Data Tables** — ranked leaderboards for categories, customers and sellers
- **100% Data-Driven** — every KPI and chart is computed directly from `cleaned_ecommerce.csv`

---

## 🗂 Project Structure

```
E-Commerce-Dashboard/
│
├── app.py                     # Flask backend, data processing & Plotly chart builders
├── requirements.txt
├── README.md
├── cleaned_ecommerce.csv      # Dataset
│
├── templates/
│   ├── base.html               # Sidebar, navbar, filter bar, layout shell
│   ├── dashboard.html          # Executive overview
│   ├── products.html
│   ├── customers.html
│   ├── payments.html
│   ├── reviews.html
│   ├── sellers.html
│   └── about.html
│
├── static/
│   ├── css/style.css            # Premium dark BI theme
│   ├── js/script.js             # Sidebar toggle, chart rendering, KPI count-up
│   └── images/
│
└── assets/
```

---

## 🧰 Tech Stack

| Layer      | Technology              |
|------------|--------------------------|
| Backend    | Python, Flask             |
| Data       | Pandas, NumPy             |
| Charts     | Plotly (dark theme)       |
| Frontend   | Bootstrap 5, Bootstrap Icons, HTML5, CSS3, JavaScript |
| Fonts      | Inter, Space Grotesk (Google Fonts) |

---

## ⚙️ Installation

1. **Clone / extract** the project folder.

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. Make sure `cleaned_ecommerce.csv` is present in the project root (same folder as `app.py`).

---

## ▶️ Run Instructions

```bash
python app.py
```

Then open your browser at:

```
http://127.0.0.1:5000
```

The app runs in debug mode by default — disable this (`debug=False`) before any production deployment.

---

## 📊 Dataset

`cleaned_ecommerce.csv` contains 42 columns describing the full order lifecycle: order and delivery timestamps, customer and seller geography, product attributes, payment details, review scores, and derived fields (`Delivery_Days`, `Total_Amount`, `Year`, `Month`, `Weekday`, etc.). All KPIs and charts are computed live from this file using Pandas — nothing is hardcoded.

---

## 🖼 Screenshots

> Add screenshots of the Dashboard, Products, Customers, Payments, Reviews and Sellers pages here after running the app locally.

```
assets/screenshot-dashboard.png
assets/screenshot-products.png
assets/screenshot-customers.png
```

---

## 📁 Pages Overview

| Page       | Description |
|------------|-------------|
| Dashboard  | KPIs + 12 charts: sales trend, orders, revenue, payment split, top categories/states/sellers, reviews, delivery, AOV, weekday pattern, customer geography |
| Products   | Category & product performance, category table |
| Customers  | Geography, top cities, top-spending customers |
| Payments   | Payment method split, installments, revenue by method, trend |
| Reviews    | Rating distribution, category satisfaction, rating trend |
| Sellers    | Top sellers, seller geography, seller leaderboard |
| About      | Project description, tech stack, dataset info |

---

## 👨‍💻 Developer Notes

This project was built as a **Data Science Major Project** to demonstrate:
- Data cleaning & feature engineering with Pandas
- KPI design and business metric computation
- Interactive data visualization with Plotly
- Full-stack web development with Flask + Jinja2
- Modern, production-quality UI/UX design

---

## 📄 License

This project is provided for educational and academic purposes.
