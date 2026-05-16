import google.generativeai as genai
from config.settings import settings
import structlog
from datetime import date

logger = structlog.get_logger()

genai.configure(api_key=settings.gemini_api_key)

# Use the same fallback chain as the collector agent
FALLBACK_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-flash-latest',
]

_SYNTHESIS_PROMPT = """\
You are KharchaBOT, a smart personal finance assistant. A user asked a question about their expenses.
Below are the most relevant transactions retrieved from their history.

Today's date is: {today}

User Question: "{query}"

Retrieved Transactions:
{transactions}

Instructions:
- Directly answer the user's question in a friendly, concise way.
- If the question asks for a total/sum (e.g. "how much did I spend on food"), calculate and state the total amount in ₹.
- If the question asks for a list or history, format it cleanly with bullet points.
- If the question asks for a count, provide the count.
- Always mention the date range or context when relevant.
- If the retrieved transactions don't clearly answer the question, say so honestly and suggest using /report or /summary for exact date-range queries.
- Use ₹ symbol for amounts. Keep it conversational, not robotic.
- Do NOT dump raw transaction IDs or internal fields. Present only what's useful to the user.
- Keep the response under 10 lines where possible.
"""


async def synthesize_search_answer(query: str, transaction_docs: list[str]) -> str:
    """
    Takes a user's natural language query and a list of retrieved transaction
    document strings, then uses Gemini to synthesize a direct, useful answer.
    """
    if not transaction_docs:
        return (
            "I couldn't find any transactions matching your search.\n\n"
            "Tip: Use /history to see recent transactions or /report <start> <end> for a date range."
        )

    today = date.today().strftime("%d %B %Y")
    transactions_block = "\n\n".join(
        f"[{i+1}] {doc}" for i, doc in enumerate(transaction_docs)
    )

    prompt = _SYNTHESIS_PROMPT.format(
        today=today,
        query=query,
        transactions=transactions_block,
    )

    for model_name in FALLBACK_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            answer = response.text.strip()
            logger.info("Search synthesis complete", model=model_name, query=query)
            return answer
        except Exception as e:
            logger.warning(
                "Search synthesis model failed, trying next",
                model=model_name,
                error=str(e),
            )
            continue

    # Graceful fallback: format results ourselves if all models fail
    logger.error("All synthesis models failed, falling back to raw list")
    lines = [f"Here are the most relevant transactions for: '{query}'\n"]
    for i, doc in enumerate(transaction_docs, 1):
        # Extract a readable summary from the raw doc string
        parts = {
            kv.split(":")[0].strip(): kv.split(":", 1)[1].strip()
            for kv in doc.split(".")
            if ":" in kv
        }
        date_str = parts.get("Date", "?")
        cat = parts.get("Category", "?")
        amt = parts.get("Amount", "?")
        desc = parts.get("Description", "")
        lines.append(f"{i}. {date_str} | {cat} | ₹{amt} — {desc}")
    return "\n".join(lines)
