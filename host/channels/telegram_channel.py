"""Telegram channel implementation using python-telegram-bot"""
import logging
from typing import Callable, Awaitable, Optional
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from .. import config
from ..env import read_env_file

log = logging.getLogger(__name__)

class TelegramChannel:
    name = "telegram"

    def __init__(self, on_message: Callable, on_chat_metadata: Callable, registered_groups: list):
        self._on_message = on_message
        self._on_chat_metadata = on_chat_metadata
        self._registered_groups = registered_groups
        self._app: Optional[Application] = None
        token = read_env_file(["TELEGRAM_BOT_TOKEN"]).get("TELEGRAM_BOT_TOKEN", "")
        self._token = token

    def _jid(self, chat_id: int) -> str:
        return f"tg:{chat_id}"

    def owns_jid(self, jid: str) -> bool:
        return jid.startswith("tg:")

    def is_connected(self) -> bool:
        return self._app is not None and self._app.running

    async def connect(self) -> None:
        if not self._token:
            log.warning("TELEGRAM_BOT_TOKEN not set — Telegram disabled")
            return

        import asyncio
        MAX_RETRIES = 3
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._app = Application.builder().token(self._token).build()

                async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
                    if not update.message or not update.message.text:
                        return
                    jid = self._jid(update.effective_chat.id)
                    sender = str(update.effective_user.id) if update.effective_user else "unknown"
                    sender_name = update.effective_user.full_name if update.effective_user else "Unknown"
                    text = update.message.text

                    groups = {g["jid"]: g for g in self._registered_groups}
                    group = groups.get(jid)
                    if group and group.get("requires_trigger", True):
                        if not text.lower().startswith(f"@{config.ASSISTANT_NAME.lower()}"):
                            return

                    await self._on_message(
                        jid=jid,
                        sender=sender,
                        sender_name=sender_name,
                        content=text,
                        is_group=update.effective_chat.type in ("group", "supergroup"),
                        channel="telegram",
                    )

                self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
                await self._app.initialize()
                await self._app.start()
                await self._app.updater.start_polling()
                log.info("Telegram channel connected")
                return  # success
            except Exception as e:
                err_str = str(e).lower()
                if "conflict" in err_str:
                    log.error(
                        "Telegram: Conflict detected — another bot instance is already running. "
                        "Stop the other instance and restart."
                    )
                    raise  # Conflict is unrecoverable, re-raise immediately

                if attempt < MAX_RETRIES:
                    wait = 2 ** attempt  # 2s, 4s
                    log.warning(
                        f"Telegram connect attempt {attempt}/{MAX_RETRIES} failed "
                        f"({type(e).__name__}: {e}) — retrying in {wait}s"
                    )
                    # Clean up failed app before retry
                    try:
                        if self._app:
                            await self._app.shutdown()
                    except Exception:
                        pass
                    self._app = None
                    await asyncio.sleep(wait)
                else:
                    log.error(
                        f"Telegram connect failed after {MAX_RETRIES} attempts: {type(e).__name__}: {e}"
                    )
                    raise

    async def send_message(self, jid: str, text: str) -> None:
        if not self._app:
            return
        chat_id = int(jid.replace("tg:", ""))
        await self._app.bot.send_message(chat_id=chat_id, text=text)

    async def send_file(self, jid: str, file_path: str, caption: str = "") -> None:
        """Send a document/file to a Telegram chat."""
        import pathlib
        import traceback

        # --- DEBUG LOG START ---
        debug_log_path = "/workspace/group/debug_send.log"
        def write_debug(msg):
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(f"[DEBUG] {msg}\n")
            except Exception as e:
                pass
        # --- DEBUG LOG END ---

        write_debug(f"=== START send_file ===")
        write_debug(f"Target JID: {jid}, File: {file_path}")

        if not self._app:
            write_debug("ERROR: self._app is None")
            return

        p = pathlib.Path(file_path)
        if not p.exists():
            write_debug(f"ERROR: File not found: {p}")
            await self.send_message(jid, f"⚠️ File not found: {p.name}")
            return

        chat_id = int(jid.replace("tg:", ""))
        write_debug(f"Chat ID: {chat_id}, File Size: {p.stat().st_size} bytes")

        try:
            write_debug("Attempting to read file in binary mode...")
            # CRITICAL FIX: Read file as binary to avoid encoding issues (e.g., cp950 errors)
            with open(p, "rb") as f:
                file_data = f.read()
            
            write_debug(f"File read successful. Data length: {len(file_data)}")
            write_debug(f"Calling send_document API...")

            # Send the file data directly
            await self._app.bot.send_document(
                chat_id=chat_id,
                document=file_data,
                filename=p.name,
                caption=caption or f"📎 {p.name}",
            )

            write_debug("API call successful!")
            log.info(f"Successfully sent file {p.name} to {jid}")

        except Exception as exc:
            error_trace = traceback.format_exc()
            write_debug(f"ERROR Exception: {exc}")
            write_debug(f"Traceback: {error_trace}")
            log.error(f"Failed to send file {p.name} to {jid}: {exc}", exc_info=True)

            # Fallback: notify user
            try:
                await self.send_message(jid, f"⚠️ Failed to send file '{p.name}': {exc}")
            except Exception as msg_exc:
                log.error(f"Also failed to send error message: {msg_exc}")
        finally:
            write_debug("=== END send_file ===\n")

    async def send_typing(self, jid: str) -> None:
        if not self._app:
            return
        try:
            from telegram.constants import ChatAction
            chat_id = int(jid.replace("tg:", ""))
            await self._app.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception as e:
            log.debug(f"Typing indicator failed: {e}")

    async def disconnect(self) -> None:
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
