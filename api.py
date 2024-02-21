"""API for Robosymbiosis custom GPTs."""
import logging
from typing import Any
from typing import Dict
from typing import List

import nltk
from fastapi import FastAPI
from fastapi import HTTPException

from utils import calculate_similarities
from utils import format_search_results
from utils import perform_text_search
from utils import preprocess_to_ascii_words


logger = logging.getLogger(__name__)


app = FastAPI(
    servers=[{"url": "https://api.robosymbiosis.com", "description": "Production server"}]
)

# Download necessary NLTK data
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("punkt")

document_limit = 5


# Refactored search function
@app.get("/{database}_search/")
async def search(database: str, query: str) -> List[Dict[str, Any]]:
    """Search for a query in the specified database.

    Args:
        database (str): The name of the database to search in.
        query (str): The query to search for.

    Raises:
        HTTPException: If the database is not found.

    Returns:
        List[Dict[str, Any]]: The search results.
    """
    if database not in ["godot", "odoo", "fusion"]:
        raise HTTPException(status_code=404, detail="Database not found")

    words = preprocess_to_ascii_words(query)
    match_counts = perform_text_search(words, database)
    sorted_docs = sorted(match_counts.items(), key=lambda x: x[1], reverse=True)[:document_limit]
    similarities = calculate_similarities(sorted_docs, words, database)

    similarities.sort(key=lambda x: x[2], reverse=True)
    top_5 = similarities[:document_limit]

    formatted_results = format_search_results(top_5, database)

    return formatted_results


@app.get("/privacy-policy/")
async def privacy() -> str:
    """Return the privacy policy."""
    return "You are allowed to use this API for any purpose."
