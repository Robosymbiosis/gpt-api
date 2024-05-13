#!/bin/bash

# Specify the database (godot, odoo, or fusion)
database="odoo"

# Query string variable
query_string="how do I add a a product via the API?"

# URL encode the query string
encoded_query=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$query_string'''))")

# Perform the curl request and process the response with jq
curl -X 'GET' "http://127.0.0.1:8000/${database}_search/?query=$encoded_query" -H 'accept: application/json' | jq -r '.[] | @text'
