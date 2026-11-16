# Simple ERP (Desktop App)

A small desktop ERP application written in **Python** with **Tkinter** and **SQLite**.
It is made for beginners: the code is short, commented in simple English, and easy to read.

You can manage products, customers and sales, and see a quick summary on the dashboard.

## Features

- **Dashboard**: total products, customers, sales, revenue, and a low-stock list (5 or less items left)
- **Products**: add, update and delete products (name, price, stock)
- **Customers**: add, update and delete customers (name, phone)
- **Sales**: choose a customer and a product, enter a quantity, and sell
  - Total is calculated automatically (price x quantity)
  - Stock is reduced after every sale
  - A sale is blocked if there is not enough stock
- Products and customers that already have sales cannot be deleted (keeps the data safe)
- Modern look: sidebar menu, cards, and clean tables

## Requirements

- Python 3.8 or newer
- Nothing else to install. Tkinter and SQLite are included with Python.

> On some Linux systems Tkinter is a separate package: `sudo apt install python3-tk`

## How to run

1. Download or clone this project.
2. Open a terminal in the project folder.
3. Run:

```
python erp_app.py
```

The first time you run it, a database file called `erp_data.db` is created automatically in the same folder.

## How to use

1. Open **Products** and add a few products with price and stock.
2. Open **Customers** and add a customer.
3. Open **Sales**, pick a customer and a product, type a quantity, and click **Sell**.
4. Open **Dashboard** to see the totals and low-stock products.

To update or delete a record, click its row in the table first. The form fills in automatically.

## Project structure

```
erp_app.py      # the whole application
erp_data.db     # database file (created automatically, not uploaded to Git)
README.md
```

Inside `erp_app.py` the code has 3 parts:

| Part | What it does |
|------|--------------|
| Part 1 | Database functions (create tables, add, read, update, delete, make a sale) |
| Part 2 | The window (sidebar, pages, forms, tables) |
| Part 3 | Starts the program |

## Database tables

| Table | Columns |
|-------|---------|
| products | id, name, price, stock |
| customers | id, name, phone |
| sales | id, date, customer_id, product_id, quantity, total |

## Change the colors

Open `erp_app.py` and find the lines starting with `COLOR_` at the top of Part 2.
Change the hex codes (for example `COLOR_BLUE = "#2563eb"`) and the whole app look changes.

## Ideas for the next steps

- Search box for products and customers
- Purchase screen (add stock from suppliers)
- Printable invoice / bill
- Export reports to Excel or PDF
- Login screen

## License

Free to use for learning. Add a license file (for example MIT) if you want others to reuse it.
