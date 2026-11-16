# Simple ERP - made with Python, Tkinter and SQLite
# Pages: Dashboard, Products, Customers, Sales
#
# How to run:  python erp_app.py
#
# The file has 4 parts:
#   PART 1 - database (saving and reading data)
#   PART 2 - what happens when we click buttons
#   PART 3 - drawing the screen (window, buttons, tables)
#   PART 4 - start the app

import sqlite3                       # database that comes with python
import tkinter as tk                 # window library that comes with python
from tkinter import ttk, messagebox  # ttk = table and dropdown, messagebox = popup
from datetime import datetime        # to save date of the sale

DB_FILE = "erp_data.db"   # the database file, it is made automatically


# ------------------------------------------------------------
# PART 1 - DATABASE
# Think of the database like an excel file.
# Every table is one sheet in that file.
# ------------------------------------------------------------

def run_query(sql, values=()):
    # use this when we want to CHANGE data (insert, update, delete)
    conn = sqlite3.connect(DB_FILE)   # open the database
    cur = conn.cursor()
    cur.execute(sql, values)          # run the command
    conn.commit()                     # save the change
    conn.close()


def get_rows(sql, values=()):
    # use this when we only want to READ data (select)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(sql, values)
    rows = cur.fetchall()             # all the rows we got
    conn.close()
    return rows


def create_tables():
    # make the 3 tables, only if they are not already there
    run_query("""CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL)""")

    run_query("""CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT)""")

    run_query("""CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    customer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    total REAL NOT NULL)""")


# ----- products -----

def add_product(name, price, stock):
    run_query("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
              (name, price, stock))


def get_products():
    return get_rows("SELECT id, name, price, stock FROM products ORDER BY id")


def update_product(product_id, name, price, stock):
    run_query("UPDATE products SET name=?, price=?, stock=? WHERE id=?",
              (name, price, stock, product_id))


def delete_product(product_id):
    # if this product is already sold, we do not delete it
    # (otherwise the sales list will have a product that does not exist)
    sold = get_rows("SELECT id FROM sales WHERE product_id=?", (product_id,))
    if len(sold) > 0:
        return False, "This product is already sold, so it cannot be deleted."
    run_query("DELETE FROM products WHERE id=?", (product_id,))
    return True, "Product deleted."


# ----- customers -----

def add_customer(name, phone):
    run_query("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))


def get_customers():
    return get_rows("SELECT id, name, phone FROM customers ORDER BY id")


def update_customer(customer_id, name, phone):
    run_query("UPDATE customers SET name=?, phone=? WHERE id=?",
              (name, phone, customer_id))


def delete_customer(customer_id):
    sold = get_rows("SELECT id FROM sales WHERE customer_id=?", (customer_id,))
    if len(sold) > 0:
        return False, "This customer has sales, so it cannot be deleted."
    run_query("DELETE FROM customers WHERE id=?", (customer_id,))
    return True, "Customer deleted."


# ----- sales -----

def make_sale(customer_id, product_id, quantity):
    # This is the main logic of the app. Steps:
    #   1. get the price and stock of the product
    #   2. check the quantity is ok
    #   3. total = price x quantity
    #   4. save the sale
    #   5. reduce the stock
    # It gives back two things: True/False and a message to show.

    rows = get_rows("SELECT price, stock FROM products WHERE id=?", (product_id,))
    if len(rows) == 0:
        return False, "Product not found."

    price = rows[0][0]
    stock = rows[0][1]

    if quantity <= 0:
        return False, "Quantity must be more than 0."
    if quantity > stock:
        return False, "Not enough stock. Only " + str(stock) + " left."

    total = price * quantity
    today = datetime.now().strftime("%d-%m-%Y %H:%M")

    run_query("INSERT INTO sales (date, customer_id, product_id, quantity, total) "
              "VALUES (?, ?, ?, ?, ?)",
              (today, customer_id, product_id, quantity, total))

    new_stock = stock - quantity
    run_query("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))

    return True, "Sale done! Total = " + str(total)


def get_sales():
    # JOIN means: take the names from the other tables,
    # so we can show "Rahul" instead of customer id 3
    return get_rows("""SELECT sales.id, sales.date, customers.name, products.name,
                              sales.quantity, sales.total
                       FROM sales
                       JOIN customers ON sales.customer_id = customers.id
                       JOIN products ON sales.product_id = products.id
                       ORDER BY sales.id DESC""")


# ----- numbers for the dashboard -----

def get_summary():
    summary = {}
    summary["products"] = get_rows("SELECT COUNT(*) FROM products")[0][0]
    summary["customers"] = get_rows("SELECT COUNT(*) FROM customers")[0][0]
    summary["sales"] = get_rows("SELECT COUNT(*) FROM sales")[0][0]

    revenue = get_rows("SELECT SUM(total) FROM sales")[0][0]
    if revenue is None:       # no sales yet, so SUM gives None
        revenue = 0
    summary["revenue"] = revenue

    # products which have 5 or less items left
    summary["low_stock"] = get_rows(
        "SELECT name, stock FROM products WHERE stock <= 5 ORDER BY stock")
    return summary


# ------------------------------------------------------------
# PART 2 - WHAT HAPPENS WHEN WE CLICK
#
# Note: these functions use boxes like entry_p_name, product_table etc.
# Those are made later in PART 3. It still works, because python
# only looks for them when the button is really clicked.
# ------------------------------------------------------------

# ----- small helper functions -----

def get_selected_id(table):
    # gives the id of the row the user clicked, or None if nothing is clicked
    selected = table.selection()
    if len(selected) == 0:
        return None
    values = table.item(selected[0])["values"]
    return values[0]


def fill_table(table, rows):
    # first remove the old rows, then add the new rows
    for old_row in table.get_children():
        table.delete(old_row)

    count = 0
    for row in rows:
        # alternate colors: one white row, one grey row
        if count % 2 == 0:
            color = "light"
        else:
            color = "dark"
        table.insert("", tk.END, values=row, tags=(color,))
        count = count + 1


# ----- changing the page -----

def show_page(page, title, menu_button):
    # hide all the pages
    dashboard_page.pack_forget()
    products_page.pack_forget()
    customers_page.pack_forget()
    sales_page.pack_forget()

    # show only the page we want
    page.pack(fill="both", expand=True)
    page_title.config(text=title)

    # make all menu buttons dark, then make the clicked one blue
    btn_dashboard.config(bg=DARK)
    btn_products.config(bg=DARK)
    btn_customers.config(bg=DARK)
    btn_sales.config(bg=DARK)
    menu_button.config(bg=BLUE)


def open_dashboard():
    refresh_dashboard()      # get the latest numbers first
    show_page(dashboard_page, "Dashboard", btn_dashboard)


def open_products():
    show_page(products_page, "Products", btn_products)


def open_customers():
    show_page(customers_page, "Customers", btn_customers)


def open_sales():
    show_page(sales_page, "Sales", btn_sales)


# ----- refresh (load the data again and show it on screen) -----

def refresh_dashboard():
    s = get_summary()
    label_products.config(text=str(s["products"]))
    label_customers.config(text=str(s["customers"]))
    label_sales.config(text=str(s["sales"]))
    label_revenue.config(text=str(round(s["revenue"], 2)))

    low_stock_box.delete(0, tk.END)    # clear the list
    if len(s["low_stock"]) == 0:
        low_stock_box.insert(tk.END, "  All products have enough stock.")
    for item in s["low_stock"]:
        low_stock_box.insert(tk.END, "  " + item[0] + "  -  " + str(item[1]) + " left")


def refresh_products():
    fill_table(product_table, get_products())


def refresh_customers():
    fill_table(customer_table, get_customers())


def refresh_sales():
    fill_table(sales_table, get_sales())


def refresh_dropdowns():
    # every item in the dropdown looks like "3 - Rahul"  (id - name)
    customer_list = []
    for c in get_customers():
        customer_list.append(str(c[0]) + " - " + c[1])
    dropdown_customer["values"] = customer_list

    product_list = []
    for p in get_products():
        product_list.append(str(p[0]) + " - " + p[1] + " (stock " + str(p[3]) + ")")
    dropdown_product["values"] = product_list

    dropdown_customer.set("")
    dropdown_product.set("")


def refresh_all():
    refresh_products()
    refresh_customers()
    refresh_sales()
    refresh_dropdowns()
    refresh_dashboard()


# ----- products page buttons -----

def clear_product_form():
    entry_p_name.delete(0, tk.END)
    entry_p_price.delete(0, tk.END)
    entry_p_stock.delete(0, tk.END)
    product_table.selection_remove(product_table.selection())


def read_product_form():
    # read the 3 boxes and check them. Gives (name, price, stock) or None if wrong.
    name = entry_p_name.get().strip()
    if name == "":
        messagebox.showwarning("Missing", "Please enter the product name.")
        return None

    try:
        price = float(entry_p_price.get())
        stock = int(entry_p_stock.get())
    except ValueError:
        # happens when user types letters in price or stock
        messagebox.showwarning("Wrong input", "Price must be a number and stock must be a whole number.")
        return None

    if price < 0 or stock < 0:
        messagebox.showwarning("Wrong input", "Price and stock cannot be negative.")
        return None

    return name, price, stock


def add_product_click():
    data = read_product_form()
    if data is None:
        return
    add_product(data[0], data[1], data[2])
    clear_product_form()
    refresh_all()


def product_row_clicked(event):
    # when user clicks a row in the table, put that row in the 3 boxes
    selected = product_table.selection()
    if len(selected) == 0:
        return
    values = product_table.item(selected[0])["values"]
    entry_p_name.delete(0, tk.END)
    entry_p_price.delete(0, tk.END)
    entry_p_stock.delete(0, tk.END)
    entry_p_name.insert(0, values[1])
    entry_p_price.insert(0, values[2])
    entry_p_stock.insert(0, values[3])


def update_product_click():
    product_id = get_selected_id(product_table)
    if product_id is None:
        messagebox.showinfo("Select", "First click a product in the table.")
        return
    data = read_product_form()
    if data is None:
        return
    update_product(product_id, data[0], data[1], data[2])
    clear_product_form()
    refresh_all()


def delete_product_click():
    product_id = get_selected_id(product_table)
    if product_id is None:
        messagebox.showinfo("Select", "First click a product in the table.")
        return
    if not messagebox.askyesno("Confirm", "Do you want to delete this product?"):
        return
    ok, message = delete_product(product_id)
    messagebox.showinfo("Result", message)
    clear_product_form()
    refresh_all()


# ----- customers page buttons -----

def clear_customer_form():
    entry_c_name.delete(0, tk.END)
    entry_c_phone.delete(0, tk.END)
    customer_table.selection_remove(customer_table.selection())


def add_customer_click():
    name = entry_c_name.get().strip()
    phone = entry_c_phone.get().strip()
    if name == "":
        messagebox.showwarning("Missing", "Please enter the customer name.")
        return
    add_customer(name, phone)
    clear_customer_form()
    refresh_all()


def customer_row_clicked(event):
    customer_id = get_selected_id(customer_table)
    if customer_id is None:
        return
    # we take the name and phone from the database, not from the table.
    # The table changes a phone like 0123 into 123 (the 0 is lost).
    for c in get_customers():
        if c[0] == customer_id:
            entry_c_name.delete(0, tk.END)
            entry_c_phone.delete(0, tk.END)
            entry_c_name.insert(0, c[1])
            entry_c_phone.insert(0, c[2])


def update_customer_click():
    customer_id = get_selected_id(customer_table)
    if customer_id is None:
        messagebox.showinfo("Select", "First click a customer in the table.")
        return
    name = entry_c_name.get().strip()
    if name == "":
        messagebox.showwarning("Missing", "Please enter the customer name.")
        return
    update_customer(customer_id, name, entry_c_phone.get().strip())
    clear_customer_form()
    refresh_all()


def delete_customer_click():
    customer_id = get_selected_id(customer_table)
    if customer_id is None:
        messagebox.showinfo("Select", "First click a customer in the table.")
        return
    if not messagebox.askyesno("Confirm", "Do you want to delete this customer?"):
        return
    ok, message = delete_customer(customer_id)
    messagebox.showinfo("Result", message)
    clear_customer_form()
    refresh_all()


# ----- sales page button -----

def sell_click():
    if dropdown_customer.get() == "" or dropdown_product.get() == "":
        messagebox.showwarning("Missing", "Please choose a customer and a product.")
        return

    try:
        quantity = int(entry_quantity.get())
    except ValueError:
        messagebox.showwarning("Wrong input", "Quantity must be a whole number.")
        return

    # The dropdown text is like "3 - Rahul".
    # split(" - ") cuts it into ["3", "Rahul"], and [0] is the id.
    customer_id = int(dropdown_customer.get().split(" - ")[0])
    product_id = int(dropdown_product.get().split(" - ")[0])

    ok, message = make_sale(customer_id, product_id, quantity)
    if ok:
        messagebox.showinfo("Done", message)
        entry_quantity.delete(0, tk.END)
        refresh_all()
    else:
        messagebox.showwarning("Cannot sell", message)


# ------------------------------------------------------------
# PART 3 - DRAWING THE SCREEN
# ------------------------------------------------------------

create_tables()   # make sure the database tables are there

# colors - change these and the whole look changes
BG = "#f1f5f9"       # page background (light grey)
WHITE = "#ffffff"
DARK = "#1e293b"     # left menu
BLUE = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
ORANGE = "#f59e0b"
GREY = "#64748b"
TEXT = "#0f172a"
FONT = "Segoe UI"


# ----- small helper functions to draw things -----

def make_button(parent, text, color, command):
    # a flat coloured button
    return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                     activebackground=color, activeforeground="white",
                     font=(FONT, 10, "bold"), relief="flat", bd=0,
                     highlightthickness=0,     # removes the thin outline
                     padx=16, pady=6, cursor="hand2")


def make_entry(parent, label_text, width, column):
    # a small grey label with a text box under it
    box = tk.Frame(parent, bg=WHITE)
    box.grid(row=0, column=column, padx=(0, 12))
    tk.Label(box, text=label_text, bg=WHITE, fg=GREY, font=(FONT, 9)).pack(anchor="w")
    # light grey border, it turns blue when we click inside the box
    entry = tk.Entry(box, width=width, font=(FONT, 11), relief="flat", bg="#f8fafc",
                     highlightthickness=1, highlightbackground="#cbd5e1",
                     highlightcolor=BLUE)
    entry.pack(ipady=4)
    return entry


def make_table(parent, columns, widths):
    # a table with scrollbar
    frame = tk.Frame(parent, bg=WHITE)
    frame.pack(fill="both", expand=True, pady=(15, 0))

    table = ttk.Treeview(frame, columns=columns, show="headings")
    for i in range(len(columns)):
        table.heading(columns[i], text=columns[i], anchor="w")
        table.column(columns[i], width=widths[i], anchor="w")

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)

    # the two row colors used in fill_table
    table.tag_configure("light", background="#ffffff")
    table.tag_configure("dark", background="#f1f5f9")
    return table


def make_stat_card(parent, title, color, column):
    # a card with a small title and a big number. Gives back the number label.
    card = tk.Frame(parent, bg=WHITE, padx=18, pady=14)
    card.grid(row=0, column=column, padx=(0, 15), sticky="ew")
    # weight=1 and the same uniform name = all 4 cards get equal width
    parent.columnconfigure(column, weight=1, uniform="cards")

    tk.Frame(card, bg=color, height=4).pack(fill="x", pady=(0, 10))  # colored line on top
    tk.Label(card, text=title, bg=WHITE, fg=GREY, font=(FONT, 9, "bold")).pack(anchor="w")
    number_label = tk.Label(card, text="0", bg=WHITE, fg=color, font=(FONT, 24, "bold"))
    number_label.pack(anchor="w")
    return number_label


# ----- main window -----

root = tk.Tk()
root.title("Simple ERP")
root.geometry("1050x620")
root.minsize(900, 550)
root.configure(bg=BG)

# look of the tables
style = ttk.Style()
style.theme_use("clam")    # "clam" theme lets us change the colors
style.configure("Treeview", background="white", fieldbackground="white",
                foreground=TEXT, rowheight=32, font=(FONT, 10), borderwidth=0)
style.configure("Treeview.Heading", background="#e2e8f0", foreground=TEXT,
                font=(FONT, 10, "bold"), relief="flat", padding=8)
style.map("Treeview", background=[("selected", BLUE)],
          foreground=[("selected", "white")])    # selected row is blue


# ----- left menu -----

sidebar = tk.Frame(root, bg=DARK, width=210)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)    # keep the width fixed

tk.Label(sidebar, text="Simple ERP", bg=DARK, fg="white",
         font=(FONT, 18, "bold")).pack(anchor="w", padx=22, pady=(28, 4))
tk.Label(sidebar, text="Business manager", bg=DARK, fg="#94a3b8",
         font=(FONT, 9)).pack(anchor="w", padx=22, pady=(0, 30))


def make_menu_button(text, command):
    button = tk.Button(sidebar, text="   " + text, command=command, bg=DARK,
                       fg="white", activebackground=BLUE, activeforeground="white",
                       font=(FONT, 11), relief="flat", bd=0, highlightthickness=0,
                       anchor="w", padx=14, pady=10, cursor="hand2")
    button.pack(fill="x", padx=12, pady=2)
    return button


btn_dashboard = make_menu_button("Dashboard", open_dashboard)
btn_products = make_menu_button("Products", open_products)
btn_customers = make_menu_button("Customers", open_customers)
btn_sales = make_menu_button("Sales", open_sales)


# ----- right side: title on top, pages below -----

right_side = tk.Frame(root, bg=BG)
right_side.pack(side="right", fill="both", expand=True)

page_title = tk.Label(right_side, text="Dashboard", bg=BG, fg=TEXT,
                      font=(FONT, 20, "bold"))
page_title.pack(anchor="w", padx=30, pady=(22, 10))

page_area = tk.Frame(right_side, bg=BG)
page_area.pack(fill="both", expand=True, padx=30, pady=(0, 20))

# 4 empty pages. Only one is shown at a time (see show_page)
dashboard_page = tk.Frame(page_area, bg=BG)
products_page = tk.Frame(page_area, bg=BG)
customers_page = tk.Frame(page_area, bg=BG)
sales_page = tk.Frame(page_area, bg=BG)


# ----- dashboard page -----

cards_row = tk.Frame(dashboard_page, bg=BG)
cards_row.pack(fill="x")

label_products = make_stat_card(cards_row, "PRODUCTS", BLUE, 0)
label_customers = make_stat_card(cards_row, "CUSTOMERS", GREEN, 1)
label_sales = make_stat_card(cards_row, "SALES", ORANGE, 2)
label_revenue = make_stat_card(cards_row, "REVENUE", RED, 3)

low_stock_card = tk.Frame(dashboard_page, bg=WHITE, padx=18, pady=14)
low_stock_card.pack(fill="both", expand=True, pady=(18, 0))
tk.Label(low_stock_card, text="Low stock (5 or less)", bg=WHITE, fg=TEXT,
         font=(FONT, 12, "bold")).pack(anchor="w", pady=(0, 8))

low_stock_box = tk.Listbox(low_stock_card, font=(FONT, 11), bd=0,
                           highlightthickness=0, bg=WHITE, fg=TEXT, height=8)
low_stock_box.pack(fill="both", expand=True)


# ----- products page -----

product_form = tk.Frame(products_page, bg=WHITE, padx=18, pady=14)
product_form.pack(fill="x")

product_fields = tk.Frame(product_form, bg=WHITE)
product_fields.pack(anchor="w")
entry_p_name = make_entry(product_fields, "Product name", 30, 0)
entry_p_price = make_entry(product_fields, "Price", 12, 1)
entry_p_stock = make_entry(product_fields, "Stock", 12, 2)

product_buttons = tk.Frame(product_form, bg=WHITE)
product_buttons.pack(anchor="w", pady=(12, 0))
make_button(product_buttons, "Add", BLUE, add_product_click).pack(side="left", padx=(0, 8))
make_button(product_buttons, "Update", GREEN, update_product_click).pack(side="left", padx=(0, 8))
make_button(product_buttons, "Delete", RED, delete_product_click).pack(side="left", padx=(0, 8))
make_button(product_buttons, "Clear", GREY, clear_product_form).pack(side="left")

product_table = make_table(products_page, ("ID", "Name", "Price", "Stock"),
                           (60, 380, 120, 120))
product_table.bind("<<TreeviewSelect>>", product_row_clicked)   # runs when a row is clicked


# ----- customers page -----

customer_form = tk.Frame(customers_page, bg=WHITE, padx=18, pady=14)
customer_form.pack(fill="x")

customer_fields = tk.Frame(customer_form, bg=WHITE)
customer_fields.pack(anchor="w")
entry_c_name = make_entry(customer_fields, "Customer name", 30, 0)
entry_c_phone = make_entry(customer_fields, "Phone", 20, 1)

customer_buttons = tk.Frame(customer_form, bg=WHITE)
customer_buttons.pack(anchor="w", pady=(12, 0))
make_button(customer_buttons, "Add", BLUE, add_customer_click).pack(side="left", padx=(0, 8))
make_button(customer_buttons, "Update", GREEN, update_customer_click).pack(side="left", padx=(0, 8))
make_button(customer_buttons, "Delete", RED, delete_customer_click).pack(side="left", padx=(0, 8))
make_button(customer_buttons, "Clear", GREY, clear_customer_form).pack(side="left")

customer_table = make_table(customers_page, ("ID", "Name", "Phone"), (60, 380, 240))
customer_table.bind("<<TreeviewSelect>>", customer_row_clicked)


# ----- sales page -----

sales_form = tk.Frame(sales_page, bg=WHITE, padx=18, pady=14)
sales_form.pack(fill="x")

sales_fields = tk.Frame(sales_form, bg=WHITE)
sales_fields.pack(anchor="w")

# customer dropdown
box1 = tk.Frame(sales_fields, bg=WHITE)
box1.grid(row=0, column=0, padx=(0, 12))
tk.Label(box1, text="Customer", bg=WHITE, fg=GREY, font=(FONT, 9)).pack(anchor="w")
dropdown_customer = ttk.Combobox(box1, width=24, font=(FONT, 11), state="readonly")
dropdown_customer.pack(ipady=3)

# product dropdown
box2 = tk.Frame(sales_fields, bg=WHITE)
box2.grid(row=0, column=1, padx=(0, 12))
tk.Label(box2, text="Product", bg=WHITE, fg=GREY, font=(FONT, 9)).pack(anchor="w")
dropdown_product = ttk.Combobox(box2, width=32, font=(FONT, 11), state="readonly")
dropdown_product.pack(ipady=3)

entry_quantity = make_entry(sales_fields, "Quantity", 10, 2)

sales_buttons = tk.Frame(sales_form, bg=WHITE)
sales_buttons.pack(anchor="w", pady=(12, 0))
make_button(sales_buttons, "Sell", GREEN, sell_click).pack(side="left")

sales_table = make_table(sales_page, ("ID", "Date", "Customer", "Product", "Qty", "Total"),
                         (50, 140, 160, 180, 60, 100))


# ------------------------------------------------------------
# PART 4 - START THE APP
# ------------------------------------------------------------

refresh_all()       # load the data on the screen
open_dashboard()    # first page we see
root.mainloop()     # keep the window open until we close it