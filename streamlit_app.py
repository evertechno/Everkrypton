import streamlit as st
import pandas as pd
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

# Logging setup
logging.basicConfig(level=logging.INFO)

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals using AI, and send emails securely via Gmail.")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV with Lead Data", type=["csv", "xlsx"])
df = None  # Initialize the df variable here to ensure it's defined even if no file is uploaded

if uploaded_file is not None:
    # Load CSV data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("Preview of the data:")
    st.write(df.head())

    # Ensure correct columns are present
    required_columns = ['Lead Name', 'Interested Product', 'Price Range', 'Email Address', 'Lead Date']
    if not all(col in df.columns for col in required_columns):
        st.error(f"CSV file must contain the following columns: {', '.join(required_columns)}")

# Authentication with Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Function to authenticate with Google OAuth 2.0
def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

# Function to send email using Gmail API
def send_email(to_email, lead_name, proposal, service):
    message = MIMEMultipart()
    message["From"] = 'me'  # 'me' refers to the authenticated Gmail account
    message["To"] = to_email
    message["Subject"] = f"Personalized Proposal for {lead_name}"
    body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"
    message.attach(MIMEText(body, "plain"))
    
    raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
    
    try:
        send_message = service.users().messages().send(userId="me", body=raw_message).execute()
        logging.info(f"Message Id: {send_message['id']}")
        return True
    except Exception as e:
        logging.error(f"An error occurred while sending the email: {e}")
        return False

# Proceed with generating proposals only if the file was uploaded and df is defined
if df is not None and st.button("Generate Proposals"):
    # Authenticate Gmail account
    creds = authenticate_gmail()
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    
    # Process each lead and create a personalized email
    responses = []
    for _, row in df.iterrows():
        lead_name = row['Lead Name']
        product = row['Interested Product']
        budget = row['Price Range']
        email = row['Email Address']
        
        # Generate AI proposal (simulated here as a basic string)
        proposal = f"Dear {lead_name},\n\nWe have the perfect {product} for you! Your budget of {budget} is ideal. Let's talk soon!"
        responses.append((lead_name, email, proposal))
        
        # Send email via Gmail API
        if send_email(email, lead_name, proposal, service):
            st.success(f"Proposal sent to {lead_name} at {email}")
        else:
            st.error(f"Failed to send email to {lead_name} at {email}")

# Option to download the generated proposals
if st.button("Download Generated Proposals"):
    output_df = pd.DataFrame(responses, columns=['Lead Name', 'Email Address', 'Proposal'])
    output_df.to_csv("generated_proposals.csv", index=False)
    st.download_button("Download CSV", "generated_proposals.csv", "generated_proposals.csv")
