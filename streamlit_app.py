import streamlit as st
import pandas as pd
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import logging
import matplotlib.pyplot as plt
from wordcloud import WordCloud

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
if uploaded_file is not None:
    # Load CSV data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.write("Preview of the data:")
    st.write(df.head())

    # Ensure correct columns are present
    required_columns = ['Lead Name', 'Interested Product', 'Price Range', 'Email Address']
    if not all(col in df.columns for col in required_columns):
        st.error(f"CSV file must contain the following columns: {', '.join(required_columns)}")

    # Button to generate personalized proposals
    if st.button("Generate Proposals"):
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
            for lead_name, email, proposal in responses:
                try:
                    send_email(email, lead_name, proposal)
                    st.success(f"Email sent to {lead_name} at {email}")
                    logging.info(f"{datetime.now()} - Email sent to {lead_name} at {email}")
                except Exception as e:
                    st.error(f"Failed to send email to {lead_name}: {e}")
                    logging.error(f"{datetime.now()} - Failed to send email to {lead_name}: {e}")

        # Save generated proposals to a CSV file for record-keeping
        if st.button("Download Generated Proposals"):
            output_df = pd.DataFrame(responses, columns=['Lead Name', 'Email Address', 'Proposal'])
            output_df.to_csv("generated_proposals.csv", index=False)
            st.download_button("Download CSV", "generated_proposals.csv", "generated_proposals.csv")

        # Provide an option to send a test email
        if st.button("Send Test Email"):
            send_email("test@example.com", "Test User", "This is a test email. If you received this, the email system is working!")
            st.success("Test email sent successfully!")

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

# Add extra functionality to generate a report based on lead data
if st.button("Generate Lead Report"):
    lead_report = f"Total Leads: {len(df)}\n"
    lead_report += f"Leads Interested in High Budget: {len(df[df['Price Range'].apply(lambda x: float(x.replace('$', '').replace(',', '').strip()) > 50000)])}\n"
    lead_report += f"Leads Interested in Mid Budget: {len(df[df['Price Range'].apply(lambda x: 20000 <= float(x.replace('$', '').replace(',', '').strip()) <= 50000)])}\n"
    lead_report += f"Leads Interested in Low Budget: {len(df[df['Price Range'].apply(lambda x: float(x.replace('$', '').replace(',', '').strip()) < 20000)])}\n"
    
    st.write("Lead Report:")
    st.write(lead_report)

# Option to analyze lead conversion rate based on proposal effectiveness
if st.button("Analyze Lead Conversion"):
    # Simulating conversion rate analysis for demonstration purposes
    conversion_rate = (len(df[df['Interested Product'].str.contains('premium', case=False)]) / len(df)) * 100
    st.write(f"Estimated Lead Conversion Rate: {conversion_rate:.2f}%")

# Option to apply custom filters to leads
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

# Option to store proposals in a database (simulate with a simple file-based storage)
if st.button("Store Proposals in Database"):
    if not os.path.exists('proposals_db'):
        os.mkdir('proposals_db')
    for lead_name, email, proposal in responses:
        with open(f"proposals_db/{lead_name}_{email}.txt", 'w') as f:
            f.write(proposal)
    st.success("Proposals stored successfully in database.")

# Option to generate and visualize a dashboard with lead statistics
if st.button("Generate Dashboard"):
    # Placeholder code for a simple dashboard showing lead stats
    st.write("Dashboard:")
    st.write(f"Total Leads: {len(df)}")
    st.write(f"Leads Interested in Product A: {len(df[df['Interested Product'] == 'Product A'])}")
    st.write(f"Leads Interested in Product B: {len(df[df['Interested Product'] == 'Product B'])}")

    # Plotting a bar chart of leads per product
    product_counts = df['Interested Product'].value_counts()
    st.write("Leads per Product:")
    st.bar_chart(product_counts)

# Provide option to generate AI-based follow-up email
if st.button("Generate Follow-Up Email"):
    follow_up_email = "Hi {lead_name},\n\nWe just wanted to follow up on our previous proposal for {product}. Please let us know if you have any questions.\n\nBest regards,\nYour Company"
    st.write("Follow-up Email Template:")
    st.write(follow_up_email)

# Option to summarize lead data
if st.button("Summarize Lead Data"):
    summary = df.describe()
    st.write("Lead Data Summary:")
    st.write(summary)

# Option to visualize lead distribution by budget range
if st.button("Visualize Lead Budget Distribution"):
    df['Budget Range'] = df['Price Range'].apply(lambda x: 'High' if float(x.replace('$', '').replace(',', '').strip()) > 50000 else 'Mid' if float(x.replace('$', '').replace(',', '').strip()) >= 20000 else 'Low')
    budget_distribution = df['Budget Range'].value_counts()
    st.write("Lead Budget Distribution:")
    st.bar_chart(budget_distribution)

# Option to show detailed lead profile
if st.button("Show Detailed Lead Profile"):
    lead_name = st.text_input("Enter Lead Name for Profile")
    if lead_name:
        lead_profile = df[df['Lead Name'].str.contains(lead_name, case=False)]
        st.write("Lead Profile:")
        st.write(lead_profile)

# Option to show email templates with variables
if st.button("Show Email Templates"):
    email_templates = {
        "Initial Proposal": "Dear {lead_name},\n\nThank you for showing interest in our {product}. We have prepared a tailored proposal for you based on your budget of {budget}.\n\nBest regards,\nYour Company",
        "Follow-Up": "Hi {lead_name},\n\nJust wanted to follow up on our proposal for {product}. Let me know if you need any additional information.\n\nBest regards,\nYour Company"
    }
    st.write("Email Templates:")
    st.write(email_templates)

# Option to export filtered leads to CSV
if st.button("Export Filtered Leads to CSV"):
    filtered_leads.to_csv("filtered_leads.csv", index=False)
    st.download_button("Download Filtered Leads CSV", "filtered_leads.csv")
