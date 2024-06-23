from flask import Flask, request, render_template
from tokens import OAI_TOKEN
import base64, requests, re

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

@app.route("/read_receipt", methods=['POST'])
def read_receipt():
    file = request.files['file']
    base64_image = base64.b64encode(file.read()).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OAI_TOKEN}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Compile the information on this receipt into a csv file with the columns Product, Price, and Category, where the possible Categories are Food, Household Essentials, Health and Beauty, Electronics, Clothing, Home and Furniture, Toys and Games, Office Supplies, Outdoor, Automotive, Baby, and Pet."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    message = response.json()['choices'][0]['message']['content']
    
    csvData =  re.search(r'```csv(.*)```', message, re.DOTALL)[0]

    return {"content": csvData}
    # return {}

if __name__ == '__main__':
    app.run()