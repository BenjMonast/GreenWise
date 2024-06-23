import imaplib
import email
from email.header import decode_header
import getpass
import time


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

                print(f"Subject: {subject}")
                print(f"From: {from_}")

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
                            print(f"Body: {body}")
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
                        print(f"Body: {body}")

                print("=" * 100)

        time.sleep(check_interval)

