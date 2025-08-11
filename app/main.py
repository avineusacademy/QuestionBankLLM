from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from app.llm_utils import generate_questions
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process/")
async def process_files(files: list[UploadFile] = File(...)):
    content = ""
    for file in files:
        if file.filename.endswith(".pdf"):
            reader = PdfReader(file.file)
            for page in reader.pages:
                content += page.extract_text() or ""
        elif file.filename.endswith(".txt"):
            content += (await file.read()).decode("utf-8")
    
    questions = await generate_questions(content)
    return {"content": content, "questions": questions}
