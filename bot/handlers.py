from telegram import Update
from telegram.ext import ContextTypes
from db.connection import async_session
from db.crud import get_or_create_user, add_transaction
from agents.collector_agent import parse_transaction_text
from tools.ocr import extract_text_from_photo
import structlog

logger = structlog.get_logger()


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text messages to log expenses."""
    user_msg = update.message.text
    telegram_user = update.message.from_user

    # Ignore extremely short messages that can't be a transaction
    if not user_msg or len(user_msg.strip()) < 4:
        await update.message.reply_text(
            "Message too short. Try something like: 'spent 150 on groceries'"
        )
        return

    # Let user know we are processing
    processing_msg = await update.message.reply_text("Processing your transaction...")

    # Step 1: Parse text using Gemini
    try:
        parsed_data = await parse_transaction_text(user_msg)
    except Exception as e:
        logger.error("Gemini call failed", error=str(e))
        await processing_msg.edit_text(f"[Gemini Error] {str(e)}")
        return

    if not parsed_data:
        await processing_msg.edit_text("Sorry, I couldn't understand the transaction details. Please try rephrasing.")
        return

    if "error" in parsed_data:
        await processing_msg.edit_text(f"Notice: {parsed_data['error']}")
        return

    # Step 2: Save to database
    try:
        async with async_session() as session:
            user = await get_or_create_user(
                session,
                telegram_id=telegram_user.id,
                name=telegram_user.first_name
            )
            txn = await add_transaction(
                session,
                user_id=user.id,
                data=parsed_data,
                raw_input=user_msg,
                source="manual"
            )

            reply = (
                f"Transaction Logged!\n"
                f"Date: {txn.txn_date}\n"
                f"Amount: \u20b9{float(txn.amount):,.2f}\n"
                f"Category: {txn.category}\n"
                f"Note: {txn.description}\n"
                f"Type: {txn.type.capitalize()}"
            )
            await processing_msg.edit_text(reply)

    except Exception as e:
        logger.error("Database operation failed", error=str(e))
        await processing_msg.edit_text(f"[Database Error] {str(e)}")


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages — run OCR, parse with Gemini, log to DB."""
    telegram_user = update.message.from_user
    processing_msg = await update.message.reply_text("Scanning receipt...")

    # Step 1: OCR — get the highest resolution photo
    photo = update.message.photo[-1]
    try:
        extracted_text = await extract_text_from_photo(photo, context.bot)
    except Exception as e:
        logger.error("OCR failed", error=str(e))
        await processing_msg.edit_text(f"[OCR Error] Could not read the image: {str(e)}")
        return

    if not extracted_text:
        await processing_msg.edit_text(
            "Could not extract any text from this image.\n"
            "Tip: Make sure the image is clear and well-lit."
        )
        return

    # Step 2: Parse OCR text with Gemini
    try:
        parsed_data = await parse_transaction_text(extracted_text)
    except Exception as e:
        logger.error("Gemini OCR parse failed", error=str(e))
        await processing_msg.edit_text(f"[Gemini Error] {str(e)}")
        return

    if not parsed_data:
        await processing_msg.edit_text(
            f"Scanned text:\n{extracted_text[:300]}\n\n"
            "Could not extract transaction details. Try sending the amount and category as a message instead."
        )
        return

    if "error" in parsed_data:
        await processing_msg.edit_text(f"Notice: {parsed_data['error']}")
        return

    # Step 3: Save to database
    try:
        async with async_session() as session:
            user = await get_or_create_user(
                session,
                telegram_id=telegram_user.id,
                name=telegram_user.first_name
            )
            txn = await add_transaction(
                session,
                user_id=user.id,
                data=parsed_data,
                raw_input=extracted_text,
                source="ocr"
            )

        reply = (
            f"Receipt Scanned and Logged!\n"
            f"Date: {txn.txn_date}\n"
            f"Amount: \u20b9{txn.amount}\n"
            f"Category: {txn.category}\n"
            f"Note: {txn.description}\n"
            f"Type: {txn.type.capitalize()}\n"
            f"Source: OCR"
        )
        await processing_msg.edit_text(reply)

    except Exception as e:
        logger.error("Database save failed after OCR", error=str(e))
        await processing_msg.edit_text(f"[Database Error] {str(e)}")
