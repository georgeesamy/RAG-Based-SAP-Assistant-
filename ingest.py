import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
import ollama
import uuid
import re


PDF_PATH = "test.pdf"

reader = PdfReader(PDF_PATH)

# Extract full text
full_text = ""

for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text += text + "\n"

# Split by numbered subsections like 2.1, 2.2, 2.3
pattern = r"(\d+\.\d+ .*?)(?=\n\d+\.\d+ |\Z)"
structured_sections = re.findall(pattern, full_text, re.DOTALL)


client = chromadb.Client(Settings(
    persist_directory="./chroma_db",
    is_persistent=True
))

collection = client.get_or_create_collection(name="sap_case_study")


def embed(text):
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]


def chunk_text(text, chunk_size=1200, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


for section_text in structured_sections:
    section_title = section_text.split("\n")[0]

    chunks = chunk_text(section_text)

    for idx, chunk in enumerate(chunks):
        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[chunk],
            embeddings=[embed(chunk)],
            metadatas=[{
                "section": section_title,
                "chunk_index": idx
            }]
        )

print("Section-based ingestion complete.")
