from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
import os
from tempfile import NamedTemporaryFile
from typing import List

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_text_and_split(file_path: str, file_type: str) -> List[Document]:
    if file_type == "pdf":
        loader = PyPDFLoader(file_path)
    elif file_type == "txt":
        loader = TextLoader(file_path)
    else:
        return []

    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_documents(documents)
    return chunks


def generate_dummy_questions_from_chunks(chunks: List[Document]):
    # This is where you'd normally call a model
    # For now, we just generate 1 dummy question per chunk
    fill_in = []
    mcq = []
    true_false = []
    one_mark = []
    two_mark = []
    five_mark = []

    for i, chunk in enumerate(chunks[:5]):  # Limit to 5 chunks to keep things light
        text_preview = chunk.page_content[:100].strip().replace("\n", " ")

        fill_in.append(f"{text_preview} _______?")
        mcq.append({
            "question": f"What is the main idea of: {text_preview}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A"
        })
        true_false.append(f"{text_preview} (True/False)")
        one_mark.append(f"What is {text_preview}?")
        two_mark.append(f"Explain the concept in: {text_preview}.")
        five_mark.append(f"Discuss in detail: {text_preview}.")

    return {
        "fill_in_the_blanks": fill_in,
        "mcq": mcq,
        "true_false": true_false,
        "one_mark": one_mark,
        "two_mark": two_mark,
        "five_mark": five_mark
    }


@app.post("/process/")
async def process_files(files: List[UploadFile] = File(...)):
    content = ""
    all_chunks = []

    for file in files:
        suffix = os.path.splitext(file.filename)[-1].lower().strip(".")
        with NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            tmp_path = tmp.name

        if suffix in ["pdf", "txt"]:
            chunks = extract_text_and_split(tmp_path, suffix)
            all_chunks.extend(chunks)
            for chunk in chunks:
                content += chunk.page_content + "\n"

        os.unlink(tmp_path)

    if not all_chunks:
        return {"content": content, "questions": {"error": "No valid content found."}}

    questions = generate_dummy_questions_from_chunks(all_chunks)
    return {"content": content[:5000], "questions": questions}
