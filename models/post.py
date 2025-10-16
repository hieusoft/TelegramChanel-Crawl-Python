from datetime import datetime

class Post:
    TABLE_NAME = "posts"

    def __init__(self, id=None, channel_id=None, telegram_source_id=None,parent_telegram_source_id=None,
                 is_group=False, type="text",
                 created_at=None, updated_at=None):
        self.id = id
        self.channel_id = channel_id
        self.telegram_source_id = telegram_source_id
        self.parent_telegram_source_id = parent_telegram_source_id
        self.is_group = is_group
        self.type = type
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def create(self, cursor):
        """Thêm bản ghi mới vào bảng posts"""
        sql = f"""
            INSERT INTO {self.TABLE_NAME} 
            (channel_id, telegram_source_id,parent_telegram_source_id ,is_group, type, created_at, updated_at)
            VALUES (%s, %s, %s, %s,%s, %s, %s)
        """
        cursor.execute(sql, (
            self.channel_id,
            self.telegram_source_id,
            self.parent_telegram_source_id,
            self.is_group,
            self.type,
            self.created_at,
            self.updated_at
        ))
        self.id = cursor.lastrowid

    @classmethod
    def get_by_source_id(cls, cursor, channel_id, telegram_source_id):
        """Lấy bản ghi theo channel_id + telegram_source_id"""
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE channel_id=%s AND telegram_source_id=%s"
        cursor.execute(sql, (channel_id, telegram_source_id))
        data = cursor.fetchone()
        if data:
            return cls(**data)
        return None

    def update_by_source_id(self, cursor):
        """Cập nhật bản ghi theo channel_id + telegram_source_id"""
        if not self.channel_id or not self.telegram_source_id:
            raise ValueError("channel_id và telegram_source_id là bắt buộc để cập nhật")

        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET is_group=%s, type=%s, parent_telegram_source_id=%s, updated_at=%s
            WHERE channel_id=%s AND telegram_source_id=%s
        """
        cursor.execute(sql, (
            self.is_group,
            self.type,
            self.parent_telegram_source_id,
            datetime.utcnow(),
            self.channel_id,
            self.telegram_source_id
        ))

    def delete_by_source_id(self, cursor):
        """Xóa bản ghi theo channel_id + telegram_source_id"""
        if not self.channel_id or not self.telegram_source_id:
            raise ValueError("channel_id và telegram_source_id là bắt buộc để xóa")

        sql = f"DELETE FROM {self.TABLE_NAME} WHERE channel_id=%s AND telegram_source_id=%s"
        cursor.execute(sql, (self.channel_id, self.telegram_source_id))
