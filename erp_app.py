# ============================================================
# SIMPLE ERP APPLICATION (Desktop)
# Built with: Python + Tkinter (window) + SQLite (database)
# Modules: Products, Customers, Sales, Dashboard
#
# The file has 3 parts:
#   PART 1 - Database functions (saving and reading data)
#   PART 2 - The window (buttons, tables, forms)
#   PART 3 - Start the program
# ============================================================

import sqlite3                      # built-in database
import tkinter as tk                # built-in window library
from tkinter import ttk, messagebox # ttk = nicer widgets, messagebox = popups
from datetime import datetime       # to save the date of each sale

# The database is one file saved next to this script
DB_FILE = "erp_data.db"


# ============================================================
# PART 1 - DATABASE FUNCTIONS
# Think of the database as an Excel file with several sheets.
# Each "table" is one sheet.
# ============================================================

def run_query(sql, values=()):
    """Use this to CHANGE data (insert, update, delete)."""
    conn = sqlite3.connect(DB_FILE)   # open the database
    cur = conn.cursor()               # cursor = the pen that writes
    cur.execute(sql, values)          # run the command
    conn.commit()                     # save the changes
    conn.close()                      # close the database


def get_rows(sql, values=()):
    """Use this to READ data (select). Returns a list of rows."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(sql, values)
    rows = cur.fetchall()             # get all the results
    conn.close()
    return rows


def create_tables():
    """Create the tables the first time the program runs."""
    run_query("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    run_query("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT
        )
    """)
    run_query("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total REAL NOT NULL
        )
    """)


# ---------- Products ----------

def add_product(name, price, stock):
    run_query("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
              (name, price, stock))

def get_products():
    return get_rows("SELECT id, name, price, stock FROM products ORDER BY id")

def update_product(product_id, name, price, stock):
    run_query("UPDATE products SET name=?, price=?, stock=? WHERE id=?",
              (name, price, stock, product_id))

def delete_product(product_id):
    """Returns (True/False, message). We block deleting a product that was sold."""
    sold = get_rows("SELECT id FROM sales WHERE product_id=?", (product_id,))
    if len(sold) > 0:
        return False, "This product has sales records, so it cannot be deleted."
    run_query("DELETE FROM products WHERE id=?", (product_id,))
    return True, "Product deleted."


# ---------- Customers ----------

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
        return False, "This customer has sales records, so cannot be deleted."
    run_query("DELETE FROM customers WHERE id=?", (customer_id,))
    return True, "Customer deleted."


# ---------- Sales ----------

def make_sale(customer_id, product_id, quantity):
    """
    The main business logic:
      1. Find the product
      2. Check there is enough stock
      3. Calculate total = price x quantity
      4. Save the sale
      5. Reduce the stock
    Returns (True/False, message).
    """
    rows = get_rows("SELECT price, stock FROM products WHERE id=?", (product_id,))
    if len(rows) == 0:
        return False, "Product not found."

    price = rows[0][0]
    stock = rows[0][1]

    if quantity <= 0:
        return False, "Quantity must be more than 0."
    if quantity > stock:
        return False, "Not enough stock. Available: " + str(stock)

    total = price * quantity
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    run_query("""INSERT INTO sales (date, customer_id, product_id, quantity, total)
                 VALUES (?, ?, ?, ?, ?)""",
              (today, customer_id, product_id, quantity, total))

    new_stock = stock - quantity
    run_query("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))

    return True, "Sale saved. Total = " + str(total)

def get_sales():
    # JOIN = combine tables so we can show names instead of id numbers
    return get_rows("""
        SELECT sales.id, sales.date, customers.name, products.name,
               sales.quantity, sales.total
        FROM sales
        JOIN customers ON sales.customer_id = customers.id
        JOIN products  ON sales.product_id  = products.id
        ORDER BY sales.id DESC
    """)


# ---------- Dashboard numbers ----------

def get_summary():
    """Returns a dictionary with the numbers shown on the dashboard."""
    summary = {}
    summary["products"] = get_rows("SELECT COUNT(*) FROM products")[0][0]
    summary["customers"] = get_rows("SELECT COUNT(*) FROM customers")[0][0]
    summary["sales"] = get_rows("SELECT COUNT(*) FROM sales")[0][0]
    revenue = get_rows("SELECT SUM(total) FROM sales")[0][0]
    if revenue is None:          # no sales yet -> SUM gives None
        revenue = 0
    summary["revenue"] = revenue
    # products with 5 or fewer items left
    summary["low_stock"] = get_rows(
        "SELECT name, stock FROM products WHERE stock <= 5 ORDER BY stock")
    return summary


# ============================================================
# PART 2 - THE WINDOW (modern look)
#
# Layout of the window:
#   +-----------+------------------------------------+
#   |  SIDEBAR  |  Page title                        |
#   |  (menu)   |  Page content (cards, forms, table)|
#   +-----------+------------------------------------+
#
# Only ONE page is visible at a time. Clicking a sidebar
# button hides the old page and shows the new one.
# ============================================================

# ---------- Colors (change these to change the whole look) ----------
COLOR_SIDEBAR = "#1e293b"   # dark blue menu
COLOR_BG = "#f1f5f9"        # light grey page background
COLOR_CARD = "#ffffff"      # white boxes
COLOR_TEXT = "#0f172a"      # almost black
COLOR_MUTED = "#64748b"     # grey small text
COLOR_BLUE = "#2563eb"
COLOR_GREEN = "#16a34a"
COLOR_RED = "#dc2626"
COLOR_ORANGE = "#f59e0b"
COLOR_GREY = "#64748b"
COLOR_BORDER = "#cbd5e1"

FONT = "Segoe UI"           # normal Windows font


# ---------- Small helper functions to build the screen ----------
# These are used many times, so we write them once.

def make_button(parent, text, color, command):
    """A flat coloured button."""
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg="white",
                     activebackground=color, activeforeground="white",
                     font=(FONT, 10, "bold"), relief="flat", bd=0,
                     padx=18, pady=7, cursor="hand2")


def make_card(parent):
    """A white box with some space inside (like a card)."""
    return tk.Frame(parent, bg=COLOR_CARD, padx=18, pady=14)


def make_field(parent, label_text, width, column):
    """A small label on top and a text box below it. Returns the text box."""
    box = tk.Frame(parent, bg=COLOR_CARD)
    box.grid(row=0, column=column, padx=(0, 14))
    tk.Label(box, text=label_text, bg=COLOR_CARD, fg=COLOR_MUTED,
             font=(FONT, 9)).pack(anchor="w", pady=(0, 3))
    entry = tk.Entry(box, width=width, font=(FONT, 11), relief="flat",
                     bg="#f8fafc", highlightthickness=1,
                     highlightbackground=COLOR_BORDER,   # border when not clicked
                     highlightcolor=COLOR_BLUE)          # border when clicked
    entry.pack(ipady=5)
    return entry


def make_dropdown(parent, label_text, width, column):
    """Same as make_field, but with a dropdown list. Returns the dropdown."""
    box = tk.Frame(parent, bg=COLOR_CARD)
    box.grid(row=0, column=column, padx=(0, 14))
    tk.Label(box, text=label_text, bg=COLOR_CARD, fg=COLOR_MUTED,
             font=(FONT, 9)).pack(anchor="w", pady=(0, 3))
    dropdown = ttk.Combobox(box, width=width, font=(FONT, 11), state="readonly")
    dropdown.pack(ipady=3)
    return dropdown


def make_table(parent, columns, widths):
    """A table with a scrollbar and alternate row colours."""
    frame = tk.Frame(parent, bg=COLOR_CARD)
    frame.pack(fill="both", expand=True, pady=(15, 0))

    table = ttk.Treeview(frame, columns=columns, show="headings")
    for i in range(len(columns)):
        table.heading(columns[i], text=columns[i], anchor="w")
        table.column(columns[i], width=widths[i], anchor="w")

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)

    # two row colours, we use them one after another
    table.tag_configure("light", background="#ffffff")
    table.tag_configure("dark", background="#f1f5f9")
    return table


def fill_table(table, rows):
    """Remove old rows, then add the new rows."""
    for old_row in table.get_children():
        table.delete(old_row)
    count = 0
    for row in rows:
        if count % 2 == 0:
            color_tag = "light"
        else:
            color_tag = "dark"
        table.insert("", tk.END, values=row, tags=(color_tag,))
        count = count + 1


# ---------- The main window class ----------

class ERPApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Simple ERP")
        self.root.geometry("1050x620")
        self.root.minsize(900, 550)
        self.root.configure(bg=COLOR_BG)

        # Remember which row is selected in Products / Customers
        self.selected_product_id = None
        self.selected_customer_id = None

        self.setup_table_style()
        self.build_sidebar()
        self.build_content_area()

        # Build the inside of each page
        self.build_dashboard_page(self.pages["Dashboard"])
        self.build_product_page(self.pages["Products"])
        self.build_customer_page(self.pages["Customers"])
        self.build_sales_page(self.pages["Sales"])

        self.refresh_all()
        self.show_page("Dashboard")

    # ---------------- style of tables ----------------
    def setup_table_style(self):
        style = ttk.Style()
        style.theme_use("clam")   # "clam" lets us change colours
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground=COLOR_TEXT, rowheight=32,
                        font=(FONT, 10), borderwidth=0)
        style.configure("Treeview.Heading", background="#e2e8f0",
                        foreground=COLOR_TEXT, font=(FONT, 10, "bold"),
                        relief="flat", padding=8)
        # blue row when selected
        style.map("Treeview",
                  background=[("selected", COLOR_BLUE)],
                  foreground=[("selected", "white")])

    # ---------------- sidebar (left menu) ----------------
    def build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=COLOR_SIDEBAR, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)   # keep the width fixed

        tk.Label(sidebar, text="Simple ERP", bg=COLOR_SIDEBAR, fg="white",
                 font=(FONT, 18, "bold")).pack(anchor="w", padx=22, pady=(28, 4))
        tk.Label(sidebar, text="Business manager", bg=COLOR_SIDEBAR,
                 fg="#94a3b8", font=(FONT, 9)).pack(anchor="w", padx=22, pady=(0, 30))

        # one button for each page
        self.nav_buttons = {}
        page_names = ["Dashboard", "Products", "Customers", "Sales"]
        for name in page_names:
            # "lambda n=name" means: remember THIS name for THIS button.
            # (Without "n=name" every button would open the last page.)
            button = tk.Button(sidebar, text="   " + name,
                               command=lambda n=name: self.show_page(n),
                               bg=COLOR_SIDEBAR, fg="white",
                               activebackground=COLOR_BLUE,
                               activeforeground="white",
                               font=(FONT, 11), relief="flat", bd=0,
                               anchor="w", padx=14, pady=11, cursor="hand2")
            button.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = button

    # ---------------- right side (title + pages) ----------------
    def build_content_area(self):
        content = tk.Frame(self.root, bg=COLOR_BG)
        content.pack(side="right", fill="both", expand=True)

        self.title_label = tk.Label(content, text="", bg=COLOR_BG, fg=COLOR_TEXT,
                                    font=(FONT, 20, "bold"))
        self.title_label.pack(anchor="w", padx=30, pady=(24, 12))

        page_area = tk.Frame(content, bg=COLOR_BG)
        page_area.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        # make one empty page for each name
        self.pages = {}
        for name in ["Dashboard", "Products", "Customers", "Sales"]:
            self.pages[name] = tk.Frame(page_area, bg=COLOR_BG)

    def show_page(self, page_name):
        # hide all pages
        for name in self.pages:
            self.pages[name].pack_forget()
        # show the chosen page
        self.pages[page_name].pack(fill="both", expand=True)
        self.title_label.config(text=page_name)

        # highlight the active menu button
        for name in self.nav_buttons:
            if name == page_name:
                self.nav_buttons[name].config(bg=COLOR_BLUE)
            else:
                self.nav_buttons[name].config(bg=COLOR_SIDEBAR)

        if page_name == "Dashboard":
            self.refresh_dashboard()

    # ---------------- DASHBOARD PAGE ----------------
    def make_stat_card(self, parent, title, color, column):
        """One number card. Returns the label that shows the number."""
        card = tk.Frame(parent, bg=COLOR_CARD, padx=18, pady=14)
        card.grid(row=0, column=column, padx=(0, 15), sticky="ew")
        parent.columnconfigure(column, weight=1)   # all cards share the width

        tk.Frame(card, bg=color, height=4).pack(fill="x", pady=(0, 10))  # coloured line
        tk.Label(card, text=title, bg=COLOR_CARD, fg=COLOR_MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w")
        number_label = tk.Label(card, text="0", bg=COLOR_CARD, fg=color,
                                font=(FONT, 24, "bold"))
        number_label.pack(anchor="w")
        return number_label

    def build_dashboard_page(self, page):
        cards_row = tk.Frame(page, bg=COLOR_BG)
        cards_row.pack(fill="x")

        self.lbl_products = self.make_stat_card(cards_row, "PRODUCTS", COLOR_BLUE, 0)
        self.lbl_customers = self.make_stat_card(cards_row, "CUSTOMERS", COLOR_GREEN, 1)
        self.lbl_sales = self.make_stat_card(cards_row, "SALES", COLOR_ORANGE, 2)
        self.lbl_revenue = self.make_stat_card(cards_row, "REVENUE", COLOR_RED, 3)

        low_card = make_card(page)
        low_card.pack(fill="both", expand=True, pady=(18, 0))
        tk.Label(low_card, text="Low stock (5 or less)", bg=COLOR_CARD,
                 fg=COLOR_TEXT, font=(FONT, 12, "bold")).pack(anchor="w", pady=(0, 8))

        self.low_stock_box = tk.Listbox(low_card, font=(FONT, 11), bd=0,
                                        highlightthickness=0, bg=COLOR_CARD,
                                        fg=COLOR_TEXT, selectbackground="#dbeafe",
                                        selectforeground=COLOR_TEXT, height=8)
        self.low_stock_box.pack(fill="both", expand=True)

    def refresh_dashboard(self):
        s = get_summary()
        self.lbl_products.config(text=str(s["products"]))
        self.lbl_customers.config(text=str(s["customers"]))
        self.lbl_sales.config(text=str(s["sales"]))
        self.lbl_revenue.config(text="{:.2f}".format(s["revenue"]))  # 2 decimals

        self.low_stock_box.delete(0, tk.END)
        if len(s["low_stock"]) == 0:
            self.low_stock_box.insert(tk.END, "  All products have enough stock.")
        for item in s["low_stock"]:
            self.low_stock_box.insert(tk.END, "  " + item[0] + "   -   " + str(item[1]) + " left")

    # ---------------- PRODUCTS PAGE ----------------
    def build_product_page(self, page):
        form = make_card(page)
        form.pack(fill="x")

        fields = tk.Frame(form, bg=COLOR_CARD)
        fields.pack(anchor="w")
        self.p_name = make_field(fields, "Product name", 30, 0)
        self.p_price = make_field(fields, "Price", 12, 1)
        self.p_stock = make_field(fields, "Stock", 12, 2)

        buttons = tk.Frame(form, bg=COLOR_CARD)
        buttons.pack(anchor="w", pady=(14, 0))
        make_button(buttons, "Add", COLOR_BLUE, self.on_add_product).pack(side="left", padx=(0, 8))
        make_button(buttons, "Update", COLOR_GREEN, self.on_update_product).pack(side="left", padx=(0, 8))
        make_button(buttons, "Delete", COLOR_RED, self.on_delete_product).pack(side="left", padx=(0, 8))
        make_button(buttons, "Clear", COLOR_GREY, self.clear_product_form).pack(side="left")

        self.product_table = make_table(page, ("ID", "Name", "Price", "Stock"),
                                        (60, 380, 120, 120))
        # when the user clicks a row, fill the form with that row
        self.product_table.bind("<<TreeviewSelect>>", self.on_select_product)

    def refresh_products(self):
        fill_table(self.product_table, get_products())

    def clear_product_form(self):
        self.p_name.delete(0, tk.END)
        self.p_price.delete(0, tk.END)
        self.p_stock.delete(0, tk.END)
        self.selected_product_id = None

    def read_product_form(self):
        """Reads and checks the form. Returns (name, price, stock) or None if wrong."""
        name = self.p_name.get().strip()
        if name == "":
            messagebox.showwarning("Missing", "Please enter a product name.")
            return None
        try:
            price = float(self.p_price.get())
            stock = int(self.p_stock.get())
        except ValueError:
            messagebox.showwarning("Wrong input", "Price must be a number and stock must be a whole number.")
            return None
        if price < 0 or stock < 0:
            messagebox.showwarning("Wrong input", "Price and stock cannot be negative.")
            return None
        return name, price, stock

    def on_add_product(self):
        data = self.read_product_form()
        if data is None:
            return
        add_product(data[0], data[1], data[2])
        self.clear_product_form()
        self.refresh_all()

    def on_select_product(self, event):
        selected = self.product_table.selection()
        if len(selected) == 0:
            return
        values = self.product_table.item(selected[0])["values"]
        self.selected_product_id = values[0]
        self.p_name.delete(0, tk.END)
        self.p_price.delete(0, tk.END)
        self.p_stock.delete(0, tk.END)
        self.p_name.insert(0, values[1])
        self.p_price.insert(0, values[2])
        self.p_stock.insert(0, values[3])

    def on_update_product(self):
        if self.selected_product_id is None:
            messagebox.showinfo("Select", "Click a product in the table first.")
            return
        data = self.read_product_form()
        if data is None:
            return
        update_product(self.selected_product_id, data[0], data[1], data[2])
        self.clear_product_form()
        self.refresh_all()

    def on_delete_product(self):
        if self.selected_product_id is None:
            messagebox.showinfo("Select", "Click a product in the table first.")
            return
        if not messagebox.askyesno("Confirm", "Delete this product?"):
            return
        ok, message = delete_product(self.selected_product_id)
        messagebox.showinfo("Result", message)
        self.clear_product_form()
        self.refresh_all()

    # ---------------- CUSTOMERS PAGE ----------------
    def build_customer_page(self, page):
        form = make_card(page)
        form.pack(fill="x")

        fields = tk.Frame(form, bg=COLOR_CARD)
        fields.pack(anchor="w")
        self.c_name = make_field(fields, "Customer name", 30, 0)
        self.c_phone = make_field(fields, "Phone", 20, 1)

        buttons = tk.Frame(form, bg=COLOR_CARD)
        buttons.pack(anchor="w", pady=(14, 0))
        make_button(buttons, "Add", COLOR_BLUE, self.on_add_customer).pack(side="left", padx=(0, 8))
        make_button(buttons, "Update", COLOR_GREEN, self.on_update_customer).pack(side="left", padx=(0, 8))
        make_button(buttons, "Delete", COLOR_RED, self.on_delete_customer).pack(side="left", padx=(0, 8))
        make_button(buttons, "Clear", COLOR_GREY, self.clear_customer_form).pack(side="left")

        self.customer_table = make_table(page, ("ID", "Name", "Phone"), (60, 380, 240))
        self.customer_table.bind("<<TreeviewSelect>>", self.on_select_customer)

    def refresh_customers(self):
        fill_table(self.customer_table, get_customers())

    def clear_customer_form(self):
        self.c_name.delete(0, tk.END)
        self.c_phone.delete(0, tk.END)
        self.selected_customer_id = None

    def on_add_customer(self):
        name = self.c_name.get().strip()
        phone = self.c_phone.get().strip()
        if name == "":
            messagebox.showwarning("Missing", "Please enter a customer name.")
            return
        add_customer(name, phone)
        self.clear_customer_form()
        self.refresh_all()

    def on_select_customer(self, event):
        selected = self.customer_table.selection()
        if len(selected) == 0:
            return
        values = self.customer_table.item(selected[0])["values"]
        self.selected_customer_id = values[0]

        # We read name and phone from the DATABASE, not from the table.
        # The table turns a phone like 0123 into the number 123 (loses the 0).
        for customer in get_customers():
            if customer[0] == self.selected_customer_id:
                self.c_name.delete(0, tk.END)
                self.c_phone.delete(0, tk.END)
                self.c_name.insert(0, customer[1])
                self.c_phone.insert(0, customer[2])

    def on_update_customer(self):
        if self.selected_customer_id is None:
            messagebox.showinfo("Select", "Click a customer in the table first.")
            return
        name = self.c_name.get().strip()
        if name == "":
            messagebox.showwarning("Missing", "Please enter a customer name.")
            return
        update_customer(self.selected_customer_id, name, self.c_phone.get().strip())
        self.clear_customer_form()
        self.refresh_all()

    def on_delete_customer(self):
        if self.selected_customer_id is None:
            messagebox.showinfo("Select", "Click a customer in the table first.")
            return
        if not messagebox.askyesno("Confirm", "Delete this customer?"):
            return
        ok, message = delete_customer(self.selected_customer_id)
        messagebox.showinfo("Result", message)
        self.clear_customer_form()
        self.refresh_all()

    # ---------------- SALES PAGE ----------------
    def build_sales_page(self, page):
        form = make_card(page)
        form.pack(fill="x")

        fields = tk.Frame(form, bg=COLOR_CARD)
        fields.pack(anchor="w")
        self.s_customer = make_dropdown(fields, "Customer", 24, 0)
        self.s_product = make_dropdown(fields, "Product", 32, 1)
        self.s_qty = make_field(fields, "Quantity", 10, 2)

        buttons = tk.Frame(form, bg=COLOR_CARD)
        buttons.pack(anchor="w", pady=(14, 0))
        make_button(buttons, "Sell", COLOR_GREEN, self.on_sell).pack(side="left")

        self.sales_table = make_table(
            page, ("ID", "Date", "Customer", "Product", "Qty", "Total"),
            (50, 140, 160, 180, 60, 100))

    def refresh_dropdowns(self):
        # Each dropdown item looks like:  "3 - Rahul"  (id - name)
        customer_list = []
        for c in get_customers():
            customer_list.append(str(c[0]) + " - " + c[1])
        self.s_customer["values"] = customer_list

        product_list = []
        for p in get_products():
            product_list.append(str(p[0]) + " - " + p[1] + " (stock " + str(p[3]) + ")")
        self.s_product["values"] = product_list

        # clear whatever was chosen before
        self.s_customer.set("")
        self.s_product.set("")

    def refresh_sales(self):
        fill_table(self.sales_table, get_sales())

    def on_sell(self):
        if self.s_customer.get() == "" or self.s_product.get() == "":
            messagebox.showwarning("Missing", "Please choose a customer and a product.")
            return
        try:
            quantity = int(self.s_qty.get())
        except ValueError:
            messagebox.showwarning("Wrong input", "Quantity must be a whole number.")
            return

        # The text is "3 - Rahul". Split at " - " and take the first part = the id
        customer_id = int(self.s_customer.get().split(" - ")[0])
        product_id = int(self.s_product.get().split(" - ")[0])

        ok, message = make_sale(customer_id, product_id, quantity)
        if ok:
            messagebox.showinfo("Done", message)
            self.s_qty.delete(0, tk.END)
            self.refresh_all()
        else:
            messagebox.showwarning("Cannot sell", message)

    # ---------------- refresh everything ----------------
    def refresh_all(self):
        self.refresh_products()
        self.refresh_customers()
        self.refresh_sales()
        self.refresh_dropdowns()
        self.refresh_dashboard()


# ============================================================
# PART 3 - START THE PROGRAM
# ============================================================

if __name__ == "__main__":
    create_tables()            # make sure the tables exist
    root = tk.Tk()             # create the main window
    app = ERPApp(root)         # build our ERP inside it
    root.mainloop()            # keep the window open until closed
