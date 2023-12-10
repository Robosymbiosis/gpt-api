from fastapi import FastAPI
import sqlite3
import json
import numpy as np
import tiktoken
from numpy.linalg import norm
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import subprocess
from collections import defaultdict
import logging


logger = logging.getLogger(__name__)


app = FastAPI(
    servers=[{"url": "https://godot.robosymbiosis.com", "description": "Production server"}]
)

# Download necessary NLTK data
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("punkt")

document_limit = 5

# Initialize NLTK tools
lemmatizer = WordNetLemmatizer()

# Initialize tiktoken
encoding = tiktoken.get_encoding("cl100k_base")


# Function to preprocess text into alphanumeric ASCII words
def preprocess_to_ascii_words(text):
    tokens = word_tokenize(text.lower())
    tokens = [token for token in tokens if token not in stopwords.words("english")]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return [token for token in tokens if token.isalnum()]


# Function to execute grep search
def grep_search(word, directory="godot_documentation"):
    cmd = ["grep", "-rH", "--include=*.txt", word, directory]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout


# Function to get surrounding lines
def get_surrounding_lines(file_path, line_number, context=20):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        start = max(line_number - context - 1, 0)
        end = min(line_number + context, len(lines))
        return lines[start:end]
    except FileNotFoundError:
        return ["Error: File not found."]


# Function to calculate cosine similarity
def cosine_similarity(vec_a, vec_b):
    if norm(vec_a) == 0 or norm(vec_b) == 0:
        return 0
    if len(vec_a) > len(vec_b):
        vec_b = np.pad(vec_b, (0, len(vec_a) - len(vec_b)))
    elif len(vec_b) > len(vec_a):
        vec_a = np.pad(vec_a, (0, len(vec_b) - len(vec_a)))
    return np.dot(vec_a, vec_b) / (norm(vec_a) * norm(vec_b))


# Function to count word occurrences in a line
def count_word_occurrences(word, line):
    return line.lower().count(word.lower())


@app.get("/godot_search/")
async def search(query: str):
    words = preprocess_to_ascii_words(query)
    match_counts = defaultdict(int)

    # Execute grep search and count weighted matches
    for word in words:
        grep_result = grep_search(word)
        for line in grep_result.split("\n"):
            if line:
                file_name, line_content = line.split(":", 1)
                occurrences = count_word_occurrences(word, line_content)

                # Check if any word matches a substring of the directory
                if any(directory_substring in file_name for directory_substring in words):
                    # If it matches a directory substring, add 5 to the weight
                    match_counts[file_name] += 1
                else:
                    # Calculate the weight based on the total length of the document
                    total_length = len(line_content.split())
                    if total_length > 0:
                        weighted_occurrences = occurrences / total_length
                        match_counts[file_name] += weighted_occurrences

    # Sort and select top 20 documents
    sorted_docs = sorted(match_counts.items(), key=lambda x: x[1], reverse=True)[:document_limit]

    # Connect to SQLite Database for similarity search
    conn = sqlite3.connect("godot_documentation_embeds.db")
    cursor = conn.cursor()

    # Preprocess and then embed the query for similarity comparison
    query_embedding = encoding.encode(" ".join(words))

    # Calculate similarity for top-ranked documents
    similarities = []
    for file_name, _ in sorted_docs:
        cursor.execute(
            "SELECT line_number, tokens FROM text_embeddings WHERE file_name = ?", (file_name,)
        )
        rows = cursor.fetchall()
        for line_number, tokens_json in rows:
            tokens = json.loads(tokens_json)
            similarity = cosine_similarity(query_embedding, tokens)
            if np.isfinite(similarity):
                similarities.append((file_name, line_number, similarity))

    # Sort by similarity
    similarities.sort(key=lambda x: x[2], reverse=True)

    # Get top 5 similar embeddings
    top_5 = similarities[:document_limit]

    base_url = "https://docs.godotengine.org/en/stable/"

    formatted_results = []
    for file_name, line_number, similarity in top_5:
        surrounding_lines = get_surrounding_lines(file_name, line_number)

        # Remove 'godot_documentation/' and replace path separators and file extension
        url_suffix = file_name.replace("godot_documentation/", "").replace(".rst.txt", ".html")

        formatted_result = {
            "link": base_url + url_suffix,
            "line_number": line_number,
            "similarity": similarity,
            "context": "".join(surrounding_lines),
        }
        formatted_results.append(formatted_result)

    # Close the database connection
    conn.close()

    return formatted_results


@app.get("/privacy-policy/")
async def privacy():
    return "You are allowed to use this API for any purpose."
