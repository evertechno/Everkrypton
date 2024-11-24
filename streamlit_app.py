import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
import sib_api_v3_sdk


# --- Config ---
def get_api_key(key_name):
  try:
    return st.secrets[key_name]
  except KeyError:
    st.error(f"Missing '{key_name}' in Streamlit secrets!")
    st.stop()

#BREVO API Key
BREVO_API_KEY = get_api_key("brevo")

SMTP_USERNAME = get_api_key("smtp-username")
SMTP_PASSWORD = get_api_key("smtp-password")
GOOGLE_API_KEY = get_api_key("google")



#--- API initialisation
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = BREVO_API_KEY
api_client = sib_api_v3_sdk.ApiClient(configuration)
api_instance = sib_api_v3_sdk.EmailCampaignsApi(api_client)


# --- Email Functions ---

def create_brevo_campaign():
    try:
        # Example campaign data
        campaign_data = {
            "name": "Example Campaign",
            "subject": "Example Subject",
            "sender": {
                "name": "Example Sender Name",  
                "email": "example_sender@example.com",
            },
            "html_content": "This is an example campaign.",
            "recipients": {"listIds": [1, 2]}, # Replace with your list IDs
            "scheduled_at": "2024-10-27T10:00:00",  
        }

        result = api_instance.create_email_campaign(campaign_data)
        st.success("Brevo Campaign created successfully!")
        st.info(result)
        return result
    except sib_api_v3_sdk.ApiException as e:
        st.error(f"Brevo Error: {e}")
        return None

def send_email(from_name, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = from_name  
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    smtp_server = "smtp-relay.brevo.com"
    smtp_port = 587
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo() #important, needed
        server.login(SMTP_USERNAME, SMTP_PASSWORD)  #important change
        text = msg.as_string()
        server.sendmail(from_name, to_email, text)  
    
    st.success(f"Email sent to {to_email} successfully.")

# --- Gemini AI Integration ---
def generate_sales_proposal(customer_data):
    try:
      prompt = f"""
        Generate a personalized sales email:


        Customer Name: {customer_data['Name']}
        Product: {customer_data['Product']}
        Product Details: {customer_data['Product Details']}
        Customer Needs: {customer_data['Customer Needs']}
        """

        response = genai.generate_content(prompt=prompt, model_name='gemini-pro-v1.5',max_output_tokens=500)

        if not response.error:

          return response.text.strip()


        else:
            st.error(f"Error generating sales proposal: {response.error}")
            return None

    except Exception as e:
        st.error(f"Error generating sales proposal: {e}")
        return None



# --- Streamlit App ---
st.title("Generate & Send Personalized Sales Proposals")

uploaded_file = st.file_uploader("Upload your customer data (CSV)", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Data:")
        st.dataframe(df)
        for _, row in df.iterrows():
            customer_data = row.to_dict()
            
            # This part is improved to generate appropriate subject and emails using AI data.
            generated_email_text = generate_sales_proposal(customer_data)
            if generated_email_text:  # Important null check
                email_parts = generated_email_text.split('\n\n', maxsplit=2)  
                from_name = email_parts[0].strip()
                subject = email_parts[1].strip()
                body = email_parts[2].strip() if len(email_parts) >2 else "" # handles possible single email format

                send_email(from_name, customer_data['Email'], subject, body)

    except Exception as e:
      st.error(f"An unexpected error occurred during file processing: {e}")

else:
    st.info("Please upload a valid CSV file.")
