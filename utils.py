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


# Initialize NLTK tools
lemmatizer = WordNetLemmatizer()


# Function to preprocess text into alphanumeric ASCII words
def preprocess_to_ascii_words(text):
    tokens = word_tokenize(text.lower())
    tokens = [token for token in tokens if token not in stopwords.words("english")]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return [token for token in tokens if token.isalnum()]


# Function to execute grep search
def grep_search(word, directory="encoders/godot/godot_documentation"):
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
