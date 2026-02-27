import os
import psycopg2
from flask import Flask, render_template, request, url_for, redirect
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("login.html")
@app.route("/login/")
def hello():
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True)
