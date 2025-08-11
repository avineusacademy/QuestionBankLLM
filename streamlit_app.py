import streamlit as st
import requests
import docx
from io import BytesIO
import pdfkit

BACKEND_URL = "http://backend:8000/process/"  # Use 'backend' for Docker network

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

st.title("📘 Question Bank Generator from TXT/PDF")

uploaded_files = st.file_uploader("Upload TXT or PDF files", accept_multiple_files=True, type=["pdf", "txt"])

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
            except requests.RequestException as e:
                st.error(f"Backend request failed: {e}")
