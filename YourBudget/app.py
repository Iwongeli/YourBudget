from cs50 import SQL
from flask import Flask
from flask import flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

from helpers import login_required, lookforspecial

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///yourwallet.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()
    error = None

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = 'Invalid username and/or password.'
            return render_template("register.html", error=error)

        # Ensure username is not in use
        names = db.execute("SELECT username FROM users")
        if next((name for name in names if name["username"] == request.form.get("username")), None):
            error = 'User allready exist.'
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif len(request.form.get("password")) < 6:
            error = 'password is to short.'
            return render_template("register.html", error=error)

        # Ensure password and corfirmation are the same.
        elif not request.form.get("password") == request.form.get("confirmation"):
            error = 'passwords are different.'
            return render_template("register.html", error=error)

        # Ensure there are no special characters or spaces in username or password.
        elif lookforspecial(request.form.get("username")):
            error = 'Dont use special characters or spaces for login or password.'
            return render_template("register.html", error=error)

        elif lookforspecial(request.form.get("password")):
            error = 'Dont use special characters or spaces for login or password.'
            return render_template("register.html", error=error)

        # Add user to database
        password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), password)
        error = "succesfully registered"
        return render_template("register.html", error=error)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    error = None
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = 'Invalid login and/or password.'
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = 'Invalid login and/or password.'
            return render_template("login.html", error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = 'Invalid login and/or password.'
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    error = None
    # Get today date for form
    today_date = date.today()

    # Get list of categories
    categories = db.execute("SELECT category_type, id FROM categories WHERE users_id=? ORDER BY id", session["user_id"])

    if request.method == "POST":
        print(request.form.get("c_select"))

        if request.form.get("c_select") == None:
            error = 'First declare category in "categories".'
            return render_template("index.html", categories=categories, error=error, today_date=today_date)


        # Check if all necesery informations provided
        if not request.form.get("name") or not request.form.get("value") or not request.form.get("quantity") or not request.form.get("c_select") :
            error = 'Fill at least name value and quantity, select operation type and category.'
            return render_template("index.html", categories=categories, error=error, today_date=today_date)


        # Chceck if values are numbers
        try:
            # Get total by multiplying value * quantity
            value = request.form.get("value")
            for i in value:
                if i == ",":
                    value[i] = "."

            total = float(value) * float(request.form.get("quantity"))
            total = round(total, 2)
        except:
            error = 'provide value and quantity as numbers'
            return render_template("index.html", categories=categories, error=error, today_date=today_date)


        # Get selected category id
        category = db.execute("SELECT id FROM categories WHERE users_id=? AND category_type=?", session["user_id"], request.form.get("c_select"))[0]['id']

        # Get operation type
        operation_type = int(request.form.get("inlineRadioOptions"))

        # Check
        print(session["user_id"], request.form.get("name"), float(request.form.get("value")), float(request.form.get("quantity")), total, category, operation_type, request.form.get("date"), request.form.get("text"))

        # Add record to database
        db.execute("INSERT INTO operations (operation_user, title, value, quantity, total, category_id, operation_type, operation_date, note, external_link) VALUES (?,?,?,?,?,?,?,?,?,?)", session["user_id"], request.form.get("name"), float(request.form.get("value")), float(request.form.get("quantity")), total, category, operation_type, request.form.get("date"), request.form.get("text"), request.form.get("external_link"))

        # Add total to category value
        if operation_type == 0:
            category_value = -total + db.execute("SELECT category_value FROM categories WHERE users_id=? AND id=?", session["user_id"], category)[0]['category_value']
        else:
            category_value = total + db.execute("SELECT category_value FROM categories WHERE users_id=? AND id=?", session["user_id"], category)[0]['category_value']
        db.execute("UPDATE categories SET category_value=? WHERE users_id=? AND id=?",category_value, session["user_id"], category)

        # Prompt succes
        error = 'record has been added to database.'
        return render_template("index.html", categories=categories, error=error, today_date=today_date)

    # Get method
    return render_template("index.html", categories=categories, error=error, today_date=today_date)


@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    """Show available categories"""

    if request.method == "POST":
        # Add category
        db.execute("INSERT INTO categories (users_id, category_type) VALUES (?, ?)", session["user_id"], request.form.get("category_name"))
        categories = db.execute("SELECT category_type, id FROM categories WHERE users_id=? ORDER BY id", session["user_id"])
        return render_template("categories.html", categories=categories)
    # prompt categorie
    try:
        categories = db.execute("SELECT category_type, id FROM categories WHERE users_id=? ORDER BY id", session["user_id"])
    except:
        categories = ["Null"]
    return render_template("categories.html", categories=categories)

@app.route("/categories_del/<id>", methods=["POST"])
@login_required
def categories_del(id):
    # Delete category with button
    db.execute("DELETE FROM operations WHERE operation_user=? AND category_id=?", session["user_id"], id)
    db.execute("DELETE FROM categories WHERE users_id=? AND id=?", session["user_id"], id)
    try:
        categories = db.execute("SELECT category_type, id FROM categories WHERE users_id=? ORDER BY id", session["user_id"])
    except:
        categories = ["Null"]
    return render_template("categories.html", categories=categories)


@app.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    """Show statistics of transactions"""

    sp_labels_list = []
    sp_total_list = []
    er_labels_list = []
    er_total_list = []
    ac_labels_list = []
    ac_total_list = []


    if request.method == "POST":
        # Look for date if provided for filter else get far enough date
        date_from = request.form.get("date_from")
        date_to = request.form.get("date_to")
        if not date_from:
            date_from = '2000-01-01'

        if not date_to:
            date_to = '2099-01-01'

        # Take records including
        ac_records = db.execute("SELECT total, operation_date, operation_type FROM operations WHERE operation_user=? AND operation_date BETWEEN ? AND ? ORDER BY operation_date", session["user_id"], date_from, date_to)
        sp_records = db.execute("SELECT SUM(total), category_type FROM categories INNER JOIN operations ON categories.id = operations.category_id WHERE operation_user=? AND operation_type=0 AND operation_date BETWEEN ? AND ? GROUP BY category_id", session["user_id"], date_from, date_to)
        er_records = db.execute("SELECT SUM(total), category_type FROM categories INNER JOIN operations ON categories.id = operations.category_id WHERE operation_user=? AND operation_type=1 AND operation_date BETWEEN ? AND ? GROUP BY category_id", session["user_id"], date_from, date_to)
    else:
        ac_records = db.execute("SELECT total, operation_date, operation_type FROM operations WHERE operation_user=? AND operation_date ORDER BY operation_date", session["user_id"])
        sp_records = db.execute("SELECT SUM(total), category_type FROM categories INNER JOIN operations ON categories.id = operations.category_id WHERE operation_user=? AND operation_type=0 GROUP BY category_id", session["user_id"])
        er_records = db.execute("SELECT SUM(total), category_type FROM categories INNER JOIN operations ON categories.id = operations.category_id WHERE operation_user=? AND operation_type=1 GROUP BY category_id", session["user_id"])

    for record in sp_records:
        sp_labels_list.append(record['category_type'])
        sp_total_list.append(record['SUM(total)'])

    for record in er_records:
        er_labels_list.append(record['category_type'])
        er_total_list.append(record['SUM(total)'])

    acumulation = 0
    prev_date = 0
    balance = [0, 0, 0]

    for record in ac_records:
        if record['operation_date'] == prev_date:
            if record['operation_type'] == 1:
                balance[1] = balance[1] + record['total']
                acumulation = acumulation + record['total']
            else:
                balance[2] = balance[2] + record['total']
                acumulation = acumulation - record['total']
            ac_total_list[-1] = acumulation
        else:
            if record['operation_type'] == 1:
                balance[1] = balance[1] + record['total']
                acumulation = acumulation + record['total']
            else:
                balance[2] = balance[2] + record['total']
                acumulation = acumulation - record['total']
            ac_labels_list.append(record['operation_date'])
            ac_total_list.append(acumulation)
            prev_date = record['operation_date']
    balance[0] = acumulation

    return render_template("statistics.html", balance=balance, ac_total_list=ac_total_list, ac_labels_list=ac_labels_list, er_labels_list=er_labels_list, er_total_list=er_total_list, sp_labels_list=sp_labels_list, sp_total_list=sp_total_list)


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of transactions"""
    # Get list of categories
    categories = db.execute("SELECT category_type, id FROM categories WHERE users_id=? ORDER BY id", session["user_id"])
    date_to = None
    date_from = None

    if request.method == "POST":

        date_from = request.form.get("date_from")
        date_to = request.form.get("date_to")
        if not date_from:
            date_from = '2020-01-01'

        if not date_to:
            date_to = '2025-01-01'
        if request.form.get("c_select") == "ANY":
            records = db.execute("SELECT * FROM operations INNER JOIN categories ON operations.category_id = categories.id WHERE operation_user=? AND operation_date BETWEEN ? AND ? ORDER BY operation_date", session["user_id"], date_from, date_to)
        else:
            # list categories
            category = db.execute("SELECT id FROM categories WHERE users_id=? AND category_type=?", session["user_id"], request.form.get("c_select"))[0]['id']

            # list records join categories
            records = db.execute("SELECT * FROM operations INNER JOIN categories ON operations.category_id = categories.id WHERE operation_user=? AND category_id=? AND operation_date BETWEEN ? AND ? ORDER BY operation_date", session["user_id"], category, date_from, date_to)

        for record in records:
            if record['operation_type'] == 0:
                record['operation_type'] = 'Expence'
            else:
                record['operation_type'] = 'Income'

        return render_template("history.html", categories=categories, records=records, date_from=date_from, date_to=date_to)

    # list records join categories
    records = db.execute("SELECT * FROM operations INNER JOIN categories ON operations.category_id = categories.id WHERE operation_user=? ORDER BY operation_date DESC", session["user_id"])
    for record in records:
        if record['operation_type'] == 0:
            record['operation_type'] = 'Expence'
        else:
            record['operation_type'] = 'Income'

    return render_template("history.html", categories=categories, records=records)


@app.route("/history/delete/<id>", methods=["POST"])
@login_required
def history_delete(id):
    """delete transactions"""
    # Get dataset
    category = db.execute("SELECT category_id FROM operations WHERE operation_user=? AND operation_id=?", session["user_id"], id)[0]['category_id']
    operation_type = db.execute("SELECT operation_type FROM operations WHERE operation_user=? AND operation_id=?", session["user_id"], id)[0]['operation_type']
    total = db.execute("SELECT total FROM operations WHERE operation_user=? AND operation_id=?", session["user_id"], id)[0]['total']
    if operation_type == 0:
        category_value = total + db.execute("SELECT category_value FROM categories WHERE users_id=? AND id=?", session["user_id"], category)[0]['category_value']
    else:
        category_value = -total + db.execute("SELECT category_value FROM categories WHERE users_id=? AND id=?", session["user_id"], category)[0]['category_value']

    # Remove operation from records
    db.execute("UPDATE categories SET category_value=? WHERE users_id=? AND id=?",category_value, session["user_id"], category)
    db.execute("DELETE FROM operations WHERE operation_user=? AND operation_id=?", session["user_id"], id)
    return redirect("/history")

@app.route("/history/explore/<id>", methods=["POST"])
@login_required
def history_explore(id):
    """Explore further transactions"""
    link = None

    data = db.execute("SELECT * FROM operations INNER JOIN categories ON operations.category_id = categories.id WHERE operation_user=? AND operation_id=?", session["user_id"], id)[0]
    if len(data['external_link']) > 2:
        link = True
    if data['operation_type'] == 0:
        data['operation_type'] = 'Expence'
    else:
        data['operation_type'] = 'Income'
    return render_template("history_explore.html", categories=categories, data=data, link=link)
