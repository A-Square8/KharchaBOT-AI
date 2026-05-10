import asyncio
from config.settings import settings
from db.connection import init_db

async def main():
    print(f"Initializing database at: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    await init_db()
    print("✅ Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
