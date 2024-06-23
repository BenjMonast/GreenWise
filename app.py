from flask import Flask, request, render_template
from tokens import *
import base64, requests, re, pickle
from emails import read_new_emails

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
@app.route("/read_receipt_email", methods=['POST'])

def read_receipt_email():
    receipt = read_new_emails("somethingnormalai@gmail.com", EMAIL_PASSWORD)
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
                        "type": "text",
                        "text": {
                            "text": receipt
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    message = response.json()['choices'][0]['message']['content']

    csvData = re.search(r'```csv(.*)```', message, re.DOTALL)[0]

    return {"content": csvData}


@app.route("/read_receipt", methods=['POST'])
def read_receipt():
    file = request.files['file']
    base64_image = base64.b64encode(file.read()).decode('utf-8')

    csv_text = None

    url = "https://api.taggun.io/api/receipt/v1/verbose/encoded"

    payload = {
        "image": base64_image,
        "filename": "image.jpg",
        "contentType": "image/jpeg"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apikey": TAGGUN_TOKEN
    }

    response = requests.post(url, json=payload, headers=headers)

    items = []

    for row in response.json()['amounts']:
        text = row['text']
        words = text.split(" ")
        if not (words[0].isnumeric() and len(words[0]) == 9):
            continue

        items.append((words[0], words[-1]))

    with open('redcircle_cache.pkl', 'rb') as f:
        cache = pickle.load(f)
    
    out = []

    for row in items:
        id = row[0]
        if id not in cache:
            json = requests.get(f"https://api.redcircleapi.com/request?api_key={RC_TOKEN}&type=search&search_term={id}").json()
            if "search_results" in json:
                cache[id] = json["search_results"]
            else:
                cache[id] = None

        if cache[id] == None:
            continue

        out.append([cache[id][0]['product']['title'], row[1]])

    with open('redcircle_cache.pkl', 'wb') as f:
        pickle.dump(cache, f)

    return {"content": out}


    # return {}

if __name__ == '__main__':
    app.run()
