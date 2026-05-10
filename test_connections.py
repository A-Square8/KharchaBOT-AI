import asyncio
import os
from config.settings import settings
from db.connection import async_session
from db.crud import get_or_create_user
from agents.collector_agent import parse_transaction_text

async def main():
    print("Testing Gemini...")
    try:
        res = await parse_transaction_text("I bought a coffee for 250")
        print("Gemini result:", res)
    except Exception as e:
        print("Gemini Error:", e)

    print("\nTesting Database...")
    try:
        async with async_session() as session:
            user = await get_or_create_user(session, telegram_id=999999, name="TestUser")
            print("DB User created/found:", user.name)
    except Exception as e:
        print("DB Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
