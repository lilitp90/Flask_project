import os

import requests
from flask import Flask, session, render_template, request, flash, redirect, \
    url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm, ReviewForm

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
create_users_query = "CREATE TABLE IF NOT EXISTS users(" \
                     "user_id SERIAL PRIMARY KEY, " \
                     "username VARCHAR (50), password VARCHAR (100));"
create_reviews_query = "CREATE TABLE IF NOT EXISTS reviews(" \
                       "review_id SERIAL PRIMARY KEY, " \
                       "user_id integer, book VARCHAR(30), " \
                       "rating integer, review VARCHAR (100));"
db.execute(create_users_query)
db.execute(create_reviews_query)
db.commit()


@app.route("/")
def index():
    if session.get("user_id") is None:
        return redirect("/login")
    return render_template("search.html")


@app.route("/signup", methods=["GET", "POST"])
def register():
    try:
        form = RegistrationForm(request.form)
        if request.method == "POST" and form.validate():
            username = form.username.data
            user = db.execute("SELECT * FROM users WHERE username=:username",
                              {"username": username}).fetchone()
            if user:
                flash("The username is already in use, "
                      "please choose another!", "error")
                return redirect(url_for('register'))
            confirm = form.confirm.data
            if confirm != form.password.data:
                flash("Two passwords do not match!", "error")
                return redirect(url_for('register'))
            password = generate_password_hash(form.password.data,
                                              method='sha256')
            db.execute("INSERT INTO users(username, password) "
                       "VALUES (:username, :password)",
                       {"username": username, "password": password})
            db.commit()
            return redirect('/login')
        return render_template("register.html", form=form)
    except Exception as e:
        return str(e)


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        form = LoginForm(request.form)
        if request.method == "POST" and form.validate():
            username = form.username.data
            password = form.password.data
            user = db.execute("SELECT * FROM users WHERE username = "
                              ":username",
                              {'username': username}).fetchone()
            db.commit()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                authenticated_user = check_password_hash(user.password,
                                                         password)
                if not authenticated_user:
                    flash("Username or password is incorrect", "error")
                    return redirect(url_for('login'))

                return redirect("/")
        return render_template('login.html', form=form)
    except Exception as e:
        return str(e)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/booklist", methods=["GET", "POST"])
def search():
    searched = request.form.get("usersinput")
    get_from_db = db.execute("SELECT title, author, isbn FROM books "
                             "JOIN authors USING(author_id) "
                             "WHERE isbn LIKE :usersearch "
                             "OR title LIKE :usersearch "
                             "OR author LIKE :usersearch",
                             {"usersearch": '%{}%'.
                             format(searched)}).fetchall()
    if len(get_from_db) == 0:
        error = "No Results please try again!"
        return render_template("search.html", error=error)
    else:
        return render_template("book_list.html", searched=get_from_db)


@app.route("/details", methods=["GET", "POST"])
def details():
    try:
        form = ReviewForm(request.form)
        selected = request.args.get('selected')
        details = db.execute("SELECT * FROM books "
                             "JOIN authors USING(author_id) "
                             "WHERE isbn=:selected ",
                             {"selected": selected}).fetchall()
        reviewed_user = db.execute("SELECT user_id, book, rating "
                                   "FROM reviews "
                                   "WHERE user_id="
                                   ":user_id and book=:book;",
                                   {"user_id": session["user_id"],
                                    "book": details[0][2]}).fetchone()
        api_key = os.getenv("API_KEY")
        response = requests.get(
            "https://www.goodreads.com/book/review_counts."
            "json",
            params={"key": api_key, "isbns": details[0][1]})
        output = response.json()['books'][0]
        if request.method == "POST":
            if reviewed_user:
                flash("You can't review the same book twice!", "error")
            else:
                rating = form.rating.data
                review = form.review.data

                db.execute("Insert INTO reviews (user_id, book, "
                           "rating, review) VALUES (:user_id, :book, "
                           ":rating, :review);", {
                               "user_id": session["user_id"],
                               "book": details[0][2], "rating": rating,
                               "review": review})
                db.commit()
                flash("Review submitted successfully!", "success")
                return render_template("details.html", details=details,
                                       average_rating=
                                       output['average_rating'],
                                       work_ratings_count=
                                       output['work_ratings_count'])

        return render_template("details.html", details=details, form=form,
                               average_rating=output['average_rating'],
                               work_ratings_count=
                               output['work_ratings_count'],
                               reviewed_user=reviewed_user)
    except Exception:
        return redirect("/")


@app.route("/api/<isbn>")
def create_api(isbn):
    data = db.execute("SELECT * FROM books JOIN authors USING(author_id) "
                      "WHERE isbn=:isbn ",
                      {"isbn": isbn})
    if data.rowcount == 0:
        return jsonify({"Error": "No such book ISBN"}), 404
    else:
        dict_data = dict(data.fetchone().items())
        return jsonify(dict_data)
