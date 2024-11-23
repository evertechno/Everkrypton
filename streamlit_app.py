import smtplib
import streamlit as st
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai

# Access SMTP credentials from Streamlit secrets
smtp_server = "smtp-relay.brevo.com"
smtp_port = 587
sender_email = st.secrets["smtp"]["username"]  # Retrieve SMTP username from Streamlit secrets
sender_password = st.secrets["smtp"]["password"]  # Retrieve SMTP key (Master Password) from Streamlit secrets

# Configure the Gemini AI API key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Function to send email with better logging
def send_email(to_email, subject, body):
    try:
        # Setup the MIME
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach the email body to the email
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to the SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)  # Enable debug mode for SMTP to get detailed logs
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Login using the stored credentials
            text = msg.as_string()
            
            # Send the email
            response = server.sendmail(sender_email, to_email, text)  # Send the email
            st.write(f"Server Response: {response}")  # Print server response for debugging

        st.success(f"Email sent successfully to {to_email}")
    
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Function to generate a personalized sales proposal using AI
def generate_sales_proposal(customer_name, product_name, product_details, customer_needs):
    try:
        # Define the prompt for AI to generate a sales proposal
        prompt = f"""
        Generate a personalized sales proposal for a customer named {customer_name}. 
        The product is {product_name}, and here are the details: {product_details}. 
        The customer's needs are: {customer_needs}. 
        The proposal should be professional, persuasive, and tailored to the customer's needs.
        """

        # Generate the sales proposal using AI
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Return the generated proposal text
        return response.text
    except Exception as e:
        st.error(f"Error generating sales proposal: {e}")
        return None

# Streamlit App UI
st.title("Generate and Send Personalized Sales Proposal")
st.write("Upload a CSV file with customer details to generate and send personalized proposals.")

# File upload for CSV
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

# Check if the file is uploaded and is in CSV format
if uploaded_file is not None:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(uploaded_file)

    # Display the uploaded data (for verification)
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
            
            # Send the proposal via email
            send_email(recipient_email, subject, proposal)
else:
    st.info("Please upload a CSV file to continue.")
