import os
import pickle
import smtplib
import streamlit as st
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail OAuth2 Authentication
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """Handles authentication with Gmail API."""
    creds = None
    
    # Check if token.pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials are available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Run the OAuth flow and obtain credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            
            # Use this for local server authentication (should work with a browser)
            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                # Fallback to console authentication for headless environments
                creds = flow.run_console()

        # Save credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

# Send Email Function
def send_email(to_email, subject, body):
    """Send an email using Gmail."""
    creds = authenticate_gmail()
    
    # Send email using Gmail API
    try:
        # Set up the MIME
        message = MIMEMultipart()
        message["From"] = creds.token
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to the Gmail SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Start TLS encryption
            server.login(creds.token, creds.token)
            server.sendmail(creds.token, to_email, message.as_string())
            server.quit()
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
    # AI-based proposal generation
    for _, row in df.iterrows():
        lead_name = row['Lead Name']
        product = row['Interested Product']
        budget = row['Price Range']
        email = row['Email Address']
        
        # Personalized Proposal Generation (This could be replaced with AI/Google AI model in future)
        proposal = f"Dear {lead_name},\n\nWe are excited to offer you a {product} that fits your budget of {budget}. We believe this will be a great addition to your business.\n\nBest regards,\nYour Company Name"
        
        # Send Email with Proposal
        subject = f"Personalized Sales Proposal for {lead_name}"
        body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"
        
        # Call the send_email function
        try:
            send_email(email, subject, body)
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

