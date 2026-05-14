import sys
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import settings
from bot.handlers import handle_text_message, handle_photo_message, handle_pdf_message
from bot.commands import (
    cmd_log,
    cmd_emi,
    cmd_summary,
    cmd_report,
    cmd_compare,
    cmd_export,
    cmd_history,
    cmd_search,
    cmd_backfill,
)


def main():
    bot_token = settings.telegram_bot_token
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in settings or .env file.")
        sys.exit(1)

    print("Initializing local polling bot...")

    # Build the Application
    bot_app = Application.builder().token(bot_token).build()

    # Define a custom start command for local testing
    async def start_command(update: Update, context):
        await update.message.reply_text(
            "Hello, I'm FinPilot AI! (Running locally via Polling Mode)\n"
            "Try saying: 'I spent 500 on dinner'\n\n"
            "Commands:\n"
            "/log <amount> <category> — manual entry\n"
            "/emi add <amount> <desc> — log an EMI\n"
            "/summary — this month's breakdown\n"
            "/report <start> <end> — custom date range\n"
            "/compare — income vs expenses\n"
            "/export — download CSV\n"
            "/history — last 10 transactions\n"
            "/search <query> — search transaction history\n"
            "/backfill — backfill existing entries into vector memory"
        )

    # Register handlers
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler("log", cmd_log))
    bot_app.add_handler(CommandHandler("emi", cmd_emi))
    bot_app.add_handler(CommandHandler("summary", cmd_summary))
    bot_app.add_handler(CommandHandler("report", cmd_report))
    bot_app.add_handler(CommandHandler("compare", cmd_compare))
    bot_app.add_handler(CommandHandler("export", cmd_export))
    bot_app.add_handler(CommandHandler("history", cmd_history))
    bot_app.add_handler(CommandHandler("search", cmd_search))
    bot_app.add_handler(CommandHandler("backfill", cmd_backfill))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    bot_app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf_message))
    bot_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    async def delete_webhook_and_start(app):
        import asyncio
        await bot_app.bot.delete_webhook(drop_pending_updates=True)
        print("Webhook cleared (attempt 1). Waiting for production race...")
        await asyncio.sleep(3)
        await bot_app.bot.delete_webhook(drop_pending_updates=True)
        print("Webhook cleared (attempt 2). Polling is safe to start.")

    async def restore_webhook_on_shutdown(app):
        webhook_url = settings.telegram_webhook_url
        if webhook_url:
            full_url = f"{webhook_url}/webhook/{bot_token}"
            try:
                resp = requests.get(
                    f"https://api.telegram.org/bot{bot_token}/setWebhook?url={full_url}",
                    timeout=10
                )
                data = resp.json()
                if data.get("ok"):
                    print(f"\nWebhook restored to production: {webhook_url}")
                else:
                    print(f"\nFailed to restore webhook: {data}")
            except Exception as e:
                print(f"\nFailed to restore webhook: {e}")
        else:
            print("\nNo TELEGRAM_WEBHOOK_URL set, skipping webhook restore.")

    bot_app.post_init = delete_webhook_and_start
    bot_app.post_shutdown = restore_webhook_on_shutdown

    print("Starting bot polling. Send messages in Telegram to test!")
    print("Press Ctrl+C to stop.")

    bot_app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
