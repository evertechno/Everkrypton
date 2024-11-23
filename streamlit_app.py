import smtplib
import streamlit as st
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

# Function to send email
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
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Login using the stored credentials
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)  # Send the email

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
st.write("Use AI to generate personalized sales proposals based on customer information.")

# Inputs for customer details
customer_name = st.text_input("Customer Name")
product_name = st.text_input("Product Name")
product_details = st.text_area("Product Details")
customer_needs = st.text_area("Customer Needs")

# Button to generate and send proposal
if st.button("Generate Proposal and Send Email"):
    if customer_name and product_name and product_details and customer_needs:
        # Generate the sales proposal using AI
        proposal = generate_sales_proposal(customer_name, product_name, product_details, customer_needs)
        
        if proposal:
            # Email inputs
            recipient_email = st.text_input("Recipient Email")
            subject = f"Personalized Sales Proposal for {customer_name}"
            
            # Send the email with the generated proposal
            send_email(recipient_email, subject, proposal)
    else:
        st.error("Please fill out all fields to generate the proposal.")
