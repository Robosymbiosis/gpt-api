"""Utility functions for the search engine."""
import json
import sqlite3
import subprocess
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import numpy as np
import tiktoken
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from numpy.linalg import norm
from tiktoken.core import Encoding

lemmatizer = WordNetLemmatizer()
encoding = tiktoken.get_encoding("cl100k_base")


def preprocess_to_ascii_words(text: str) -> list[str]:
    """Preprocess text into alphanumeric ASCII words.

    Args:
        text (str): The text to preprocess.

    Returns:
        list[str]: The preprocessed words.
    """
    tokens = word_tokenize(text.lower())
    tokens = [token for token in tokens if token not in stopwords.words("english")]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return [token for token in tokens if token.isalnum()]


def grep_search(word: str, directory: str = "") -> str:
    """Counts how many times a word appears in all files in a directory.

    Args:
        word (str): The word to search for.
        directory (str): The directory to recursively search in. Defaults to "".

    Returns:
        _type_: A newline separated string of search results.
    """
    if "odoo" in directory:
        file_pattern = "*.rst"
    else:
        file_pattern = "*.txt"

    cmd = ["grep", "-rH", "--include=" + file_pattern, word, directory]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return result.stdout


def get_surrounding_lines(file_path: str, line_number: int, context=20) -> list[str]:
    """Get surrounding lines of a line in a file.

    Args:
        file_path (str): The file to read from.
        line_number (int): The line number to get surrounding lines for.
        context (int): Gets the surrounding lines before and after the specified line number. Defaults to 20.

    Returns:
        list[str]: The surrounding lines.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        start = max(line_number - context - 1, 0)
        end = min(line_number + context, len(lines))
        return lines[start:end]
    except FileNotFoundError:
        return ["Error: File not found."]


def cosine_similarity(vec_a: Encoding, vec_b: Encoding) -> float:
    """Calculate the cosine similarity between two vectors.

    Args:
        vec_a (Encoding): The first vector.
        vec_b (Encoding): The second vector.

    Returns:
        float: The cosine similarity between the two vectors.
    """
    if norm(vec_a) == 0 or norm(vec_b) == 0:
        return 0
    if len(vec_a) > len(vec_b):
        vec_b = np.pad(vec_b, (0, len(vec_a) - len(vec_b)))
    elif len(vec_b) > len(vec_a):
        vec_a = np.pad(vec_a, (0, len(vec_b) - len(vec_a)))
    return np.dot(vec_a, vec_b) / (norm(vec_a) * norm(vec_b))


def count_word_occurrences(word: str, line: str) -> int:
    """Count the occurrences of a word in a line.

    Args:
        word (str): The word to search for.
        line (str): The line to search in.

    Returns:
        int: The number of occurrences of the word in the line.
    """
    return line.lower().count(word.lower())


def format_search_results(
    similarities: List[Tuple[str, int, float]], database: str
) -> List[Dict[str, Any]]:
    """Sort all the search results and format them for the API response.

    Args:
        similarities (List[Tuple[str, int, float]]): A list of the top similar search results.
        database (str): The name of the database.

    Returns:
        List[Dict[str, Any]]: The formatted search results.
    """
    formatted_results = []
    if database == "odoo":
        base_url = "https://www.odoo.com/documentation/17.0/"
    else:  # Default to Godot
        base_url = f"https://docs.{database}engine.org/en/stable/"

    for file_name, line_number, similarity in similarities:
        file_name = f"encoders/{database}/" + file_name
        surrounding_lines = get_surrounding_lines(file_name, line_number)
        if database == "godot":
            url_suffix = file_name.replace(
                f"encoders/{database}/{database}_documentation/", ""
            ).replace(".rst.txt", ".html")
        elif database == "odoo":
            # Odoo-specific transformation if needed
            url_suffix = file_name.replace(
                f"encoders/{database}/{database}_documentation/", ""
            ).replace(".rst", ".html")
        formatted_result = {
            "link": base_url + url_suffix,
            "line_number": line_number,
            "similarity": similarity,
            "context": "".join(surrounding_lines),
        }
        formatted_results.append(formatted_result)
    return formatted_results


def perform_text_search(words: List[str], database: str) -> Dict[str, float]:
    """Perform the initial text search using grep to find the most common occurances of words across the documentation.

    Args:
        words (List[str]): The words to search for.
        database (str): The name of the database.

    Returns:
        Dict[str, float]: A dictionary of file names and their match counts.
    """
    match_counts: defaultdict = defaultdict(int)
    for word in words:
        grep_result = grep_search(word, directory=f"encoders/{database}/{database}_documentation")
        for line in grep_result.split("\n"):
            if line:
                file_name, line_content = line.split(":", 1)
                occurrences = count_word_occurrences(word, line_content)
                if any(directory_substring in file_name for directory_substring in words):
                    match_counts[file_name] += 5
                else:
                    total_length = len(line_content.split())
                    if total_length > 0:
                        weighted_occurrences = occurrences / total_length
                        match_counts[file_name] += weighted_occurrences
    return match_counts


def calculate_similarities(
    sorted_docs: List[Tuple[str, float]], words: List[str], database: str
) -> List[Tuple[str, int, float]]:
    """Calculate the similarities between the search query and the database entries.

    Args:
        sorted_docs (List[Tuple[str, float]]): The sorted list of documents and their match counts.
        words (List[str]): The words to search for.
        database (str): The name of the database.

    Returns:
        List[Tuple[str, int, float]]: The list of similarities.
    """
    db_path = f"encoders/{database}/{database}_documentation_embeds.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query_embedding = encoding.encode(" ".join(words))
    similarities = []
    for file_name, _ in sorted_docs:
        file_name = file_name.replace(f"encoders/{database}/", "")
        cursor.execute(
            "SELECT line_number, tokens FROM text_embeddings WHERE file_name = ?", (file_name,)
        )
        rows = cursor.fetchall()
        for line_number, tokens_json in rows:
            tokens = json.loads(tokens_json)
            similarity = cosine_similarity(query_embedding, tokens)
            if np.isfinite(similarity):
                similarities.append((file_name, line_number, similarity))
    conn.close()
    return similarities


from typing import List, Tuple, Dict, Any
