import chromadb
from chromadb.config import Settings
import ollama


client = chromadb.Client(Settings(
    persist_directory="./chroma_db",
    is_persistent=True
))

collection = client.get_collection(name="sap_case_study")


def embed(text):
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]


def ask(question):
    question_lower = question.lower()
    query_embedding = embed(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=4,
        include=["documents", "metadatas", "distances"]
    )

    distances = results["distances"][0]
    best_distance = distances[0]

    print("DEBUG distance:", best_distance)

    SIMILARITY_THRESHOLD = 400  # adjust if needed

    if best_distance > SIMILARITY_THRESHOLD:
        return "This question is not covered in the provided PDF."

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # Boost exact section title match
    for meta in metadatas:
        section_title = meta["section"].lower()
        if all(word in section_title for word in question_lower.split()):
            target_section = meta["section"]
            break
    else:
        target_section = metadatas[0]["section"]

    # Retrieve ALL chunks of that section
    all_section_chunks = collection.get(
        where={"section": target_section}
    )

    section_docs = all_section_chunks["documents"]
    section_metas = all_section_chunks["metadatas"]

    # Sort chunks by original order
    section_data = [
        (doc, meta["chunk_index"])
        for doc, meta in zip(section_docs, section_metas)
    ]

    sorted_chunks = [
        doc for doc, idx in sorted(section_data, key=lambda x: x[1])
    ]

    print("CHUNKS:", len(sorted_chunks))


    context = "\n".join(sorted_chunks)

    prompt = f"""
Format the following section for clarity and readability.

Rules:
- Do NOT remove any instructional content.
- Do NOT reorder content.
- Preserve all code exactly.
- Completely REMOVE any lines that contain the word "Figure".
- Do NOT rewrite, summarize, or reference any figures.
- Do NOT replace figure lines with parentheses.
- Do NOT mention figures in any way.
- Add headings only if naturally implied by the text.
- Improve spacing and indentation.
- Keep original wording.

Section:
{context}
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0,
            "num_ctx": 4096
        }
    )

    return response["message"]["content"]


if __name__ == "__main__":
    while True:
        q = input("\nAsk a question (or type 'exit'): ")
        if q.lower() == "exit":
            break

        print("\nAnswer:\n", ask(q))
