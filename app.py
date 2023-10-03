import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///student.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

    return render_template("index.html")

@app.route("/option1")
@login_required
def option1():

    return render_template("option1.html")

@app.route("/option2")
@login_required
def option2():

    return render_template("option2.html")
@app.route("/option3")
@login_required
def option3():

    return render_template("option3.html")


@app.route("/thehut")
@login_required
def thehut():
    return render_template("thehut.html")


@app.route("/end")
@login_required
def end():
    return render_template("end.html")

@app.route("/face")
@login_required
def face():
    return render_template("face.html")

@app.route("/theclue", methods=["GET", "POST"])
@login_required
def theclue():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("answer"):
            return apology("insert answer", 403)

    true = "alohomora"
    answer = request.form.get("answer")

    if true == answer:
        return render_template("thehut.html")
    else:
        return apology("wrong answer", 403)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not symbol:
            return apology("Missing Symbol")

        elif not lookup(symbol):
            return apology("Invalid Symbol")

        elif not shares:
            return apology("Missing Shares")

        elif not shares.isdigit():
            return apology("Invalid Shares")

        else:
            quote = lookup(symbol)
            total = float(shares) * quote["price"]
            rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
            cash = rows[0]["cash"]

        if cash < total:
            return apology("Can't Afford")
        else:
            db.execute("INSERT INTO action(symbol, name, shares, price, user_id, total, action) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       quote["symbol"], quote["name"], shares, quote["price"], session["user_id"], float(shares) * quote["price"], "buy")
            db.execute("UPDATE users SET cash = cash - ? WHERE id = ? ", total, session["user_id"])

            flash("bought!")
            return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT * FROM action WHERE user_id = ?", session["user_id"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide the student name", 403)

        # Ensure password was submitted
        elif not request.form.get("house"):
            return apology("choose your house", 403)

        # Query database for username
        db.execute("INSERT INTO students (student, house) VALUES(?, ?)", request.form.get("username"), request.form.get("house"))
        rows = db.execute("SELECT * FROM students WHERE student = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        #if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            #return apology("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        companysymbol = request.form.get("symbol")

        if not companysymbol:
            return apology("Invalid Input")

        elif not lookup(companysymbol):
            return apology("Invalid Symbol")
        else:
            quote = lookup(companysymbol)
            return render_template("quoted.html", name=quote["name"], symbol=quote["symbol"], price=usd(quote["price"]))
    else:

        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        student = request.form.get("username")
        house = request.form.get("house")

        if not student or not house:
            return apology("Invalid Input")

        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", student, house)
        except:
            return apology("username already exists")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash("registered!")
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    symbolcheck = db.execute(
        "SELECT symbol, SUM(shares) AS shares FROM action WHERE user_id = ? GROUP BY symbol", session["user_id"])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        totalshares = db.execute(
            "SELECT SUM(shares) AS shares FROM action WHERE user_id = ? AND symbol = ? GROUP BY symbol", session["user_id"], symbol)
        total = totalshares[0]["shares"]

        if not symbol:
            return apology("Missing Symbol")

        elif not shares:
            return apology("Missing Shares")

        elif int(shares) > total:
            return apology("Too Many Shares")

        else:
            quote = lookup(symbol)
            total = float(shares) * quote["price"]
            rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
            session["user_cash"] = rows[0]["cash"]

        if session["user_cash"] < total:
            return apology("Can't Afford")
        else:
            negativeshares = int(shares) * -1
            db.execute("INSERT INTO action(symbol, name, shares, price, user_id, total, action) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       quote["symbol"], quote["name"], negativeshares, quote["price"], session["user_id"], float(shares) * quote["price"], "sell")
            db.execute("UPDATE users SET cash = cash + ? WHERE id = ? ", total, session["user_id"])

            flash("Sold!")
            return redirect("/")

    else:
        return render_template("sell.html", symbolcheck=symbolcheck)


@app.route("/changepassword", methods=["GET", "POST"])
def change():
    """Register user"""
    if request.method == "POST":
        newpassword = request.form.get("newpassword")
        confirmation = request.form.get("confirmation")

        if not newpassword or not confirmation:
            return apology("Invalid Input")

        elif newpassword != confirmation:
            return apology("Passwords do not match")
        else:
            password_hash = generate_password_hash(newpassword, method='pbkdf2:sha256', salt_length=8)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", password_hash, session["user_id"])

        flash("Password Changed!")
        return redirect("/")

    else:
        return render_template("changepassword.html")