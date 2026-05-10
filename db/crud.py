from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User, Transaction
import structlog

logger = structlog.get_logger()

async def get_or_create_user(session: AsyncSession, telegram_id: int, name: str | None = None) -> User:
    """Retrieve an existing user by telegram_id, or create them if they don't exist."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()
    
    if not user:
        user = User(telegram_id=telegram_id, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("New user created", telegram_id=telegram_id, name=name)
    
    return user

async def add_transaction(session: AsyncSession, user_id: int, data: dict, raw_input: str, source: str = "manual") -> Transaction:
    """Add a new transaction to the database."""
    txn = Transaction(
        user_id=user_id,
        amount=data.get("amount", 0.0),
        type=data.get("type", "expense"),
        category=data.get("category"),
        description=data.get("description"),
        raw_input=raw_input,
        source=source
    )
    session.add(txn)
    await session.commit()
    await session.refresh(txn)
    logger.info("Transaction added", user_id=user_id, amount=txn.amount, type=txn.type)
    return txn
