from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile
from typing import List, Optional
import os
import ocrmypdf

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins, adjust as needed
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
    fill_in = []
    mcq = []
    true_false = []
    one_mark = []
    two_mark = []
    five_mark = []

    for chunk in chunks[:5]:  # limit to 5 chunks for speed
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

def ocr_pdf_to_searchable_pdf(pdf_bytes: bytes, language_code: str) -> bytes:
    with NamedTemporaryFile(suffix=".pdf", delete=False) as input_tmp, NamedTemporaryFile(suffix=".pdf", delete=False) as output_tmp:
        input_tmp.write(pdf_bytes)
        input_tmp.flush()
        try:
            ocrmypdf.ocr(
                input_tmp.name,
                output_tmp.name,
                language=language_code,
                deskew=True,
                clean=True,
                optimize=3,
                progress_bar=False,
                use_threads=True,
                skip_text=True  # crucial to skip pages with existing text
            )
        except ocrmypdf.exceptions.PriorOcrFoundError:
            # fallback: if OCR aborted due to existing text, just pass original
            output_tmp.write(pdf_bytes)
            output_tmp.flush()
        with open(output_tmp.name, "rb") as f:
            searchable_pdf = f.read()
    os.unlink(input_tmp.name)
    os.unlink(output_tmp.name)
    return searchable_pdf

@app.post("/process/")
async def process_files(
    files: List[UploadFile] = File(...),
    language: Optional[str] = Form("eng")  # default to English
):
    content = ""
    all_chunks = []

    for file in files:
        suffix = os.path.splitext(file.filename)[-1].lower().strip(".")
        with NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            file_bytes = await file.read()
            tmp.write(file_bytes)
            tmp.flush()
            tmp_path = tmp.name

        if suffix == "pdf":
            try:
                searchable_pdf_bytes = ocr_pdf_to_searchable_pdf(file_bytes, language)
                with NamedTemporaryFile(delete=False, suffix=".pdf") as ocr_tmp:
                    ocr_tmp.write(searchable_pdf_bytes)
                    ocr_tmp.flush()
                    ocr_tmp_path = ocr_tmp.name
                chunks = extract_text_and_split(ocr_tmp_path, "pdf")
                os.unlink(ocr_tmp_path)
            except Exception:
                chunks = extract_text_and_split(tmp_path, "pdf")
        elif suffix == "txt":
            chunks = extract_text_and_split(tmp_path, "txt")
        else:
            chunks = []

        all_chunks.extend(chunks)
        for chunk in chunks:
            content += chunk.page_content + "\n"

        os.unlink(tmp_path)

    if not all_chunks:
        return {"content": content, "questions": {"error": "No valid content found."}}

    questions = generate_dummy_questions_from_chunks(all_chunks)
    return {"content": content[:5000], "questions": questions}
