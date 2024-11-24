import smtplib
import streamlit as st
import pandas as pd
import sib_api_v3_sdk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pprint import pprint
import google.generativeai as genai

# ----------------------------
# Brevo API Setup
# ----------------------------
# Configure the Brevo API key using Streamlit secrets
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = st.secrets["brevo"]["api_key"]
api_instance = sib_api_v3_sdk.EmailCampaignsApi(sib_api_v3_sdk.ApiClient(configuration))

# ----------------------------
# SMTP Configuration
# ----------------------------
smtp_server = "smtp-relay.brevo.com"
smtp_port = 587
sender_email = st.secrets["smtp"]["username"]  # Retrieve SMTP username from Streamlit secrets
sender_password = st.secrets["smtp"]["password"]  # Retrieve SMTP password (Master Password) from Streamlit secrets

# Configure the Gemini AI API key for proposal generation
genai.configure(api_key=st.secrets["google"]["GOOGLE_API_KEY"])

# ----------------------------
# Function to Create Brevo Campaign
# ----------------------------
def create_brevo_campaign():
    # Use the updated parameter names
    email_campaigns = sib_api_v3_sdk.CreateEmailCampaign(
        name="Campaign sent via the API",
        subject="My subject",
        sender={"name": "From Name", "email": "myfromemail@mycompany.com"},
        campaign_type="classic",  # Correct parameter name for campaign type
        html_content="Congratulations! You successfully sent this example campaign via the Brevo API.",
        recipients={"listIds": [2, 7]},  # List IDs to send to
        scheduled_at="2024-12-01 00:00:01"  # Example of scheduling the campaign
    )
    
    try:
        # Call the Brevo API to create the campaign
        api_response = api_instance.create_email_campaign(email_campaigns)
        pprint(api_response)
        return api_response
    except Exception as e:
        st.error(f"Error creating Brevo campaign: {e}")
        return None

# ----------------------------
# Function to Send Email via SMTP
# ----------------------------
def send_email(to_email, subject, body):
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)  # Enable debug level for detailed SMTP logs
            server.starttls()  # Start TLS encryption
            server.login(sender_email, sender_password)  # Login with credentials
            text = msg.as_string()
            response = server.sendmail(sender_email, to_email, text)
            st.write(f"Server Response: {response}")

        st.success(f"Email sent successfully to {to_email}")
    
    except Exception as e:
        st.error(f"Error sending email: {e}")

# ----------------------------
# Function to Generate Sales Proposal using AI
# ----------------------------
def generate_sales_proposal(customer_name, product_name, product_details, customer_needs):
    try:
        # Define the prompt for the AI model to generate a proposal
        prompt = f"""
        Generate a personalized sales proposal for a customer named {customer_name}. 
        The product is {product_name}, and here are the details: {product_details}. 
        The customer's needs are: {customer_needs}. 
        The proposal should be professional, persuasive, and tailored to the customer's needs.
        """

        # Use Gemini AI to generate the proposal text
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        st.error(f"Error generating sales proposal: {e}")
        return None

# ----------------------------
# Streamlit App UI
# ----------------------------
st.title("Generate and Send Personalized Sales Proposal")
st.write("Upload a CSV file with customer details to generate and send personalized proposals.")

# File upload for CSV
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

# Check if a file was uploaded
if uploaded_file is not None:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(uploaded_file)

    # Display the uploaded data
    st.write("Uploaded CSV Data:")
    st.dataframe(df)

    # Process each row in the CSV to generate and send proposals
    for index, row in df.iterrows():
        customer_name = row['Name']
        recipient_email = row['Email']
        product_name = row['Product']
        product_details = row['Product Details']
        customer_needs = row['Customer Needs']
        
        # Generate the sales proposal using AI
        proposal = generate_sales_proposal(customer_name, product_name, product_details, customer_needs)
        
        if proposal:
            # Subject for the email
            subject = f"Personalized Sales Proposal for {customer_name}"
            
            # Send the proposal via SMTP
            send_email(recipient_email, subject, proposal)

    # Optionally, create a Brevo campaign (this step can be skipped or used to send marketing campaigns)
    create_brevo_campaign()

else:
    st.info("Please upload a CSV file to continue.")
