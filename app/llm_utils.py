import subprocess
import json
from typing import List
from langchain_core.documents import Document

def build_prompt(content: str) -> str:
    return f"""
You are an expert teacher. Based on the following content, generate a comprehensive question bank with:

1. Fill in the blanks
2. Multiple-choice questions (4 options with correct answer)
3. True/False questions
4. 1-mark short answer questions
5. 2-mark brief explanation questions
6. 5-mark long answer descriptive questions

Content:
\"\"\"
{content[:4000]}
\"\"\"

Respond with **only valid JSON** in the following format:

{{
  "fill_in_the_blanks": ["..."],
  "mcq": [
    {{
      "question": "Sample?",
      "options": ["A", "B", "C", "D"],
      "answer": "A"
    }}
  ],
  "true_false": ["..."],
  "one_mark": ["..."],
  "two_mark": ["..."],
  "five_mark": ["..."]
}}
"""

def generate_questions_with_ollama(chunks: List[Document]) -> dict:
    # Join content from chunks to build prompt
    combined_text = "\n".join(chunk.page_content for chunk in chunks[:5])  # Limit to first 5 chunks

    prompt = build_prompt(combined_text)

    # Call Ollama CLI (assumes ollama model named 'llama2' is installed)
    try:
        # subprocess to call ollama CLI with prompt
        result = subprocess.run(
            ["ollama", "query", "llama2", "--prompt", prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()

        # Ollama returns JSON string, parse it
        questions = json.loads(output)
        return questions

    except Exception as e:
        # On failure, return dummy error
        return {
            "error": f"Failed to generate questions with Ollama: {e}",
            "raw_response": output if 'output' in locals() else ""
        }
