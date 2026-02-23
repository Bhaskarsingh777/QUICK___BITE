from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from io import BytesIO
import base64
import os
import qrcode

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

# ---------------- DATABASE CONFIG ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql://food_bemp_user:JNAkhl4rCjGcyv3gMkOKOQXWi9PW1Fej@dpg-d6e5m3ffte5s73dqsfk0-a/food_bemp"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ---------------- DATABASE SETUP ----------------
def init_db():
    con = get_db_connection()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_email TEXT,
        item TEXT,
        quantity INTEGER,
        address TEXT,
        phone TEXT,
        total_price REAL,
        status TEXT DEFAULT 'Preparing'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        name TEXT,
        message TEXT,
        rating INTEGER
    )
    """)

    con.commit()
    cur.close()
    con.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT name, message, rating FROM reviews ORDER BY id DESC")
    reviews = cur.fetchall()
    cur.close()
    con.close()
    return render_template("index.html", reviews=reviews)

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])

    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        con.commit()
        flash("Signup successful! Please login.")
    except Exception:
        con.rollback()
        flash("Email already exists!")

    cur.close()
    con.close()
    return redirect(url_for("home"))

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    con.close()

    if user and check_password_hash(user[3], password):
        session["user"] = email
        flash("Login successful!")
    else:
        flash("Invalid credentials!")

    return redirect(url_for("home"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for("home"))

# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user" not in session:
        flash("Please login first!")
        return redirect(url_for("home"))

    item = request.form["item"]
    price = float(request.form["price"])
    qty = int(request.form.get("quantity", 1))

    cart = session.get("cart", {})

    if item in cart:
        cart[item]["quantity"] += qty
    else:
        cart[item] = {"price": price, "quantity": qty}

    session["cart"] = cart
    flash("Item added to cart!")
    return redirect(url_for("cart"))

# ---------------- CART ----------------
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect(url_for("home"))

    cart = session.get("cart", {})
    total = sum(v["price"] * v["quantity"] for v in cart.values())
    return render_template("cart.html", cart=cart, total=total)

# ---------------- UPDATE QUANTITY ----------------
@app.route("/update_quantity/<item>/<action>")
def update_quantity(item, action):
    if "user" not in session:
        return redirect(url_for("home"))

    cart = session.get("cart", {})
    if item in cart:
        if action == "increase":
            cart[item]["quantity"] += 1
        elif action == "decrease" and cart[item]["quantity"] > 1:
            cart[item]["quantity"] -= 1

    session["cart"] = cart
    return redirect(url_for("cart"))

# ---------------- REMOVE ITEM ----------------
@app.route("/remove_item/<item>")
def remove_item(item):
    if "user" not in session:
        return redirect(url_for("home"))

    cart = session.get("cart", {})
    cart.pop(item, None)
    session["cart"] = cart
    return redirect(url_for("cart"))

# ---------------- CHECKOUT ----------------
@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect(url_for("home"))

    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("home"))

    total = sum(v["price"] * v["quantity"] for v in cart.values())
    return render_template("checkout.html", total=total)

from io import BytesIO
import base64

@app.route("/payment", methods=["POST"])
def payment():
    if "user" not in session:
        return redirect(url_for("home"))

    session["delivery_address"] = request.form["address"]
    session["delivery_phone"] = request.form["phone"]
    total = float(request.form["total"])

    upi_link = f"upi://pay?pa=9871209052@yapl&pn=Quick Bite&am={total}&cu=INR"

    img = qrcode.make(upi_link)

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()

    return render_template("payment.html", total=total, qr_code=qr_code)

# ---------------- CONFIRM PAYMENT ----------------
@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    if "user" not in session:
        return redirect(url_for("home"))

    cart = session.get("cart", {})
    con = get_db_connection()
    cur = con.cursor()

    for item, info in cart.items():
        cur.execute("""
            INSERT INTO orders
            (user_email, item, quantity, address, phone, total_price)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session["user"],
            item,
            info["quantity"],
            session.get("delivery_address"),
            session.get("delivery_phone"),
            info["price"] * info["quantity"]
        ))

    con.commit()
    cur.close()
    con.close()
    session.pop("cart", None)

    return "<h2>✅ Payment Successful – Order Confirmed</h2>"

# ---------------- TRACK ORDERS ----------------
@app.route("/track_orders")
def track_orders():
    if "user" not in session:
        return redirect(url_for("home"))

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM orders WHERE user_email=%s ORDER BY id DESC", (session["user"],))
    orders = cur.fetchall()
    cur.close()
    con.close()
    return render_template("track_orders.html", orders=orders)

# ---------------- REVIEW ----------------
@app.route("/review", methods=["POST"])
def review():
    name = request.form["name"]
    message = request.form["message"]
    rating = request.form["rating"]

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO reviews (name, message, rating) VALUES (%s, %s, %s)",
                (name, message, rating))
    con.commit()
    cur.close()
    con.close()

    flash("Review submitted successfully!")
    return redirect(url_for("home"))

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials!")
    return render_template("admin_login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    con = get_db_connection()
    cur = con.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()

    cur.execute("SELECT COALESCE(SUM(total_price),0) FROM orders")
    revenue = cur.fetchone()[0]

    cur.close()
    con.close()

    return render_template("admin_dashboard.html",
                           users=users,
                           orders=orders,
                           revenue=revenue)

# ---------------- DELETE USER ----------------
@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    con.commit()
    cur.close()
    con.close()

    return redirect(url_for("admin_dashboard"))

# ---------------- DELETE ORDER ----------------
@app.route("/delete_order/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM orders WHERE id=%s", (order_id,))
    con.commit()
    cur.close()
    con.close()

    return redirect(url_for("admin_dashboard"))

# ---------------- UPDATE ORDER STATUS ----------------
@app.route("/update_status/<int:order_id>", methods=["POST"])
def update_status(order_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    new_status = request.form.get("status")

    con = get_db_connection()
    cur = con.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
    con.commit()
    cur.close()
    con.close()

    return redirect(url_for("admin_dashboard"))

# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)