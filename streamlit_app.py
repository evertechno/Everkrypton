import streamlit as st
import pandas as pd
import google.generativeai as genai
import logging
from brevo_python import Configuration, ApiClient
from brevo_python.apis.transactional_emails_api import TransactionalEmailsApi
from brevo_python.models.send_smtp_email import SendSmtpEmail
from brevo_python.rest import ApiException
from datetime import datetime

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Brevo API Configuration
api_key = st.secrets["BREVO_API_KEY"]

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals using AI, and send emails automatically.")

# Configure logging
log_filename = "sales_proposals.log"
logging.basicConfig(filename=log_filename, level=logging.INFO)

# Function to send email using Brevo API
def send_email(to_email, lead_name, proposal):
    # Set up the Brevo API client
    configuration = Configuration()
    configuration.api_key['api-key'] = api_key
    api_client = ApiClient(configuration)
    
    # Initialize the TransactionalEmailsApi
    api_instance = TransactionalEmailsApi(api_client)
    
    # Prepare the email content
    subject = f"Personalized Proposal for {lead_name}"
    body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"
    
    # Create the email data structure
    email_data = SendSmtpEmail(
        sender={"email": "mahalaxmiastrovastu01@gmail.com"},  # Replace with your sender email
        to=[{"email": to_email}],
        subject=subject,
        html_content=f"<html><body><p>{body}</p></body></html>"
    )
    
    try:
        # Send the email using Brevo API
        response = api_instance.send_transac_email(email_data)
        logging.info(f"Successfully sent email to {to_email}")
        return True
    except ApiException as e:
        logging.error(f"Error sending email to {to_email}: {e}")
        return False

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV with Lead Data", type=["csv", "xlsx"])
df = None  # Initialize the df variable

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
            logging.info(f"Generated proposal for {lead_name}: {proposal[:100]}...")

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
            logging.error(f"Error generating proposal for {lead_name}: {e}")
    
    # Show email status
    st.write("Email Delivery Status:")
    email_status_df = pd.DataFrame(email_status, columns=['Lead Name', 'Email Address', 'Status'])
    st.write(email_status_df)

# Option to filter leads by price range
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

# Option to generate and visualize a dashboard with lead statistics
if df is not None and st.button("Generate Dashboard"):
    # Placeholder code for a simple dashboard showing lead stats
    st.write("Dashboard:")
    st.write(f"Total Leads: {len(df)}")
    st.write(f"Leads Interested in Product A: {len(df[df['Interested Product'] == 'Product A'])}")
    st.write(f"Leads Interested in Product B: {len(df[df['Interested Product'] == 'Product B'])}")

    # Plotting a bar chart of leads per product
    product_counts = df['Interested Product'].value_counts()
    st.write("Leads per Product:")
    st.bar_chart(product_counts)

    # Generate Salesperson Assignment
    salesperson = []
    for _, row in df.iterrows():
        if row['Price Range'] > 50000:
            salesperson.append('John Doe')
        else:
            salesperson.append('Jane Smith')
    df['Salesperson'] = salesperson
    st.write("Lead Assignments:")
    st.write(df[['Lead Name', 'Salesperson']])
