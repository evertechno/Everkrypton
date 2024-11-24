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
        st.error(f"Missing '{key_name}' in Streamlit secrets! Please add the API keys.")
        st.stop()  # Stop the app if secrets are missing


# API keys
BREVO_API_KEY = get_api_key("brevo_api_key")
SMTP_USERNAME = get_api_key("smtp_username")
SMTP_PASSWORD = get_api_key("smtp_password")
GOOGLE_API_KEY = get_api_key("google_api_key")


# --- Initialize API ---


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = BREVO_API_KEY
api_client = sib_api_v3_sdk.ApiClient(configuration)
api_instance = sib_api_v3_sdk.EmailCampaignsApi(api_client)



# --- Email Sending Functions ---

def send_email(from_addr, to_addr, subject, body, from_name="Example Sender"):
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        smtp_server = "smtp-relay.brevo.com"
        smtp_port = 587
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(from_addr, to_addr, msg.as_string())

        st.success(f"Email sent to {to_addr} successfully.")
    except smtplib.SMTPAuthenticationError as e:
        st.error(f"SMTP Authentication Error: {e}")
    except Exception as e:
        st.error(f"Error sending email: {e}")


# --- AI-based email generation ---
def generate_email_content(customer_data):

  try: 
    # Clear prompt, to properly create separate promps if necessary
    prompt = f"""
      Generate a personalized sales email with:

      Customer Name: {customer_data.get('Name', 'Customer')}
      Product: {customer_data.get('Product', 'Product')}
      Product Details: {customer_data.get('Product Details', 'No Details Available')}
      Customer Needs: {customer_data.get('Customer Needs', 'No Specific Needs Available')}


      Make sure you create:
          1. "From" field with name for a company: `[Company Name]`
          2.  Subject Line for a sale 
          3. A professional persuasive body of the email


      Output in this format: 
      [FROM NAME]
      [SUBJECT LINE]
      [EMAIL BODY]


    """

    response = genai.generate_content(prompt=prompt, model_name='gemini-pro-v1.5')


    #Check if the response is successful before handling data
    if not response.error:
       generated_content = response.text.strip().split("\n", maxsplit=2)  
       if len(generated_content)==3:  # Ensure the split works
         return generated_content[0].strip(),generated_content[1].strip(),generated_content[2].strip() # extract all needed text correctly
    else:
        st.error(f"Error Generating email from AI: {response.error}")  #Important: to prevent crashes



    return None, None, None


  except Exception as e:

        st.error(f"An unexpected error occurred while generating the email content: {e}")
        return None,None,None
# --- Streamlit App ---
st.title("Personalized Sales Proposals & Emails")

uploaded_file = st.file_uploader("Upload your customer data (CSV)", type="csv")


if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Customer Data:")
        st.dataframe(df)

        for index, row in df.iterrows():

            customer_data = row.to_dict()

            from_name, subject, body = generate_email_content(customer_data)
          

            if from_name and subject and body:  #Important: to check AI response returned correct info 

                send_email(
                    from_name, customer_data['Email'], subject, body)
   
            else:
              st.error("AI Email generation was not successful") # Important!

    except Exception as e:
        st.error(f"An error occurred during file processing: {e}")
else:
    st.info("Please upload a valid CSV file.")
