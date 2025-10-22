import asyncio
from pathlib import Path
import logging,os
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto,MessageService
import re
from models.post import Post
from models.message import Messages
from services.translator import Translator
from utils.logger import Logger
from services.media_processor import ProcessImage
from telethon.errors import RPCError

class TelegramClientWrapper:
    _fetch_client = None
    _send_client = None
    _is_connected = False
    _instance = None

    def __new__(cls, api_id, api_hash, session_fetch, session_send):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, api_id: int, api_hash: str, session_fetch: str, session_send: str):
        
        if not hasattr(self, "initialized"):
            self.api_id = api_id
            self.api_hash = api_hash
            self.session_fetch = session_fetch
            self.session_send = session_send

            self.translator = Translator()
            self.processimage = ProcessImage()

       
            TelegramClientWrapper._fetch_client = TelegramClient(session_fetch, api_id, api_hash)

          
            TelegramClientWrapper._send_client = TelegramClient(session_send, api_id, api_hash)

            self.initialized = True

    async def start_all(self):
      
        if not TelegramClientWrapper._is_connected:
            await TelegramClientWrapper._fetch_client.start()
            await TelegramClientWrapper._send_client.start()
            TelegramClientWrapper._is_connected = True
            Logger.info("✅ Telegram clients (fetch & send) started successfully")

    async def disconnect_all(self):
        """Ngắt kết nối cả 2 account"""
        if TelegramClientWrapper._is_connected:
            await TelegramClientWrapper._fetch_client.disconnect()
            await TelegramClientWrapper._send_client.disconnect()
            TelegramClientWrapper._is_connected = False
            Logger.info("🛑 Telegram clients disconnected")

    @property
    def fetch_client(self):
        """Account dùng để lấy tin nhắn"""
        return TelegramClientWrapper._fetch_client

    @property
    def send_client(self):
        """Account dùng để gửi tin nhắn"""
        return TelegramClientWrapper._send_client

    async def get_entity(self, channel_id_or_username):
        try:
            return await TelegramClientWrapper._fetch_client.get_entity(channel_id_or_username)
        except Exception as e:
            Logger.error(f"❌ Failed to get entity for {channel_id_or_username}: {e}")
            return None
    async def get_messages(self, entity, limit: int = 10):
        try:
            messages = await TelegramClientWrapper._fetch_client.get_messages(entity, limit=limit)
            return messages if messages else []
        except Exception as e:
            Logger.error(f"❌ Failed to get messages from {entity}: {e}")
            return []
    async def process_photo(self, file_path: str, channel):
        
        try:
            if not file_path or not os.path.exists(file_path):
                Logger.warning("⚠️ File không tồn tại, bỏ qua xử lý ảnh.")
                return None
            processed_path = file_path.replace("downloads", "processed")

            Path(os.path.dirname(processed_path)).mkdir(parents=True, exist_ok=True)

         
            self.processimage.replace_text(
                image_path=file_path,
                find_text=channel.old_watermark,
                new_text=channel.new_watermark,
                output_path=processed_path
            )

            Logger.info(f"🖼️ Ảnh đã xử lý xong: {processed_path}")
            return processed_path

        except Exception as e:
            Logger.error(f"❌ Lỗi xử lý ảnh: {e}")
            return None
    async def download_photo(self, message, download_dir: str, custom_name: str = None):
          
            try:
                Path(download_dir).mkdir(parents=True, exist_ok=True)

                if not isinstance(message.media, MessageMediaPhoto):
                    Logger.warning(f"⚠️ Message {message.id} không chứa ảnh, bỏ qua.")
                    return None

            
                file_name = custom_name or f"{message.id}.jpg"
                file_path = os.path.join(download_dir, file_name)

                await TelegramClientWrapper._fetch_client.download_media(message, file=file_path)

                Logger.debug(f"📥 Đã tải ảnh {message.id} → {file_path}")
                return file_path

            except Exception as e:
                Logger.error(f"❌ Failed to download photo for message {message.id}: {e}")
                return None
    
    async def send_message(self, target_channel, post, cursor):
        try:
            if not TelegramClientWrapper._is_connected:
                await self.start()

            entity = await TelegramClientWrapper._send_client.get_entity(target_channel)
            if not entity:
                Logger.error(f"❌ Không tìm thấy kênh: {target_channel}")
                return None

            messages = Messages.get_by_post_id(cursor, post.id)
            if not messages:
                Logger.debug(f"⚠️ Không có message nào trong post {post.id}")
                return None

            photos = [m for m in messages if m.media_type == "photo"]
            photos.reverse()
            texts = [m for m in messages if m.media_type == "text"]

            sent_ids = []
            reply_to_id=None
            if post.parent_telegram_source_id:
                reply_to_id = Post.get_target_by_source_id(cursor,post.channel_id,post.parent_telegram_source_id)
             
            if len(photos) > 1:
                files_to_send = [m.processed_file_path or m.original_file_path for m in photos if os.path.exists(m.processed_file_path or m.original_file_path)]
                if files_to_send:
                    caption = photos[0].translated_text or photos[0].original_text or ""
                    sent_messages = await TelegramClientWrapper._send_client.send_file(
                        entity,
                        file=files_to_send,
                        caption=caption,
                        reply_to=reply_to_id,
                        force_document=False
                    )
                    ids = [msg.id for msg in sent_messages] if isinstance(sent_messages, list) else [sent_messages.id]
                    sent_ids.extend(ids)
                    Logger.info(f"📸 Sent album ({len(ids)} ảnh) → {target_channel} | IDs: {ids}")
                    ids.reverse()
                    for m, sent_id in zip(photos, ids):
                        m.target_telegram_message_id = sent_id
                        m.update_target_by_message_id(cursor)
          
            elif len(photos) == 1:
                m = photos[0]
                file_path = m.processed_file_path or m.original_file_path
                if file_path and os.path.exists(file_path):
                    sent = await TelegramClientWrapper._send_client.send_file(
                        entity,
                        file=file_path,
                        caption=m.translated_text or m.original_text or "",
                        reply_to=reply_to_id ,
                        force_document=False
                    )
                    sent_ids.append(sent.id)
                    Logger.info(f"🖼️ Sent photo → {target_channel} | ID: {sent.id}")
                    m.target_telegram_message_id = sent.id
                    m.update_target_by_message_id(cursor)

        
            for m in texts:
                text = m.translated_text or m.original_text
                if text:
                    sent = await TelegramClientWrapper._send_client.send_message(entity, text, reply_to=reply_to_id )
                    sent_ids.append(sent.id)
                    Logger.info(f"💬 Sent text → {target_channel} | ID: {sent.id}")
                    m.target_telegram_message_id = sent.id
                    m.update_target_by_message_id(cursor)

         
            cursor.connection.commit()

            sent_ids.reverse()
            if sent_ids:
                post.target_telegram_source_id = sent_ids[0]
                post.update_target_by_source_id(cursor)
                cursor.connection.commit()  

            return sent_ids

        except RPCError as e:
            Logger.error(f"❌ Telegram RPC Error: {e}")
            return None
        except Exception as e:
            Logger.error(f"❗ Failed to send message to {target_channel}: {e} {post.id}")
            return None



    async def fetch_new_messages_for_channel(self, connection, channel, limit: int = 10):
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
                Logger.debug(f"[Channel {channel.channel_id}] ❌ Entity not found — skipping.")
                return

            messages = await self.get_messages(entity, limit=limit)
            if not messages:
                Logger.info(f"[Channel {channel.channel_id}] ⚠️ No new messages found.")
                return

            processed_groups = set()
            post_count = 0
            saved_count = 0

            posts_messages_map = {}

            for msg in messages:
           
                if msg.video or msg.gif or msg.document or msg.audio or msg.voice or msg.sticker or msg.poll or msg.web_preview or isinstance(msg, MessageService):
                    continue

                group_id = getattr(msg, "grouped_id", None) or msg.id
                if group_id in processed_groups:
                    continue
                processed_groups.add(group_id)

                post_count += 1
                if post_count > 5:
                    Logger.info(f"[Channel {channel.channel_id}] ⏹️ Reached 5 newest posts, stop fetching.")
                    break
                is_group = bool(getattr(msg, "grouped_id", None))
                album_messages = [
                    m for m in messages
                    if getattr(m, "grouped_id", None) == getattr(msg, "grouped_id", None)
                ] if is_group else [msg]

                telegram_source_id = min(m.id for m in album_messages)         
                # Skip nếu đã tồn tại
                exists = Post.get_by_source_id(cursor, channel.channel_id,telegram_source_id)
                if exists:
                    Logger.debug(f"[Channel {channel.channel_id}] 🔁 Skipping existing message ID {msg.id}")
                    continue

              
                is_photo = isinstance(getattr(msg, "media", None), MessageMediaPhoto)
                post_type = "album" if is_group else ("photo" if is_photo else "text")
                parent_message_id = getattr(msg, "reply_to_msg_id", None)
               


                post = Post(
                    channel_id=channel.channel_id,
                    telegram_source_id=telegram_source_id,
                    target_telegram_source_id=telegram_source_id,
                    parent_telegram_source_id=parent_message_id, 
                    is_group=is_group,
                    type=post_type
                )
                posts_messages_map[post] = []

             
                text = msg.text.strip() if getattr(msg, "text", None) else None
                if text:
                    text = re.sub(re.escape(channel.old_caption), channel.new_caption, text, flags=re.IGNORECASE)
                translated = self.translator.translate_text(text) if text else None

                if not getattr(msg, "media", None):
                    message_obj = Messages(
                        post_id=None,
                        telegram_message_id=msg.id,
                        target_telegram_message_id=None,
                        media_type="text",
                        original_text=text,
                        translated_text=translated,
                        original_file_path=None,
                        processed_file_path=None
                    )
                    posts_messages_map[post].append(message_obj)

   
                album_messages = [
                    m for m in messages
                    if getattr(m, "grouped_id", None) == getattr(msg, "grouped_id", None)
                ] if getattr(msg, "grouped_id", None) else [msg]

                for media_msg in album_messages:
                    if isinstance(getattr(media_msg, "media", None), MessageMediaPhoto):
                        try:
                            custom_name = f"{media_msg.id}.jpg"
                            save_dir = f"downloads/{channel.channel_id}"
                            file_path = await self.download_photo(media_msg, save_dir, custom_name=custom_name)
                            file_process_path = await self.process_photo(file_path, channel)
                        except Exception as e:
                            Logger.error(f"[Channel {channel.channel_id}] ❌ Error downloading media {media_msg.id}: {e}")
                            continue
                        text1 = (media_msg.text or "").strip()
                        if text1 :
                            text1 = re.sub(re.escape(channel.old_caption), channel.new_caption, text, flags=re.IGNORECASE)
                        translated = self.translator.translate_text(text1) if text1 else None   
                        message_obj = Messages(
                            post_id=None,
                            telegram_message_id=media_msg.id,
                            target_telegram_message_id=None,
                            media_type="photo",
                            original_text=text1,
                            translated_text=translated,
                            original_file_path=file_path,
                            processed_file_path=file_process_path
                        )
                        posts_messages_map[post].append(message_obj)
            sorted_posts = sorted(posts_messages_map.keys(), key=lambda p: p.telegram_source_id)
            for post in sorted_posts:
                parent_id = post.parent_telegram_source_id
                if parent_id:
                    parent_post = Post.get_by_source_id(cursor, channel.channel_id, parent_id)
        
                    post.parent_telegram_source_id = parent_id if parent_post else None
                post.create(cursor)
            connection.commit()
            Logger.info(f"[Channel {channel.channel_id}] 💾 Committed {len(posts_messages_map)} new posts.")

           
            for post in sorted_posts:
                for message_obj in posts_messages_map[post]:
                    message_obj.post_id = post.id
                    message_obj.create(cursor)
                    saved_count += 1
            connection.commit()
            Logger.info(f"[Channel {channel.channel_id}] 📝 Committed {saved_count} new messages.")

         
            for post in sorted_posts:  
                await self.send_message(channel.target_channel_id, post, cursor)

            Logger.info(f"[Channel {channel.channel_id}] ✅ Completed: {saved_count} new messages saved.")

        except Exception as e:
            Logger.error(f"[Channel {getattr(channel, 'channel_id', 'unknown')}] ❗ Error fetching messages: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
