import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configure the API key securely from Streamlit's secrets
# Make sure to add GOOGLE_API_KEY in secrets.toml (for local) or Streamlit Cloud Secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("Sales Demo, Proposal & Email Campaign Generator with AI")
st.write("Use generative AI to create sales demos, proposals, and email campaigns from your leads data.")

# CSV Upload
uploaded_file = st.file_uploader("Upload CSV with Lead Details", type=["csv"])

if uploaded_file is not None:
    # Read the CSV file into a DataFrame
    leads_df = pd.read_csv(uploaded_file)
    
    # Show the first few rows of the data to confirm it was loaded correctly
    st.write("Uploaded Lead Data:")
    st.dataframe(leads_df.head())

    # Assuming the CSV has columns like: Company, Role, Industry, PainPoints, TargetProduct
    if all(col in leads_df.columns for col in ['Company', 'Role', 'Industry', 'PainPoints', 'TargetProduct']):
        
        # Button to generate content for all leads
        if st.button("Generate Content for All Leads"):
            for _, lead in leads_df.iterrows():
                company_name = lead['Company']
                target_role = lead['Role']
                industry = lead['Industry']
                pain_points = lead['PainPoints']
                target_product = lead['TargetProduct']

                # Use lead details to generate personalized prompts
                demo_prompt = f"Create a sales demo for a product called '{target_product}', targeting {industry} industry with the role of {target_role}. The company is {company_name}. The key pain points of the company are: {pain_points}."
                proposal_prompt = f"Create a sales proposal for {company_name}, a company in the {industry} industry. The customer's role is {target_role}. Pain points: {pain_points}. Solution: A product called {target_product}."
                email_prompt = f"Create a sales email for {company_name} in the {industry} industry. Target role: {target_role}. Pain points: {pain_points}. The product being pitched is {target_product}. The email should address the pain points and propose a solution."

                try:
                    # Initialize the AI model for generative responses
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Generate content from the AI model for each lead
                    demo_response = model.generate_content(demo_prompt)
                    proposal_response = model.generate_content(proposal_prompt)
                    email_response = model.generate_content(email_prompt)

                    # Display the generated content for each lead
                    st.subheader(f"Generated Sales Demo for {company_name}")
                    st.write(demo_response.text)
                    
                    st.subheader(f"Generated Sales Proposal for {company_name}")
                    st.write(proposal_response.text)
                    
                    st.subheader(f"Generated Email Campaign for {company_name}")
                    st.write(email_response.text)
                
                except Exception as e:
                    st.error(f"Error generating content for {company_name}: {e}")
        
    else:
        st.error("CSV file must contain columns: Company, Role, Industry, PainPoints, TargetProduct")
