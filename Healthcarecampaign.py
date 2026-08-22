import pandas as pd
import smtplib
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

# Email Configuration - Load from environment variables or set directly
sender_email = "hassan.saeed.xellex@gmail.com"  # Your Gmail address - strongly recommend using environment variables
sender_password = os.getenv("GMAIL_PASSWORD")  # Your Gmail app password, loaded from .env
smtp_server = "smtp.gmail.com"
port = 465  # For SSL

# Email Template
email_template = """Subject: Enhance Patient Care & Operational Efficiency with AI & Custom Solutions

Dear {contact_person_name},

I understand {hospital_name} is dedicated to delivering exceptional Healthcare services. At Xellex, we specialize in AI-powered solutions and custom software development tailored for the healthcare sector, helping organizations like yours operate more efficiently and improve patient care.

We offer expertise in:

*   AI-Driven Clinical Documentation: Automate workflows and enhance accuracy with AI scribes.
*   Intelligent Data Retrieval:  Improve decision-making and insights with AI-powered data solutions.
*   Interoperability & FHIR Solutions:  Seamlessly integrate systems and meet industry standards for data exchange.

Would you be open to a brief conversation to explore how Xellex can assist {hospital_name} in achieving enhanced operational efficiency?

You can also reach us out at sales@xellex.com.

Looking forward to your thoughts.

Best regards,

Hassan Saeed
Business Development Manager
Xellex
"""

def send_email(recipient_email, contact_person_name, hospital_name):
    """Sends an email using the template, replacing placeholders with provided data."""

    formatted_email = email_template.format(
        contact_person_name=contact_person_name,
        hospital_name=hospital_name
    )

    message = f"Subject: Enhance Patient Care & Operational Efficiency with AI & Custom Solutions\n\n{formatted_email}"


    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message)
            print(f"Email sent successfully to: {recipient_email}")
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")

def main():
    excel_file = "Details_20250301230915.xlsx"  # Replace with the actual path to your Excel file
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print(f"Error: Excel file '{excel_file}' not found. Please make sure the file exists and the path is correct.")
        return

    if "Full Name" not in df.columns or "Company Name" not in df.columns or "Email" not in df.columns:
        print("Error: Excel file must contain columns named 'Full Name', 'Company Name', and 'Email'.")
        return

    for index, row in df.iterrows():
        contact_person_name = row["Full Name"]
        hospital_name = row["Company Name"]
        recipient_email = row["Email"] # Assuming you have a column for recipient emails

        if pd.isna(recipient_email): # Skip rows with empty recipient emails
            print(f"Skipping row {index+2} due to missing Recipient Email.") # Excel rows are 1-indexed, header is row 1
            continue

        send_email(recipient_email, contact_person_name, hospital_name)

if __name__ == "__main__":
    main()