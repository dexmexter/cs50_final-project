import os
import random
import string

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from random_word import RandomWords
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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

    # will be a list of dictionaries for index.html
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


@app.route("/rps", methods=["GET", "POST"])
@login_required
def rps():
    """Play Rock Paper Scissors"""
    if request.method == "POST":
        user_choice = request.form.get("choice")

        if not user_choice:
            return apology("Could not get selection", 400)

        # Win states for the game
        triangle = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
        valid_choice = list(triangle.keys())
        cpu_choice = random.choice(valid_choice)

        if triangle[user_choice] == cpu_choice:
            flash(f"You picked {user_choice} and your opponent chose {cpu_choice}. You win!")
            return redirect("/")

        elif user_choice == cpu_choice:
            flash(f"You picked {user_choice} and your opponent also chose {cpu_choice}. Tie game!")
            return redirect("/")

        elif triangle[cpu_choice] == user_choice:
            flash(f"You picked {user_choice} and your opponent chose {cpu_choice}. You lose!")
            return redirect("/")

    else:
        return render_template("rps.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
