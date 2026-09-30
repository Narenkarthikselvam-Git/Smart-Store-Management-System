from flask import Flask, render_template, request, redirect
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)

def create_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, price INTEGER, quantity INTEGER, category TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, phone TEXT, password TEXT, address TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT, customer_email TEXT,
        items TEXT, total INTEGER, address TEXT,
        date TEXT, status TEXT DEFAULT 'New'
    )""")

    conn.commit()
    conn.close()


# CUSTOMER PAGES
@app.route('/')
def home():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("index.html", products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return redirect('/')
        else:
            error = "Invalid email or password"
    return render_template("login.html", error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name  = request.form['last_name']
        email      = request.form['email']
        phone      = request.form['phone']
        password   = request.form['password']
        address    = request.form['address']
        name = first_name + ' ' + last_name
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email=?", (email,))
        existing = cursor.fetchone()
        if existing:
            error = "Email already registered. Please login."
            conn.close()
        else:
            cursor.execute(
                "INSERT INTO customers (name, email, phone, password, address) VALUES (?, ?, ?, ?, ?)",
                (name, email, phone, password, address)
            )
            conn.commit()
            conn.close()
            return redirect('/login')
    return render_template("login.html", error=error)


# CHECKOUT — auto adds customer if not already exists
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        customer_name  = request.form['customer_name']
        customer_email = request.form['customer_email']
        address        = request.form['address']
        phone          = request.form.get('phone', '')
        items          = request.form['items']
        total          = request.form['total']
        date           = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Save the order
        cursor.execute(
            "INSERT INTO orders (customer_name, customer_email, items, total, address, date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (customer_name, customer_email, items, total, address, date, 'New')
        )

        # Check if customer already exists by email
        cursor.execute("SELECT id FROM customers WHERE email=?", (customer_email,))
        existing = cursor.fetchone()

        # If not, add them automatically
        if not existing:
            cursor.execute(
                "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
                (customer_name, customer_email, phone, address)
            )

        conn.commit()
        conn.close()
        return render_template("order_success.html", name=customer_name)
    return render_template("checkout.html")


# ADMIN DASHBOARD
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total) FROM orders")
    total_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT * FROM products WHERE quantity <= 10 ORDER BY quantity ASC")
    low_stock = cursor.fetchall()
    conn.close()
    return render_template(
        "admin_dashboard.html",
        orders=orders,
        customer_count=customer_count,
        product_count=product_count,
        total_orders=total_orders,
        total_revenue=total_revenue,
        low_stock=low_stock
    )


# UPDATE ORDER STATUS
@app.route('/update_order_status/<int:id>/<status>')
def update_order_status(id, status):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()
    return redirect('/admin')


# PRODUCTS
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name     = request.form['name']
        price    = request.form['price']
        quantity = request.form['quantity']
        category = request.form.get('category', 'general')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price, quantity, category) VALUES (?, ?, ?, ?)",
            (name, price, quantity, category)
        )
        conn.commit()
        conn.close()
        return redirect('/view_products')
    return render_template("add_product.html")

@app.route('/view_products')
def view_products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    search_query = request.args.get('query')
    if search_query:
        cursor.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + search_query + '%',))
    else:
        cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template(
        "view_products.html",
        products=products,
        search_query=search_query,
        low_stock_threshold=10
    )

@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/view_products')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        name     = request.form['name']
        price    = request.form['price']
        quantity = request.form['quantity']
        category = request.form.get('category', 'general')
        cursor.execute(
            "UPDATE products SET name=?, price=?, quantity=?, category=? WHERE id=?",
            (name, price, quantity, category, id)
        )
        conn.commit()
        conn.close()
        return redirect('/view_products')
    cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    product = cursor.fetchone()
    conn.close()
    return render_template("edit_product.html", product=product)


# CUSTOMERS
@app.route('/customers')
def customers():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    customers_list = cursor.fetchall()
    conn.close()
    return render_template("customers.html", customers=customers_list)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '')
        last_name  = request.form.get('last_name', '')
        name       = (first_name + ' ' + last_name).strip()
        email      = request.form['email']
        phone      = request.form['phone']
        address    = request.form.get('address', '')
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
            (name, email, phone, address)
        )
        conn.commit()
        conn.close()
        return redirect('/customers')
    return render_template("add_customer.html")

@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/customers')


# RUN SERVER
if __name__ == '__main__':
    create_table()
    app.run(debug=True)
