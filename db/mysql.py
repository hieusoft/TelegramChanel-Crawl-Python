import pymysql
import json
import os
from config.config import Config

config = Config()


connection = pymysql.connect(
    host=config.get("mysql.host", "localhost"),
    user=config.get("mysql.user", "root"),
    password= config.get("mysql.password", ""),
    database=config.get("mysql.db_name", "telegram_reposter"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False
)

def get_cursor():
    return connection.cursor()
