import openai
import os
import asyncio
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

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
      "options": ["A", "B", "C", "D"]
    }}
  ],
  "true_false": ["..."],
  "one_mark": ["..."],
  "two_mark": ["..."],
  "five_mark": ["..."]
}}
"""

async def generate_questions(content: str):
    prompt = build_prompt(content)
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
    )
    
    try:
        result = response['choices'][0]['message']['content']
        return json.loads(result)
    except Exception as e:
        # Debug print (logs to backend stdout)
        print("⚠️ Failed to parse response. Raw result:\n", result)
        return {
            "error": f"Failed to parse LLM response: {str(e)}",
            "raw_response": result
        }
