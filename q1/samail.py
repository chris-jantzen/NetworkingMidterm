import re
import smtplib
from config import email_credentials
from sys import argv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

gmail_user = email_credentials["email_address"]
gmail_password = email_credentials["email_password"]


# Validate email address is real
def check(email):
    regex = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
    return re.search(regex, email):


if not check(argv[1]):
    print("Not a valid email address")
    exit(1)

to = argv[1]  # "cjantzen22@gmail.com"
subject = "Test of email message"
body = "Hello, this is a test message sending email from Python"

email_text = """
From: Chris Jantzen <{}>
To: {} <{}>
Subject: {}

{}""".format(
    gmail_user, to.split("@")[0], to, subject, body
)

msg = MIMEMultipart()
msg["To"] = to
msg["From"] = gmail_user
msg["Subject"] = subject
msg.attach(MIMEText(email_text, "plain"))

message = msg.as_string()

try:
    server = smtplib.SMTP_SSL(
        "smtp.gmail.com", 465
    )  # Establish SMPT Connection to Gmail server
    server.ehlo_or_helo_if_needed()
    server.login(gmail_user, gmail_password)
    server.sendmail(gmail_user, to, message)
    server.close()  # Close Connection

    print("Sent!")
except smtplib.SMTPException as e:
    print("Error: ", end="")
    print(e)
