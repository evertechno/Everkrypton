import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re
from textblob import TextBlob
from wordcloud import WordCloud
from langdetect import detect
import pyttsx3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from datetime import datetime
import pytz
import networkx as nx
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from collections import Counter
import random
import requests
from bs4 import BeautifulSoup
import yaml
from word2number import w2n
from dateutil.parser import parse
from urllib.parse import urlparse
from fuzzywuzzy import fuzz
import json

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

# TF-IDF vectorization
def tfidf_vectorize(text):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    return tfidf_matrix

# KMeans clustering of text
def kmeans_clustering(texts, n_clusters=5):
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(texts)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X)
    return kmeans.labels_

# Extract links from a webpage
def extract_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return [a.get('href') for a in soup.find_all('a', href=True)]

# Named Entity Recognition (NER) using regular expressions (basic)
def extract_entities(text):
    entities = re.findall(r'\b[A-Z][a-z]*\b', text)
    return entities

# Convert words to numbers
def words_to_number(text):
    try:
        return w2n.word_to_num(text)
    except ValueError:
        return text

# Get geolocation from address using Geopy
def get_geolocation(address):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

# Fuzzy string matching
def fuzzy_match(str1, str2):
    return fuzz.ratio(str1, str2)

# Save text to YAML format
def save_to_yaml(text):
    return yaml.dump({"text": text})

# Extract date from text
def extract_date(text):
    try:
        return parse(text).date()
    except:
        return None

# URL parsing
def parse_url(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc, parsed_url.path

# Time zone conversion
def convert_to_timezone(date_time, timezone):
    tz = pytz.timezone(timezone)
    local_time = date_time.astimezone(tz)
    return local_time

# Word frequency analysis
def word_frequency(text):
    words = text.split()
    return dict(Counter(words))

# Sentiment analysis using TextBlob
def textblob_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment

# Create text-based graph
def create_graph_from_text(text):
    words = text.split()
    graph = nx.Graph()
    for i in range(len(words) - 1):
        graph.add_edge(words[i], words[i + 1])
    return graph

# Visualize with NetworkX
def visualize_relationships(text):
    graph = create_graph_from_text(text)
    nx.draw(graph, with_labels=True, node_size=500, node_color="skyblue")
    plt.show()

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
