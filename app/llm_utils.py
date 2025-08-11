import json
import re
from typing import List
from langchain_core.documents import Document

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline

# ✅ Use a public, open-access model
model_name = "tiiuae/falcon-7b-instruct"

# Load tokenizer and model without requiring auth
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Use HuggingFace pipeline
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=1024,
    temperature=0.7,
    do_sample=True,
)

llm = HuggingFacePipeline(pipeline=pipe)


# Clean text before sending to model
def clean_text(raw_text: str) -> str:
    text = re.sub(r'\n+', '\n', raw_text)
    text = re.sub(r'Page\s*\d+', '', text, flags=re.I)
    text = re.sub(r'(Unit|Chapter)\s*\d+', '', text, flags=re.I)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


# Build the prompt
def build_prompt(content: str) -> str:
    return f"""
You are an expert teacher and question paper designer.

From the educational content provided below, generate a high-quality question bank in **valid JSON format only**.

✅ Instructions:
- Use your own words to frame meaningful, exam-ready questions.
- Avoid copying titles/headings directly as question text.
- Make sure MCQs have 4 unique options and only one correct answer.
- Do NOT add explanations or extra formatting.
- Keep output clean, readable and structured as JSON.

Generate the following:
1. 3 Fill in the blanks
2. 3 Multiple-choice questions (4 options + correct answer)
3. 3 True/False statements
4. 3 One-mark short answer questions
5. 2 Two-mark explanation questions
6. 1 Five-mark descriptive question

Return exactly this JSON format:
{{
  "fill_in_the_blanks": ["..."],
  "mcq": [
    {{
      "question": "...?",
      "options": ["A", "B", "C", "D"],
      "answer": "A"
    }}
  ],
  "true_false": ["..."],
  "one_mark": ["..."],
  "two_mark": ["..."],
  "five_mark": ["..."]
}}

Educational Content:
\"\"\"
{content[:3000]}
\"\"\"
"""


# Extract only the JSON part from the response
def extract_json(response: str) -> dict:
    try:
        match = re.search(r'{.*}', response, re.DOTALL)
        if not match:
            raise ValueError("No JSON block found")
        return json.loads(match.group(0))
    except Exception as e:
        return {
            "error": f"JSON parsing failed: {str(e)}",
            "raw_response": response[:2000]
        }


# Main generator
def generate_questions_with_ollama(chunks: List[Document]) -> dict:
    combined_text = "\n".join(clean_text(chunk.page_content) for chunk in chunks[:5])
    prompt = build_prompt(combined_text)

    try:
        output = llm.invoke(prompt)
        return extract_json(output)
    except Exception as e:
        return {
            "error": f"LLM generation failed: {str(e)}",
            "raw_response": ""
        }
