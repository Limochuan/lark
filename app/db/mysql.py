# app/db/mysql.py
import os
import pymysql


def get_conn():
    """
    获取一个 MySQL 数据库连接

    作用：
    - 统一管理数据库连接
    - 供 repository 层直接调用写入 / 查询数据库
    - 不做任何业务逻辑
    """

    return pymysql.connect(
        # 数据库地址（例如：127.0.0.1 / RDS 域名）
        host=os.getenv("DB_HOST"),

        # 数据库端口，默认 3306
        port=int(os.getenv("DB_PORT", "3306")),

        # 数据库用户名
        user=os.getenv("DB_USER"),

        # 数据库密码
        password=os.getenv("DB_PASSWORD"),

        # 使用的数据库名
        database=os.getenv("DB_NAME"),

        # 字符集，支持中文、emoji
        charset="utf8mb4",

        # 查询结果返回 dict，而不是 tuple
        cursorclass=pymysql.cursors.DictCursor,

        # 自动提交（INSERT / UPDATE 不需要手动 commit）
        autocommit=True,

        # 连接超时时间（秒），防止卡死
        connect_timeout=5,
    )
