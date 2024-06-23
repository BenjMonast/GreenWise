from flask import Flask, request, render_template
from recommend import get_co2e, get_rec
from tokens import *
import base64, requests, re, pickle, os
from datetime import datetime
from markupsafe import Markup
from datetime import date as d

global numtasks

app = Flask(__name__)

@app.route("/")
def index():
    numtasks = 0
    db = []
    db_with_rec = []
    if os.path.isfile("db.pkl"):
        with open("db.pkl", "rb") as f:
            db = pickle.load(f)
        
        # function to sort
        def get_date(date):
            return datetime.strptime(date[4], "%Y-%m-%d")

        db = sorted(db, key=get_date)

        db_with_rec = []

        for item in db:
            rec_name, rec_carbon, _, rec_company = get_rec(item[0])
            if rec_name != -1:
                rec = [f"{rec_name} from {rec_company}\nC02e: {rec_carbon}"]
                db_with_rec.append(item + rec)
                numtasks = numtasks + 1
            else:
                db_with_rec.append(item + [""])

    if len(db) == 0:
        totalcarbon = 0
    else:
        totalcarbon = sum([row[3] for row in db])


    return render_template("index.html", data=db_with_rec, num=numtasks, carbon=totalcarbon)

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
    try:
        date = response.json()['date']['data'].split("T")[0]
    except:
        date = d.today().strftime('%Y-%m-%d')

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
            print(f"{id} not found in cache, querying api")
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
        out[i].append(get_co2e(out[i][0]))
        out[i].append(date)

    for i, row in enumerate(out):
        out[i][0] = Markup(out[i][0])

    if not os.path.isfile("db.pkl"):
        db = []
    else:
        with open("db.pkl", "rb") as cache_file:
            db = pickle.load(cache_file)

    db += out
    print(db)
    with open("db.pkl", "wb") as cache_file:
        pickle.dump(db, cache_file)
        
    return {"content": out}


if __name__ == '__main__':
    app.run()
