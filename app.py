import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
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
db = SQL("sqlite:///finance.db")


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
    """Show portfolio of stocks"""
    portfolio = db.execute("SELECT * FROM stocks WHERE user_id = ?", session["user_id"])
    cashDB = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = cashDB[0]["cash"]
    return render_template("index.html", portfolio=portfolio, cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        #Check if stock exists
        item = lookup(request.form.get("symbol").upper())
        if not item:
            return apology("stock not found", 400)
        #Check amount of shares requested
        shares = request.form.get("shares")
        if not shares:
            return apology("no shares inputted", 400)
        try:
            shares = int(shares)
        except ValueError:
            return apology("invalid number of shares", 400)
        if not int(shares) > 0:
            return apology("input more than 0 shares", 400)
        #Buy the shares of the stock
        cashDB = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        cash = cashDB[0]["cash"]
        tradeValue = item["price"] * int(shares)

        if cash < tradeValue:
            return apology("too broke")
        else:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - tradeValue, session["user_id"])

        date = datetime.datetime.now()
        db.execute("INSERT INTO stocks (user_id, symbol, shares, price, date) VALUES (?, ?, ?, ?, ?)", session["user_id"],
                        item['symbol'], int(shares), item['price'], date)

        flash(f"Bought {shares} shares of {item['symbol']}!")
        return redirect("/")
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

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
        item = lookup(request.form.get("symbol").upper())
        if not item:
            return apology("stock not found")

        return render_template("quoted.html", stock={'symbol': item['symbol'], 'price': usd(item['price'])})

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        #check duplicate username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) > 0:
            return apology("user already exists", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Create a new account in the data base, but first hash the password
        passHash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), passHash)
        # Retrieve the ID of the newly inserted user
        user_id = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Log the user in by storing their ID in the session
        session["user_id"] = user_id[0]["id"]

        return redirect("/")
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")
