import os
import random
import string

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from sudoku import createGame, printSudoku, string_to_puzzle, puzzle_to_string

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
db = SQL("sqlite:///games.db")


@app.route("/")
@login_required
def index():
    """Home page for resuming previous game or starting new game"""
    return render_template("index.html")


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

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Generate new puzzle"""
    if request.method == "POST":
        difficulty = request.form.get("difficulty")
        if not difficulty:
            return apology("Difficult not found", 400)

        puzzle = createGame(difficulty)
        puzzle = puzzle_to_string(puzzle)

        db.execute(
            "INSERT INTO puzzles (start, user_id, difficulty, puzzle)\
            VALUES(:start, :user_id, :difficulty, :puzzle)",
            start=datetime.now(),
            user_id=session['user_id'],
            difficulty=difficulty,
            puzzle=puzzle
        )

        game_id = db.execute(
                        "SELECT id FROM puzzles WHERE user_id = :user_id ORDER BY id DESC LIMIT 1",
                        user_id=session['user_id']
        )

        # TODO if there has not been a game created before the resume game function fails to find a previous_game_id
        db.execute(
            "UPDATE users SET previous_game_id = :game_id WHERE id = :user_id",
            game_id=game_id[0]['id'], user_id=session['user_id']
        )
        flash("New puzzle has been created")
        return redirect("/")

    # Got to route from GET (link)
    else:
        return render_template("create.html")

@app.route("/history")
@login_required
def history():
    """Show history of puzzles"""
    rows = db.execute(
        "SELECT start, finish, difficulty, id FROM puzzles WHERE user_id = :user_id",
        user_id=session['user_id']
    )

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
        session['user_id'] = rows[0]['id']
        session['previous_game_id'] = rows[0]['previous_game_id']

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

        flash("Welcome aboard!")
        return redirect("/")

    # Reached route via GET (clicked on link)
    else:
        return render_template("register.html")

@app.route("/sudoku", defaults={'game_id':'none'}, methods=["GET", "POST"])
@app.route("/sudoku/<int:game_id>", methods=["GET", "POST"])
@login_required
def sudoku(game_id):
    """Main function for displaying games"""
    if request.method == "POST":
        new_puzzle = []
        for i in range(81):
            cell = request.form.get("cell_" + str(i))
            new_puzzle.append(cell)

        new_puzzle = " ".join(new_puzzle)

        db.execute("UPDATE puzzles SET puzzle = :new_puzzle WHERE user_id = :user_id AND id = :game_id",
                new_puzzle=new_puzzle, user_id=session['user_id'], game_id=session['previous_game_id']
        )

        puzzle = string_to_puzzle(new_puzzle)

        flash("Puzzle has been saved")
        return render_template("sudoku.html", game_id=game_id, puzzle=puzzle)

    else:
        if game_id == 'none':
            game_id = session['previous_game_id']

        db.execute(
            "UPDATE users SET previous_game_id = :game_id WHERE id = :user_id",
            game_id=game_id, user_id=session['user_id']
        )

        puzzle = db.execute("SELECT puzzle FROM puzzles WHERE id = :game_id AND user_id = :user_id",
                            game_id=game_id, user_id=session['user_id']
        )

        puzzle = string_to_puzzle(puzzle[0]['puzzle'])

        return render_template("sudoku.html", game_id=game_id, puzzle=puzzle)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
