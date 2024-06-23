import imaplib
import email
import os
import pickle
from datetime import date, datetime
from email.header import decode_header
import getpass
import time
from tokens import OAI_TOKEN
import base64, requests, re

def read_new_emails(email_account, password, folder="inbox", check_interval=60):
    def fetch_emails():
        # Connect to the server
        imap = imaplib.IMAP4_SSL("imap.gmail.com")

        # Login to your account
        imap.login(email_account, password)

        # Select the mailbox you want to read (inbox by default)
        imap.select(folder)

        # Search for all emails in the selected mailbox
        status, messages = imap.search(None, "ALL")
        email_ids = messages[0].split()

        emails = []
        for email_id in email_ids:
            # Fetch the email message by ID
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse the email message
                    msg = email.message_from_bytes(response_part[1])
                    emails.append(msg)

        # Close the connection and logout
        imap.close()
        imap.logout()

        return emails

    seen_emails = set()

    while True:
        emails = fetch_emails()
        emailstring = ""
        for msg in emails:
            email_id = msg["Message-ID"]
            if email_id not in seen_emails:
                seen_emails.add(email_id)

                # Decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                # Decode the email sender
                from_ = msg.get("From")

                emailstring = emailstring + subject
                emailstring = emailstring + from_
                # If the email message is multipart
                if msg.is_multipart():
                    # Iterate over email parts
                    for part in msg.walk():
                        # Extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        try:
                            # Get the email body
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            # Print text/plain emails and skip attachments
                            emailstring = emailstring + body
                        elif "attachment" in content_disposition:
                            # Skip attachments for now
                            pass
                else:
                    # Extract content type of email
                    content_type = msg.get_content_type()

                    # Get the email body
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        # Print only text email parts
                        emailstring = emailstring +body
                emailstring = emailstring + ("=" * 100)
            return emailstring

def read_receipt_email():
    OAI_TOKEN = "sk-proj-4detDT2cE6pPgrFVXeYCT3BlbkFJqIs6aFzDL3BWhNAKd0tI"
    receipt = read_new_emails("somethingnormalai@gmail.com", "bszr fscr qfmy txto")
    if receipt is not None:
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
                                    "text": "Compile the information on this receipt into a csv file with the columns Product, Price, and Category, where the possible Categories are Food, Household Essentials, Health and Beauty, Electronics, Clothing, Home and Furniture, Toys and Games, Office Supplies, Outdoor, Automotive, Baby, and Pet."
                                },
                                {
                                    "type": "text",
                                    "text": str(receipt)

                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                message = response.json()['choices'][0]['message']['content']
                csvData = re.search(r'```csv\n(.*)\n```', message, re.DOTALL)[1].splitlines()[1:]
                if len(csvData) is None:
                    raise Exception
            except Exception as e:
                print(e)
                attempts += 1
    if not os.path.isfile("db.pkl"):
        db = []
    else:
        with open("db.pkl", "rb") as cache_file:
            db = pickle.load(cache_file)
    fcsvData = format_receipt_data(csvData)
    db += fcsvData
    print(fcsvData)
    with open("db.pkl", "wb") as cache_file:
        pickle.dump(db, cache_file)
    return {"content": format_receipt_data(csvData)}


def format_receipt_data(data):
    formatted_data = []
    current_date = datetime.today().strftime('%Y-%m-%d')

    for entry in data:
        parts = entry.split(',')
        parts.append(current_date)
        formatted_data.append(parts)

    return formatted_data


if __name__ == '__main__':
    read_receipt_email()
