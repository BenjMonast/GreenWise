from flask import Flask, request, render_template
from tokens import OAI_TOKEN
import logging

app = Flask(__name__)

@app.route("/")
def index():
    print("sdfsdfsdfs")
    return render_template("index.html")

@app.route("/carbon")
def carbon():
    return render_template("carbon.html")

@app.route("/manual")
def manual():
    return render_template("manual.html")

@app.route("/read_receipt", methods=['POST'])
def read_receipt():
    file = request.files['file']
    return "Hello world"

if __name__ == '__main__':
    app.run()