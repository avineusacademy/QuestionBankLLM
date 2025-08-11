import streamlit as st
import requests
import docx
from io import BytesIO
import pdfkit
from PIL import Image
from PyPDF2 import PdfMerger
import os

BACKEND_URL = "http://backend:8000/process/"

def download_docx(questions):
    doc = docx.Document()
    for section, items in questions.items():
        doc.add_heading(section.replace('_', ' ').title(), level=2)
        for item in items:
            if isinstance(item, dict):
                doc.add_paragraph(f"Q: {item.get('question', '')}")
                for opt in item.get("options", []):
                    doc.add_paragraph(f" - {opt}")
            else:
                doc.add_paragraph(f"Q: {item}")
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def download_txt(questions):
    text = ""
    for section, items in questions.items():
        text += f"\n== {section.replace('_', ' ').title()} ==\n"
        for item in items:
            if isinstance(item, dict):
                text += f"Q: {item.get('question', '')}\n"
                for opt in item.get("options", []):
                    text += f" - {opt}\n"
            else:
                text += f"Q: {item}\n"
    return text

def convert_txt_to_pdf(text):
    return pdfkit.from_string(text, False)

def get_ordered_files(uploaded_files):
    def extract_order(file_name):
        base = os.path.splitext(file_name)[0]
        parts = base.split('_')
        try:
            return int(parts[-1])
        except:
            return 9999  # Files without order suffix go at the end
    return sorted(uploaded_files, key=lambda f: extract_order(f.name))

def create_title_pdf(title_text):
    html = f"""
    <html>
    <head><style>body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 200px; }}</style></head>
    <body><h1>{title_text}</h1></body>
    </html>
    """
    pdf_data = pdfkit.from_string(html, False)
    return BytesIO(pdf_data)

st.title("📘 Question Bank Generator from TXT/PDF")

uploaded_files = st.file_uploader("Upload TXT or PDF files", accept_multiple_files=True, type=["pdf", "txt"])

st.subheader("🖼️ Convert Image to PDF")
image_file = st.file_uploader("Upload an image (PNG, JPG)", type=["png", "jpg", "jpeg"], key="image_upload")

if image_file:
    if st.button("Convert Image to PDF"):
        try:
            image = Image.open(image_file).convert("RGB")
            img_pdf = BytesIO()
            image.save(img_pdf, format="PDF")
            img_pdf.seek(0)
            st.session_state["image_pdf"] = img_pdf  # Store image PDF in session
            st.success("Image successfully converted to PDF!")
            st.download_button("Download Image as PDF", img_pdf, file_name="converted_image.pdf")
        except Exception as e:
            st.error(f"Failed to convert image: {e}")

# 🔹 Process and display question bank
if uploaded_files:
    if st.button("Generate Question Bank"):
        with st.spinner("Processing and generating..."):
            files = [('files', (f.name, f.read(), f.type)) for f in uploaded_files]
            try:
                response = requests.post(BACKEND_URL, files=files)
                response.raise_for_status()
                data = response.json()
                content = data.get("content", "")
                questions = data.get("questions", {})

                if "error" in questions:
                    st.error(f"LLM error: {questions['error']}")
                    st.text_area("Raw LLM Response", questions.get("raw_response", ""), height=300)
                else:
                    st.subheader("📄 Combined Content")
                    st.text_area("Extracted Text", content[:3000] + "...", height=300)

                    st.subheader("🧠 Generated Questions")
                    for section, items in questions.items():
                        st.markdown(f"### {section.replace('_', ' ').title()}")
                        for item in items:
                            if isinstance(item, dict):
                                st.markdown(f"**Q:** {item.get('question', '')}")
                                for opt in item.get('options', []):
                                    st.markdown(f"- {opt}")
                            else:
                                st.markdown(f"**Q:** {item}")

                    st.subheader("⬇️ Download Options")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        docx_buffer = download_docx(questions)
                        st.download_button("Download DOCX", docx_buffer, "question_bank.docx")

                    with col2:
                        txt_data = download_txt(questions)
                        st.download_button("Download TXT", txt_data, "question_bank.txt")

                    with col3:
                        pdf_file = pdfkit.from_string(txt_data, False)
                        st.download_button("Download PDF", data=pdf_file, file_name="question_bank.pdf")

                        # Save question bank PDF in session for merging
                        st.session_state["question_bank_pdf"] = BytesIO(pdf_file)
                        st.session_state["question_bank_pdf"].seek(0)

            except requests.RequestException as e:
                st.error(f"Backend request failed: {e}")

# 🔹 Combine uploaded files + image + question bank into single PDF
st.subheader("📎 Combine Uploaded Files into One PDF")

if st.button("Merge and Download All as Single PDF"):
    merger = PdfMerger()
    ordered_files = get_ordered_files(uploaded_files)

    # Add section title for uploaded files
    title_pdf = create_title_pdf("Uploaded Files")
    merger.append(title_pdf)

    for file in ordered_files:
        file.seek(0)
        file_buffer = BytesIO(file.read())
        file.seek(0)

        if file.type == "application/pdf":
            merger.append(file_buffer)
        elif file.type == "text/plain":
            try:
                text = file_buffer.read().decode("utf-8")
                pdf_data = convert_txt_to_pdf(text)
                pdf_stream = BytesIO(pdf_data)
                merger.append(pdf_stream)
            except Exception as e:
                st.warning(f"Could not convert {file.name} to PDF. Skipped. Error: {e}")

    # Add section title and image PDF if exists
    if "image_pdf" in st.session_state:
        try:
            title_pdf = create_title_pdf("Converted Image")
            merger.append(title_pdf)

            image_pdf = st.session_state["image_pdf"]
            image_pdf.seek(0)
            merger.append(image_pdf)
            st.info("Image PDF added to the final combined PDF.")
        except Exception as e:
            st.warning(f"Failed to include image PDF: {e}")

    # Add section title and question bank PDF if exists
    if "question_bank_pdf" in st.session_state:
        try:
            title_pdf = create_title_pdf("Generated Question Bank")
            merger.append(title_pdf)

            qb_pdf = st.session_state["question_bank_pdf"]
            qb_pdf.seek(0)
            merger.append(qb_pdf)
            st.info("Question Bank PDF added to the final combined PDF.")
        except Exception as e:
            st.warning(f"Failed to include question bank PDF: {e}")

    output_pdf = BytesIO()
    merger.write(output_pdf)
    merger.close()
    output_pdf.seek(0)

    st.success("Successfully combined all files!")
    st.download_button("Download Combined PDF", output_pdf, file_name="combined_files.pdf")
