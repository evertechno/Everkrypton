import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import streamlit as st
from datetime import datetime

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals, and send emails automatically via SMTP.")

# Access SMTP credentials from Streamlit secrets
smtp_server = "smtp-relay.brevo.com"
smtp_port = 587
sender_email = st.secrets["smtp"]["username"]  # Retrieve SMTP username from Streamlit secrets
sender_password = st.secrets["smtp"]["password"]  # Retrieve SMTP key (Master Password) from Streamlit secrets

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

# Function to send emails
def send_email(receiver_email, subject, body):
    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))

        # Set up the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)  # Log in using the SMTP key (Master Password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Process proposals and generate emails if the button is clicked
if df is not None and st.button("Generate Proposals and Send Emails"):
    proposals = []
    for _, row in df.iterrows():
        lead_name = row['Lead Name']
        product = row['Interested Product']
        budget = row['Price Range']
        email = row['Email Address']
        
        # Personalized Proposal Generation
        proposal = f"Dear {lead_name},\n\nWe are excited to offer you a {product} that fits your budget of {budget}. We believe this will be a great addition to your business.\n\nBest regards,\nYour Company Name"
        
        # Store the generated proposal for each lead
        proposals.append({
            "Lead Name": lead_name,
            "Email Address": email,
            "Proposal": proposal
        })

        # Send email using SMTP
        subject = f"Personalized Sales Proposal for {lead_name}"
        body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"
        success = send_email(email, subject, body)
        
        if success:
            st.success(f"Proposal sent to {lead_name} ({email})")
        else:
            st.error(f"Failed to send proposal to {lead_name} ({email})")

    st.success("All emails have been sent!")

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
