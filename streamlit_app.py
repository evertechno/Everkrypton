import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from textblob import TextBlob
from wordcloud import WordCloud
from langdetect import detect
import pyttsx3

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-powered Data Structuring and Analysis")
st.write("Turn unstructured text data into structured data with AI. Perform extraction, summarization, classification, and more.")

# File upload options
uploaded_file = st.file_uploader("Upload a file (Text, CSV, DOCX, JSON)", type=["txt", "csv", "docx", "json"])
unstructured_data = None

# Process file upload
if uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        unstructured_data = uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
    elif uploaded_file.type == "application/json":
        json_data = json.load(uploaded_file)
        st.write("JSON data uploaded:", json.dumps(json_data, indent=2))

# If no file uploaded, use text input
if unstructured_data is None:
    unstructured_data = st.text_area("Enter unstructured data:", height=200)

# Clean the unstructured text (remove extra spaces, punctuation, etc.)
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text

# Sentiment analysis with TextBlob
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    return "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"

# Language detection
def detect_language(text):
    try:
        return detect(text)
    except:
        return "Unknown"

# Summarize text using AI
def summarize_text(text):
    prompt = f"Summarize the following text: {text}"
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# Keyword extraction using basic frequency analysis
def extract_keywords(text, top_n=10):
    words = text.split()
    word_freq = {word: words.count(word) for word in set(words)}
    sorted_keywords = sorted(word_freq.items(), key=lambda item: item[1], reverse=True)
    return [keyword[0] for keyword in sorted_keywords[:top_n]]

# Word cloud generation
def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)
    return wordcloud

# Text-to-Speech
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Button to process text and display results
if st.button("Process Data"):
    try:
        if unstructured_data.strip():
            # Process the data
            cleaned_data = clean_text(unstructured_data)
            sentiment = analyze_sentiment(cleaned_data)
            summary = summarize_text(cleaned_data)
            keywords = extract_keywords(cleaned_data)
            language = detect_language(unstructured_data)
            
            st.subheader("Cleaned Text:")
            st.write(cleaned_data)

            # Sentiment analysis
            st.write(f"Sentiment: {sentiment}")

            # Language detection
            st.write(f"Detected Language: {language}")

            # Text Summarization
            st.subheader("Summary:")
            st.write(summary)

            # Keyword Extraction
            st.write("Extracted Keywords:", keywords)

            # Generate Word Cloud
            wordcloud = generate_wordcloud(unstructured_data)
            st.image(wordcloud.to_array(), use_column_width=True)

            # Allow user to download the structured data in CSV or JSON format
            structured_data = {
                "sentiment": sentiment,
                "summary": summary,
                "keywords": keywords,
                "language": language
            }

            download_format = st.selectbox("Select download format", ["JSON", "CSV"])
            if download_format == "CSV":
                df = pd.DataFrame([structured_data])
                st.download_button("Download CSV", df.to_csv(index=False), "structured_data.csv")
            else:
                st.download_button("Download JSON", json.dumps(structured_data), "structured_data.json")
        else:
            st.error("Please enter some unstructured data to process.")
    except Exception as e:
        st.error(f"Error: {e}")

# Text-to-Speech Feature
if st.checkbox("Convert Text to Speech"):
    text_to_speech(unstructured_data)

# Help Section
st.sidebar.title("Help & Instructions")
st.sidebar.write("""
    1. Upload unstructured text (or CSV/JSON).
    2. Use the buttons to perform sentiment analysis, entity extraction, and more.
    3. View and download the structured data in JSON or CSV format.
""")
