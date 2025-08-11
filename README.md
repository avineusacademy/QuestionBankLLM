# Question Bank Generator from TXT/PDF Files

This project allows you to upload multiple TXT or PDF files, merges their content, and uses a Large Language Model (LLM) such as OpenAI's GPT-4 to generate a comprehensive question bank. The generated questions include various formats like fill in the blanks, multiple-choice questions, true/false, and questions of varying marks. You can download the question bank as PDF, TXT, or Word document.

---

## Features

- Upload multiple `.txt` or `.pdf` files simultaneously.
- Extract and combine text from uploaded files.
- Use GPT-4 (or a compatible LLM API) to generate diverse question types.
- Download the generated question bank in PDF, TXT, or DOCX formats.
- Built with FastAPI (backend) and Streamlit (frontend).
- Fully Dockerized for easy deployment and environment management.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- OpenAI API key (or equivalent LLM API key)

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/question-bank-generator.git
   cd question-bank-generator

docker-compose up --build

Streamlit frontend: http://localhost:8501
FastAPI docs (optional): http://localhost:8000/docs


In building machine
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-eng
sudo apt install poppler-utils
sudo apt install tesseract-ocr-hin tesseract-ocr-tam
