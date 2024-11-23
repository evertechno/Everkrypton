import streamlit as st
import pandas as pd
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import logging
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import random
import openpyxl
from fpdf import FPDF

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Email configuration
SMTP_SERVER = 'smtp.yourmailserver.com'
SMTP_PORT = 587
EMAIL_SENDER = 'your_email@example.com'
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]  # Store email password securely in Streamlit secrets

# Configure logging
log_filename = "sales_proposals.log"
logging.basicConfig(filename=log_filename, level=logging.INFO)

# Streamlit App UI
st.title("Automated Sales Proposal Generator")
st.write("Upload your leads' CSV, personalize proposals using AI, and send emails automatically.")

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

# Proceed with generating proposals only if the file was uploaded and df is defined
if df is not None and st.button("Generate Proposals"):
    # Process each lead and create a personalized email
    responses = []
    for _, row in df.iterrows():
        lead_name = row['Lead Name']
        product = row['Interested Product']
        budget = row['Price Range']
        email = row['Email Address']
        
        prompt = f"Create a personalized sales proposal for {lead_name}, who is interested in {product} within a budget of {budget}. Make the proposal professional and tailored."
        
        try:
            # Generate proposal using AI model
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            proposal = response.text
            responses.append((lead_name, email, proposal))
            
            # Log the proposal creation
            logging.info(f"{datetime.now()} - Generated proposal for {lead_name}: {proposal[:100]}...")

        except Exception as e:
            st.error(f"Error generating proposal for {lead_name}: {e}")
            logging.error(f"{datetime.now()} - Error generating proposal for {lead_name}: {e}")

    # Display AI-generated proposals
    st.write("Generated Proposals:")
    for lead_name, email, proposal in responses:
        st.write(f"Proposal for {lead_name} ({email}):")
        st.write(proposal)
        st.text_area(f"Proposal for {lead_name}", proposal, height=200)

    # Send proposals via email
    if st.button("Send Emails"):
        email_status = []  # To store the status of each email sent
        for lead_name, email, proposal in responses:
            try:
                # Use a progress bar to show email sending progress
                progress_bar = st.progress(0)
                progress_bar.progress(0)  # Initialize progress bar
                send_email(email, lead_name, proposal)
                email_status.append((lead_name, email, "Success"))
                st.success(f"Email sent to {lead_name} at {email}")
                logging.info(f"{datetime.now()} - Email sent to {lead_name} at {email}")
                progress_bar.progress(100)  # Complete progress bar
                
            except Exception as e:
                email_status.append((lead_name, email, f"Failed: {e}"))
                st.error(f"Failed to send email to {lead_name}: {e}")
                logging.error(f"{datetime.now()} - Failed to send email to {lead_name}: {e}")

        # Display email sending status after completion
        st.write("Email Sending Status:")
        email_status_df = pd.DataFrame(email_status, columns=['Lead Name', 'Email Address', 'Status'])
        st.write(email_status_df)

    # Save generated proposals to a CSV file for record-keeping
    if st.button("Download Generated Proposals"):
        output_df = pd.DataFrame(responses, columns=['Lead Name', 'Email Address', 'Proposal'])
        output_df.to_csv("generated_proposals.csv", index=False)
        st.download_button("Download CSV", "generated_proposals.csv", "generated_proposals.csv")

    # Provide an option to send a test email
    if st.button("Send Test Email"):
        try:
            send_email("test@example.com", "Test User", "This is a test email. If you received this, the email system is working!")
            st.success("Test email sent successfully!")
        except Exception as e:
            st.error(f"Failed to send test email: {e}")

# Function to send email
def send_email(to_email, lead_name, proposal):
    # Create the email message
    subject = f"Personalized Proposal for {lead_name}"
    body = f"Dear {lead_name},\n\n{proposal}\n\nBest regards,\nYour Company Name"
    
    # Set up the MIME
    message = MIMEMultipart()
    message["From"] = EMAIL_SENDER
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    
    # Connect to the SMTP server and send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Start TLS encryption
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, message.as_string())
            server.quit()
            logging.info(f"{datetime.now()} - Successfully sent email to {to_email}")
    except Exception as e:
        logging.error(f"{datetime.now()} - Error sending email to {to_email}: {e}")
        raise Exception(f"Error sending email to {to_email}: {e}")

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

    # Generate Word Cloud
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(" ".join(df['Interested Product']))
    st.image(wordcloud.to_array(), caption="Word Cloud of Products Interested by Leads")

    # Sales Forecast
    total_revenue = df['Price Range'].apply(lambda x: float(x.replace('$', '').replace(',', '').strip())).sum()
    st.write(f"Estimated Sales Revenue: ${total_revenue}")

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

    # Lead Conversion Report (Simulated for now)
    df['Status'] = df['Status'].apply(lambda x: x if x in ['New', 'Contacted', 'Converted'] else 'New')
    conversion_rate = len(df[df['Status'] == 'Converted']) / len(df) * 100
    st.write(f"Conversion Rate: {conversion_rate}%")
