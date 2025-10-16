import asyncio
from pathlib import Path
import logging
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

from models.post import Post
from models.message import Messages
from services.translator import Translator
from utils.logger import Logger


class TelegramClientWrapper:
    _client = None
    _is_connected = False
    _instance = None

    def __new__(cls, api_id, api_hash, session_file):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_id: int, api_hash: str, session_file: str):
        if not hasattr(self, "initialized"):
            self.api_id = api_id
            self.api_hash = api_hash
            self.session_file = session_file
            self.translator = Translator()
            TelegramClientWrapper._client = TelegramClient(session_file, api_id, api_hash)
            self.initialized = True

    async def start(self):
        if not TelegramClientWrapper._is_connected:
            await TelegramClientWrapper._client.start()
            TelegramClientWrapper._is_connected = True
            Logger.info("✅ Telegram client started successfully")

    async def disconnect(self):
        if TelegramClientWrapper._is_connected:
            await TelegramClientWrapper._client.disconnect()
            TelegramClientWrapper._is_connected = False
            Logger.info("🛑 Telegram client disconnected")

    async def get_entity(self, channel_id_or_username):
        try:
            return await TelegramClientWrapper._client.get_entity(channel_id_or_username)
        except Exception as e:
            Logger.error(f"❌ Failed to get entity for {channel_id_or_username}: {e}")
            return None

    async def get_messages(self, entity, limit: int = 10):
        try:
            messages = await TelegramClientWrapper._client.get_messages(entity, limit=limit)
            return list(reversed(messages)) if messages else []
        except Exception as e:
            Logger.error(f"❌ Failed to get messages from {entity}: {e}")
            return []

    async def download_photo(self, message, download_path: str):
        Path(download_path).mkdir(parents=True, exist_ok=True)
        if isinstance(message.media, MessageMediaPhoto):
            try:
                return await TelegramClientWrapper._client.download_media(message, file=download_path)
            except Exception as e:
                Logger.error(f"❌ Failed to download photo for message {message.id}: {e}")
        return None

    async def fetch_new_messages_for_channel(self, connection, channel, limit: int = 5):
        messages = []
        cursor = connection.cursor()

        try:
            raw = str(channel.channel_id)
            if raw.startswith("-100"):
                channel_id = int(raw)
            elif raw.startswith("-"):
                channel_id = int(raw)
            else:
                channel_id = int(f"-100{raw}")

            Logger.info(f"🔍 Fetching messages from channel {channel.channel_id} (limit={limit})")

            entity = await self.get_entity(channel_id)
            if not entity:
                Logger.warning(f"[Channel {channel.channel_id}] ❌ Entity not found — skipping.")
                return

            messages = await self.get_messages(entity, limit=limit)
            if not messages:
                Logger.info(f"[Channel {channel.channel_id}] ⚠️ No new messages found.")
                return

            processed_groups = set()
            saved_count = 0

            for msg in messages:
                if not getattr(msg, "text", None) and not isinstance(msg.media, MessageMediaPhoto):
                    continue

                group_id = getattr(msg, "grouped_id", None) or msg.id
                if group_id in processed_groups:
                    continue
                processed_groups.add(group_id)

                exists = Post.get_by_source_id(cursor, channel.channel_id, msg.id)
                if exists:
                    Logger.debug(f"[Channel {channel.channel_id}] 🔁 Skipping existing message ID {msg.id}")
                    continue

                parent_message_id = getattr(msg, "reply_to_msg_id", None)
                parent_id_to_store = None
                if parent_message_id is not None:
                    parent_post = Post.get_by_source_id(cursor, channel.channel_id, parent_message_id)
                    parent_id_to_store = parent_message_id if parent_post else None

                is_group = bool(getattr(msg, "grouped_id", None))
                is_photo = isinstance(getattr(msg, "media", None), MessageMediaPhoto)
                post_type = "album" if is_group else ("photo" if is_photo else "text")

                post = Post(
                    channel_id=channel.channel_id,
                    telegram_source_id=msg.id,
                    parent_telegram_source_id=parent_id_to_store,
                    is_group=is_group,
                    type=post_type
                )
                post.create(cursor)
                connection.commit()

                Logger.info(f"[Channel {channel.channel_id}] 💾 Saved new post (msg_id={msg.id}, type={post_type})")

                text = msg.text.strip() if getattr(msg, "text", None) else None
                translated = self.translator.translate(text) if text else None

                if not getattr(msg, "media", None):
                    media = Messages(
                        post_id=post.id,
                        telegram_message_id=msg.id,
                        media_type="text",
                        original_text=text,
                        translated_text=translated,
                        original_file_path=None,
                        processed_file_path=None
                    )
                    media.create(cursor)
                    connection.commit()
                    saved_count += 1
                    Logger.debug(f"[Channel {channel.channel_id}] 📝 Saved text message (msg_id={msg.id})")

                album_messages = [m for m in messages if getattr(m, "grouped_id", None) == getattr(msg, "grouped_id", None)] if getattr(msg, "grouped_id", None) else [msg]

                for media_msg in album_messages:
                    if isinstance(getattr(media_msg, "media", None), MessageMediaPhoto):
                        try:
                            file_path = await self.download_photo(media_msg, f"downloads/{channel.channel_id}")
                            file_process_path = file_path.replace("downloads", "process")

                        except Exception as e:
                            Logger.error(f"[Channel {channel.channel_id}] ❌ Error downloading media {media_msg.id}: {e}")
                            file_path = None

                        if file_path:
                            media = Messages(
                                post_id=post.id,
                                telegram_message_id=media_msg.id,
                                media_type="photo",
                                original_text=(media_msg.text.strip() if getattr(media_msg, "text", None) else text),
                                translated_text=(self.translator.translate(media_msg.text.strip()) if getattr(media_msg, "text", None) else translated),
                                original_file_path=file_path,
                                processed_file_path=file_process_path
                            )
                            media.create(cursor)
                            connection.commit()
                            saved_count += 1
                            Logger.debug(f"[Channel {channel.channel_id}] 📸 Saved photo (msg_id={media_msg.id}) at {file_path}")
           
            Logger.info(f"[Channel {channel.channel_id}] ✅ Completed: {saved_count} new messages saved.")

        except Exception as e:
            Logger.exception(f"[Channel {getattr(channel, 'channel_id', 'unknown')}] ❗ Error fetching messages: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
