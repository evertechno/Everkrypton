import streamlit as st
import pandas as pd
import google.generativeai as genai
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from datetime import datetime
import logging

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Brevo API Configuration
api_key = st.secrets["BREVO_API_KEY"]
sib_api_v3_sdk.configuration.api_key['api-key'] = api_key

# Configure logging
log_filename = "sales_proposals.log"
logging.basicConfig(filename=log_filename, level=logging.INFO)

# Function to send email using Brevo (Sendinblue) API
def send_email(to_email, lead_name, proposal):
    # Create the email message
    subject = f"Personalized Proposal for {lead_name}"
    body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"

    # Configure Brevo API client
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi()
    
    # Prepare email data
    email_data = {
        "sender": {"email": "mahalaxmiastrovastu01@gmail.com"},  # Replace with your sender email
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body><p>{body}</p></body></html>"
    }

    try:
        # Send the email
        response = api_instance.send_transac_email(email_data)
        logging.info(f"{datetime.now()} - Successfully sent email to {to_email}")
        return True
    except ApiException as e:
        logging.error(f"{datetime.now()} - Error sending email to {to_email}: {e}")
        return False

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals using AI, and send emails automatically.")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV with Lead Data", type=["csv", "xlsx"])
df = None  # Initialize df variable

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

# Generate and send proposals when button is clicked
if df is not None and st.button("Generate and Send Proposals"):
    responses = []
    email_status = []

    for _, row in df.iterrows():
        lead_name = row['Lead Name']
        product = row['Interested Product']
        budget = row['Price Range']
        email = row['Email Address']

        # Generate proposal using AI model
        prompt = f"Create a personalized sales proposal for {lead_name}, who is interested in {product} within a budget of {budget}. Make the proposal professional and tailored."
        
        try:
            # Generate proposal using AI model
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            proposal = response.text
            responses.append((lead_name, email, proposal))
            
            # Log the proposal creation
            logging.info(f"{datetime.now()} - Generated proposal for {lead_name}: {proposal[:100]}...")

            # Send email using Brevo
            email_sent = send_email(email, lead_name, proposal)
            if email_sent:
                email_status.append((lead_name, email, "Success"))
                st.success(f"Email sent to {lead_name} at {email}")
            else:
                email_status.append((lead_name, email, "Failed"))
                st.error(f"Failed to send email to {lead_name} at {email}")

        except Exception as e:
            email_status.append((lead_name, email, f"Error: {e}"))
            st.error(f"Error generating proposal for {lead_name}: {e}")
            logging.error(f"{datetime.now()} - Error generating proposal for {lead_name}: {e}")
    
    # Show email status
    st.write("Email Delivery Status:")
    email_status_df = pd.DataFrame(email_status, columns=['Lead Name', 'Email Address', 'Status'])
    st.write(email_status_df)
