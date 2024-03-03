#!/bin/bash

# Define the endpoint URL for localhost
# Assuming FastAPI runs on the default port 8000
ENDPOINT_URL="http://127.0.0.1:8000/search/"

# Specify the database and query parameters
DATABASE="fusion"  # Example database
QUERY="Can you show me an example of parameterizing a sketch with the API?"  # Example query

# URL encode the query
# This is a simple way to handle spaces in queries, but might not handle all special characters.
ENCODED_QUERY=$(echo $QUERY | sed 's/ /%20/g')

# Construct the full URL with parameters
FULL_URL="${ENDPOINT_URL}?database=${DATABASE}&query=${ENCODED_QUERY}"

# Use curl to perform the GET request
curl "$FULL_URL"
