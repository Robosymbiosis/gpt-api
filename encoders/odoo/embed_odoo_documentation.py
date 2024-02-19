import json
import sqlite3
import pathlib
import tiktoken
from tqdm import tqdm  # Import tqdm
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


# Text preprocessing function
def preprocess(text):
    tokens = word_tokenize(text.lower())
    tokens = [token for token in tokens if token not in stopwords.words("english")]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return " ".join(tokens)


# Download necessary NLTK data
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("punkt")

# Initialize NLTK tools
lemmatizer = WordNetLemmatizer()

# Initialize tiktoken
encoding = tiktoken.get_encoding("cl100k_base")

# Connect to SQLite Database
conn = sqlite3.connect("odoo_documentation_embeds.db")
cursor = conn.cursor()

# Ensure the table exists
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS text_embeddings (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL,
        line_number INTEGER NOT NULL,
        tokens TEXT NOT NULL
    );
    """
)

# Specify the directory path
directory_path = pathlib.Path("odoo_documentation")

# Get the list of files, excluding 'index.rst.txt'
txt_files = [f for f in directory_path.rglob("*.rst") if "index.rst" not in f.name]

# Iterate through the files with tqdm for progress tracking
for txt_file in tqdm(txt_files, desc="Processing files"):
    try:
        with open(txt_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

            # Process only if file has at least 25 lines
            if len(lines) >= 25:
                for line_number, line in enumerate(lines, start=1):
                    # Preprocess the line
                    preprocessed_line = preprocess(line)
                    # Encode the preprocessed line
                    tokens = encoding.encode(preprocessed_line)
                    tokens_json = json.dumps(tokens)
                    cursor.execute(
                        "INSERT INTO text_embeddings (file_name, line_number, tokens) VALUES (?, ?, ?)",
                        (str(txt_file), line_number, tokens_json),
                    )
                    conn.commit()
    except Exception as e:
        print(f"Error processing file {txt_file}: {e}")

# Close the connection
conn.close()
