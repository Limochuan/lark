"""
MySQL 数据库连接工具
统一从环境变量读取配置，避免写死账号密码
"""

import pymysql
import os


def get_mysql_conn():
    """
    获取 MySQL 数据库连接

    使用 utf8mb4，确保能存中文、印尼语、emoji
    cursor 使用 DictCursor，查询结果是 dict，更好用
    autocommit=True，避免忘记 commit
    """
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),                 # 数据库地址
        port=int(os.getenv("MYSQL_PORT", 3306)),      # 端口，默认 3306
        user=os.getenv("MYSQL_USER"),                 # 用户名
        password=os.getenv("MYSQL_PASSWORD"),         # 密码
        database=os.getenv("MYSQL_DB", "zhigengniao_db"),  # 数据库名
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

