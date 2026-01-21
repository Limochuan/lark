"""
审批数据写入数据库的仓储层
这里不关心 HTTP / FastAPI，只负责“存数据”
"""

import json
from app.db.mysql import get_mysql_conn
