from flask import Flask, request, render_template
from recommend import get_rec
from tokens import *
import base64, requests, re, pickle, os
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    db = []
    if os.path.isfile("db.pkl"):
        with open("db.pkl", "rb") as f:
            db = pickle.load(f)
        
        # function to sort
        def get_date(item):
            return datetime.strptime(item[3], "%Y-%m-%d")

        db = sorted(db, key=get_date)

        db_with_rec = []

        for item in db:
            recs = get_rec(item[0])
            if len(recs) > 0:
                rec = [f"{recs[0]} from {recs[1]}\nC02e: {rec[5]}"]
                db_with_rec.append(item + rec)
            else:
                db_with_rec.append(item + [""])         

    return render_template("index.html", data=db_with_rec)

# @app.route("/carbon")
# def carbon():
#     return render_template("carbon.html")

@app.route("/manual")
def manual():
    return render_template("manual.html")


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
    date = response.json()['date']['data'].split("T")[0]

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

    names = [row[0] for row in out]
    query = ", ".join(names)
    
    csvData = None
    attempts = 0

    while csvData == None and attempts < 4:
        try:    
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
                                "text": f"Given the list of products below, return in csv format a list of categories that each product should fall into. The possible categories are Food, Household Essentials, Health and Beauty, Electronics, Clothing, Home and Furniture, Toys and Games, Office Supplies, Outdoor, Automotive, Baby, and Pet. Ensure the only column in this csv file is \"category\"\n{query}"
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            print(response.json())
            message = response.json()['choices'][0]['message']['content']

            csvData = re.search(r'```csv\n(.*)\n```', message, re.DOTALL)[1].splitlines()[1:]

            if len(csvData) != len(out):
                raise Exception
        except Exception as e:
            print(e)
            attempts += 1

    for i, row in enumerate(csvData):
        out[i].append(row)
        out[i].append(date)

    if not os.path.isfile("db.pkl"):
        db = []
    else:
        with open("db.pkl", "rb") as cache_file:
            db = pickle.load(cache_file)

    db += out

    with open("db.pkl", "wb") as cache_file:
        pickle.dump(db, cache_file)
        
    return {"content": out}


if __name__ == '__main__':
    app.run()
