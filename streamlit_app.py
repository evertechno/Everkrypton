import os
import pickle
import streamlit as st
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from datetime import datetime

# OAuth2 Authentication with Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDS_FILE = 'token.pickle'  # This file stores the credentials

def authenticate_gmail():
    """Authenticate the user and return Gmail API service using manual console authentication."""
    creds = None

    # Check if token.pickle exists and contains valid credentials
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials are available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Replace with the appropriate path to your client_secret.json file
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)

            # Run console-based authentication
            print("Please go to this URL: ")
            auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
            print(auth_url)

            # Manually authenticate: Visit the URL, get the authorization code, and paste it here.
            code = input('Enter the authorization code: ')
            creds = flow.fetch_token(authorization_response=code, client_secret_file='client_secret.json')

        # Save the credentials for the next run
        with open(CREDS_FILE, 'wb') as token:
            pickle.dump(creds, token)

    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    return service

# Send email using Gmail API
def send_email(service, to_email, subject, body):
    """Send an email using Gmail API."""
    try:
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "me"  # 'me' is a special value indicating the authenticated user
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Encode the message and send it via Gmail API
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

# Process proposals and send emails if the button is clicked
if df is not None and st.button("Generate and Send Proposals"):
    # Authenticate Gmail API
    service = authenticate_gmail()

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

# Option to download generated proposals
if df is not None and st.button("Download Generated Proposals"):
    output_df = df[['Lead Name', 'Email Address', 'Interested Product', 'Price Range']]
    output_df['Proposal'] = output_df.apply(lambda row: f"Dear {row['Lead Name']},\n\nWe are excited to offer you a {row['Interested Product']} that fits your budget of {row['Price Range']}.\n\nBest regards,\nYour Company Name", axis=1)
    
    output_df.to_csv("generated_proposals.csv", index=False)
    st.download_button("Download Proposals", "generated_proposals.csv", "generated_proposals.csv")

# Function to filter leads by budget
if df is not None:
    filters = st.selectbox("Filter Leads by Budget", options=["All", "High Budget", "Mid Budget", "Low Budget"])

    if filters == "High Budget":
        filtered_leads = df[df['Price Range'].apply(lambda x: float(x.replace('$', '').replace(',', '').strip()) > 50000)]
    elif filters == "Mid Budget":
        filtered_leads = df[df['Price Range'].apply(lambda x: 20000 <= float(x.replace('$', '').replace(',', '').strip()) <= 50000)]
    elif filters == "Low Budget":
        filtered_leads = df[df['Price Range'].apply(lambda x: float(x.replace('$', '').replace(',', '').strip()) < 20000)]
    else:
        filtered_leads = df

    st.write("Filtered Leads:")
    st.write(filtered_leads)

# Generate Lead Age (days since lead date)
if df is not None and 'Lead Date' in df.columns:
    df['Lead Date'] = pd.to_datetime(df['Lead Date'])
    df['Lead Age (Days)'] = (datetime.now() - df['Lead Date']).dt.days
    st.write("Lead Age (in Days):")
    st.write(df[['Lead Name', 'Lead Age (Days)']])
