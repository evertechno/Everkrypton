import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import streamlit as st
from datetime import datetime
import urllib.parse
from email.mime.application import MIMEApplication

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals, and send emails automatically via SMTP.")

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

# SMTP Email Settings
smtp_server = "smtp-relay.brevo.com"
smtp_port = 587
sender_email = "7cd1d3001@smtp-brevo.com"  # Enter your email here
sender_password = "sender_password"  # Enter your email password here

def send_email(receiver_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))

        # Set up the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
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
