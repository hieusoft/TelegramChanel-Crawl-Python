from datetime import datetime

class Messages:
    TABLE_NAME = "messages"

    def __init__(self, id=None, post_id=None, telegram_message_id=None, target_telegram_message_id=None,
                 media_type="text", original_text=None, translated_text=None,
                 original_file_path=None, processed_file_path=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.post_id = post_id
        self.telegram_message_id = telegram_message_id
        self.target_telegram_message_id = target_telegram_message_id
        self.media_type = media_type
        self.original_text = original_text
        self.translated_text = translated_text
        self.original_file_path = original_file_path
        self.processed_file_path = processed_file_path
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def create(self, cursor):
        """Thêm bản ghi mới vào bảng messages"""
        sql = f"""
            INSERT INTO {self.TABLE_NAME}
            (post_id, telegram_message_id, target_telegram_message_id, media_type, original_text, translated_text,
             original_file_path, processed_file_path, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, (
            self.post_id,
            self.telegram_message_id,
            self.target_telegram_message_id,
            self.media_type,
            self.original_text,
            self.translated_text,
            self.original_file_path,
            self.processed_file_path,
            self.created_at,
            self.updated_at
        ))
        self.id = cursor.lastrowid

    @classmethod
    def get_by_post_id(cls, cursor, post_id):
        """Lấy tất cả media thuộc về 1 bài post"""
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE post_id=%s"
        cursor.execute(sql, (post_id,))
        rows = cursor.fetchall()
        return [cls(**row) for row in rows] if rows else []

    @classmethod
    def get_by_telegram_message_id(cls, cursor, telegram_message_id, target_telegram_message_id=None):
        """Lấy media theo telegram_message_id (+ target_telegram_message_id tùy chọn)"""
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE telegram_message_id=%s"
        params = [telegram_message_id]
        if target_telegram_message_id:
            sql += " AND target_telegram_message_id=%s"
            params.append(target_telegram_message_id)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return cls(**row) if row else None

    def update_by_telegram_message_id(self, cursor):
        """Cập nhật bản ghi theo telegram_message_id"""
        if not self.telegram_message_id:
            raise ValueError("telegram_message_id là bắt buộc để cập nhật")

        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET target_telegram_message_id=%s,
                media_type=%s,
                original_text=%s,
                translated_text=%s,
                original_file_path=%s,
                processed_file_path=%s,
                updated_at=%s
            WHERE telegram_message_id=%s
        """
        cursor.execute(sql, (
            self.target_telegram_message_id,
            self.media_type,
            self.original_text,
            self.translated_text,
            self.original_file_path,
            self.processed_file_path,
            datetime.utcnow(),
            self.telegram_message_id
        ))
    def update_target_by_message_id(self, cursor):
       
        if not self.telegram_message_id:
            raise ValueError("telegram_message_id là bắt buộc để cập nhật")

        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET target_telegram_message_id=%s,
                updated_at=%s
            WHERE telegram_message_id=%s
        """
        cursor.execute(sql, (
            self.target_telegram_message_id,
            datetime.utcnow(),
            self.telegram_message_id
        ))
       
        
    def delete_by_telegram_message_id(self, cursor):
        """Xóa bản ghi theo telegram_message_id (+ target_telegram_message_id nếu có)"""
        if not self.telegram_message_id:
            raise ValueError("telegram_message_id là bắt buộc để xóa")

        sql = f"DELETE FROM {self.TABLE_NAME} WHERE telegram_message_id=%s"
        params = [self.telegram_message_id]
        if self.target_telegram_message_id:
            sql += " AND target_telegram_message_id=%s"
            params.append(self.target_telegram_message_id)
        cursor.execute(sql, params)
