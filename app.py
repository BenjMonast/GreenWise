from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/carbon")
def carbon():
    return render_template("carbon.html")

@app.route("/manual")
def manual():
    return render_template("manual.html")