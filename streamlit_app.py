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
sib_api_v3_sdk.configuration.api_key['api-key'] = st.secrets["brevo"]["api_key"]
api_instance = sib_api_v3_sdk.EmailCampaignsApi()

# ----------------------------
# SMTP Configuration
# ----------------------------
smtp_server = "smtp-relay.brevo.com"
smtp_port = 587
sender_email = st.secrets["smtp"]["username"]
sender_password = st.secrets["smtp"]["password"]

# Configure the Gemini AI API key for proposal generation
genai.configure(api_key=st.secrets["google"]["GOOGLE_API_KEY"])

# ----------------------------
# Function to Create Brevo Campaign
# ----------------------------
def create_brevo_campaign():
    email_campaigns = sib_api_v3_sdk.CreateEmailCampaign(
        name="Campaign sent via the API",
        subject="My subject",
        sender={"name": "From Name", "email": "myfromemail@mycompany.com"},
        type="classic",  # Choose the type of campaign (classic, A/B test, etc.)
        html_content="Congratulations! You successfully sent this example campaign via the Brevo API.",
        recipients={"listIds": [2, 7]},  # List IDs to send to
        scheduled_at="2024-12-01 00:00:01"  # Example of scheduling the campaign
    )
    
    try:
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
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(sender_email, sender_password)
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
        prompt = f"""
        Generate a personalized sales proposal for a customer named {customer_name}. 
        The product is {product_name}, and here are the details: {product_details}. 
        The customer's needs are: {customer_needs}. 
        The proposal should be professional, persuasive, and tailored to the customer's needs.
        """

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

if uploaded_file is not None:
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

    # Optionally, create a Brevo campaign
    create_brevo_campaign()

else:
    st.info("Please upload a CSV file to continue.")
