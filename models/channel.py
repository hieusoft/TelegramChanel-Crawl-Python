class Channel:
    TABLE_NAME = "channels"

    def __init__(self, id=None, channel_id=None, target_channel_id=None,
                 old_watermark="", new_watermark="", apply_watermark=True,
                 status="active", created_at=None, updated_at=None):
        self.id = id
        self.channel_id = channel_id
        self.target_channel_id = target_channel_id
        self.old_watermark = old_watermark
        self.new_watermark = new_watermark
        self.apply_watermark = apply_watermark
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def create(self, cursor):
        sql = f"""INSERT INTO {self.TABLE_NAME} 
                 (channel_id, target_channel_id, old_watermark, new_watermark, apply_watermark, status)
                 VALUES (%s,%s,%s,%s,%s,%s)"""
        cursor.execute(sql, (self.channel_id, self.target_channel_id, self.old_watermark,
                             self.new_watermark, int(self.apply_watermark), self.status))
        self.id = cursor.lastrowid

    @classmethod
    def get_by_channel_id(cls, cursor, channel_id):
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE channel_id=%s"
        cursor.execute(sql, (channel_id,))
        data = cursor.fetchone()
        if data:
            return cls(**data)
        return None

    def update_by_channel_id(self, cursor):
        if not self.channel_id:
            raise ValueError("channel_id is required for update")
        sql = f"""UPDATE {self.TABLE_NAME} SET 
                target_channel_id=%s, old_watermark=%s, new_watermark=%s,
                apply_watermark=%s, status=%s
                WHERE channel_id=%s"""
        cursor.execute(sql, (self.target_channel_id, self.old_watermark, self.new_watermark,
                            int(self.apply_watermark), self.status, self.channel_id))

    def delete_by_channel_id(self, cursor):
        if not self.channel_id:
            raise ValueError("channel_id is required for delete")
        sql = f"DELETE FROM {self.TABLE_NAME} WHERE channel_id=%s"
        cursor.execute(sql, (self.channel_id,))

    @classmethod
    def list_channels(cls, cursor, status="active"):
        sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE status=%s"
        cursor.execute(sql, (status,))
        rows = cursor.fetchall()
        return [cls(**row) for row in rows]
