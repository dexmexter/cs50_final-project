import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # a list of symbols owned for the current user
    symbols = db.execute(
        "SELECT DISTINCT symbol FROM transactions WHERE user_id = :user_id",
        user_id=session['user_id'])

    # available cash remaining
    cash = db.execute(
        "SELECT cash FROM users WHERE id = :id",
        id=session['user_id']
    )[0]['cash']

    # will be a list of dictionaies for index.html
    rows = []

    # sum of cash and the current owned value of all stock shares
    total = cash

    for symbol in symbols:
        # find the number of shares owned for this symbol
        shares = db.execute(
            "SELECT sum(shares) FROM transactions WHERE symbol = :symbol",
            symbol=symbol['symbol']
        )[0]['sum(shares)']

        # check if any of this share is currently owned
        if shares > 0:
            # create a new dictionary for the list of rows
            symbol_info = lookup(symbol['symbol'])

            row = {
                'symbol': symbol_info['symbol'],
                'name': symbol_info['name'],
                'price': usd(symbol_info['price']),
                'share_total': usd(symbol_info['price'] * shares),
                'shares': shares
            }

            rows.append(row)

            # increment total
            total += shares * symbol_info['price']

    return render_template("index.html", cash=usd(cash), total=usd(total), rows=rows)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol_info = lookup(request.form.get("symbol"))
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Please enter an integer.", 400)
        cash = db.execute(
            "SELECT cash FROM users WHERE id = :id",
            id=session['user_id']
        )[0]['cash']

        # invalid symbol
        if not symbol_info:
            # TODO, add if jinja to buy.html
            return apology("Symbol not found", 400)

        # incorrect share
        elif shares < 1:
            return apology("Incorrect amount of shares", 400)

        # process transaction
        else:

            # update cash to reflect new price
            cash -= (symbol_info['price'] * shares)

            # Apologize if user does not have enough cash for purchase
            if cash < 0:
                # TODO, add if jinja to buy.html that also returns current
                # ammount of cash on hand as well as how much they are trying
                # to spend.
                return apology("Not enough cash", 400)

            else:
                # add purchase transaction
                db.execute(
                    "INSERT INTO transactions (time, user_id, symbol, price, shares)\
                    VALUES(:time,:user_id,:symbol,:price, :shares)",
                    time=datetime.now(),
                    user_id=session['user_id'],
                    symbol=symbol_info['symbol'],
                    price=symbol_info['price'],
                    shares=shares
                )

                # update cash amount to reflect money spent
                db.execute(
                    "UPDATE users SET cash = :cash WHERE id = :user_id",
                    cash=cash, user_id=session['user_id']
                )

                # redirect to home page
                flash(
                    "Bought {} share(s) of {}".format(shares, symbol_info['symbol'])
                )
                return redirect("/")

    # Got to route from GET
    else:
        return render_template("buy.html")


@app.route("/change", methods=["GET", "POST"])
def change():
    """Change Password"""
    # Reached route via POST (submitting form via POST)
    if request.method == "POST":

        hashed_pswd = generate_password_hash(request.form.get("password"))
        old_hash = db.execute("SELECT hash FROM users WHERE id = :user_id", user_id=session['user_id'])[0]

        print("old_hash:", old_hash)

        # Username submitted?
        if not request.form.get("old_password"):
            return apology("must provide current password", 400)

        # Old password is correct?
        elif not check_password_hash(old_hash["hash"], request.form.get("old_password")):
            return apology("Current password incorrect", 400)

        # Password submitted?
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Password equals confirmation?
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Add new password to database
        db.execute(
            "UPDATE users SET hash = :hashed_pswd WHERE id = :user_id",
            hashed_pswd=hashed_pswd, user_id=session['user_id']
        )

        # Redirect to home page
        flash("Password changed")
        return logout()

    # Reached route via GET (clicked on link)
    else:
        return render_template("change.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username")

    print("username:", username)

    if db.execute("SELECT username FROM users WHERE username = :username", username=username):
        print("Username already exists")
        return jsonify(False)

    else:
        print("username is available")
        return jsonify(True)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute(
        "SELECT time, symbol, price, shares FROM transactions WHERE user_id = :user_id",
        user_id=session['user_id']
    )

    for row in rows:
        row['price'] = usd(row['price'])

    return render_template("history.html", rows=rows)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
    # Reached route via POST
    if request.method == "POST":

        symbol = request.form.get("symbol")
        symbol_info = lookup(symbol)

        if not symbol_info:
            return apology("Not a valid symbol", 400)

        else:
            # Render page with additional message for the quoted stock price
            return render_template("quoted.html", symbol_info=symbol_info, usd=usd(symbol_info['price']))

    # Reached route via GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Reached route via POST (submitting form via POST)
    if request.method == "POST":

        # Username submitted?
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Password submitted?
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Password equals confirmation?
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must provide password", 400)

        # Check if username in database
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        if len(rows) != 0:
            return apology("Username already exists", 400)

        # Add username and password to database
        username = request.form.get("username")
        hashed_pswd = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO 'users' ('username','hash') VALUES (:username, :hash)",
                   username=username, hash=hashed_pswd)

        # Redirect to home page
        # TODO send POST to Login with entered information
        flash("Welcome aboard!")
        return redirect("/")

    # Reached route via GET (clicked on link)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    symbols_owned = db.execute(
        "SELECT DISTINCT symbol FROM transactions WHERE user_id = :user_id",
        user_id=session['user_id']
    )

    if request.method == "POST":
        symbol_sold = request.form.get("symbol")
        symbol_info = lookup(symbol_sold)

        shares_sold = int(request.form.get("shares"))

        shares_owned = db.execute(
            "SELECT sum(shares) FROM transactions WHERE symbol = :symbol",
            symbol=symbol_sold
        )[0]['sum(shares)']

        # form missing symbol or shares
        if not symbol_sold or not shares_sold:
            return apology("Missing data, please resubmit form.", 400)

        # trying to sell too many shares
        elif shares_sold > shares_owned:
            return apology(
                "You can't sell {} of {}, you own {}".format(
                    shares_sold, symbol_sold, shares_owned
                ), 400
            )

        else:
            # add new transaction to db
            db.execute(
                "INSERT INTO transactions (time, user_id, symbol, price, shares)\
                VALUES(:time,:user_id,:symbol,:price, :shares)",
                time=datetime.now(),
                user_id=session['user_id'],
                symbol=symbol_info['symbol'],
                price=symbol_info['price'],
                shares=-shares_sold
            )

            # send user to home page
            return redirect("/")

    else:
        return render_template("sell.html", symbols_owned=symbols_owned)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
