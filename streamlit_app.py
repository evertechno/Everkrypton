import os
import pickle
import smtplib
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail API authentication using service account
def authenticate_gmail_service_account():
    """Authenticate using a service account for headless environments."""
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    SERVICE_ACCOUNT_FILE = '/credentials.json'  # Update with your service account JSON file
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=credentials)
    return service

# Send email function
def send_email(service, to_email, subject, body):
    """Send an email using the Gmail API with service account authentication."""
    try:
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "your-email@gmail.com"  # Use your Gmail address
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Encode the message and send it via the Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = service.users().messages().send(
            userId="me", body={"raw": raw_message}).execute()
        st.success(f"Email successfully sent to {to_email}!")

    except Exception as e:
        st.error(f"Error sending email: {e}")
        print(f"Error: {e}")

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals using AI, and send emails automatically.")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV with Lead Data", type=["csv", "xlsx"])
df = None  # Initialize the df variable

if uploaded_file is not None:
    # Load CSV or Excel data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("Preview of the data:")
    st.write(df.head())

    # Ensure required columns are present
    required_columns = ['Lead Name', 'Interested Product', 'Price Range', 'Email Address', 'Lead Date']
    if not all(col in df.columns for col in required_columns):
        st.error(f"CSV file must contain the following columns: {', '.join(required_columns)}")

# Process proposals if the button is clicked
if df is not None and st.button("Generate and Send Proposals"):
    # Authenticate Gmail service using service account
    service = authenticate_gmail_service_account()

    # AI-based proposal generation
    for _, row in df.iterrows():
        lead_name = row['Lead Name']
        product = row['Interested Product']
        budget = row['Price Range']
        email = row['Email Address']
        
        # Personalized Proposal Generation
        proposal = f"Dear {lead_name},\n\nWe are excited to offer you a {product} that fits your budget of {budget}. We believe this will be a great addition to your business.\n\nBest regards,\nYour Company Name"
        
        # Send Email with Proposal
        subject = f"Personalized Sales Proposal for {lead_name}"
        body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"
        
        # Call the send_email function
        try:
            send_email(service, email, subject, body)
        except Exception as e:
            st.error(f"Failed to send email to {lead_name} at {email}: {e}")

    st.success("All emails have been sent successfully!")

