import json
import google.generativeai as genai
from config.settings import settings
import structlog

logger = structlog.get_logger()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT_TEMPLATE = """
You are an expert financial assistant. Extract the transaction details from the user's message.
Return ONLY a valid JSON object. Do not include markdown formatting, backticks, or extra text.

Rules for extraction:
- amount: (float) the numeric value of the transaction.
- type: (string) exactly one of ["expense", "income", "emi", "investment"].
- category: (string) a short 1-2 word category (e.g., "Food", "Transport", "Salary", "Rent", "Groceries", "Car Loan").
- description: (string) a brief summary of the transaction.

User Message: "{user_input}"
"""

async def parse_transaction_text(user_input: str) -> dict | None:
    """Use Gemini to parse natural language transaction text into a structured dictionary."""
    prompt = PROMPT_TEMPLATE.format(user_input=user_input)
    try:
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        
        # Clean up possible markdown code blocks from Gemini response
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        return data
    except Exception as e:
        logger.error("Failed to parse transaction text", error=str(e), user_input=user_input)
        return None
