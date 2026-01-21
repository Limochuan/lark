"""
审批数据写入数据库的仓储层（Repository）

职责说明：
1. 只负责 MySQL 数据写入
2. 不关心 FastAPI / HTTP / 飞书 API
3. 不做业务判断、不抛业务异常
4. 所有方法都由 service 层调用

对应数据表：
- lark_approval_raw         原始回调 / 接口返回数据
- lark_approval_instance    审批实例主表
- lark_approval_task        审批任务 / 节点
- lark_approval_form_field  表单字段数据
"""

import json
from typing import Dict, Any, List

from app.db.mysql import get_mysql_conn


class ApprovalRepository:
    """
    审批数据仓储类
    """

    # =========================
    # 通用工具方法
    # =========================

    @staticmethod
    def _json_dumps(data: Any) -> str:
        """
        dict / list → JSON 字符串（统一处理）
        """
        return json.dumps(data, ensure_ascii=False)

    # =========================
    # 1. 原始数据表
    # =========================

    def save_raw_data(self, instance_code: str, payload: Dict[str, Any]) -> None:
        """
        保存飞书返回的完整原始数据（兜底用）

        表：lark_approval_raw
        """
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO lark_approval_raw (
                    instance_code,
                    raw_json
                )
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    raw_json = VALUES(raw_json)
                """
                cursor.execute(
                    sql,
                    (
                        instance_code,
                        self._json_dumps(payload),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    # =========================
    # 2. 审批实例主表
    # =========================

    def save_instance(self, instance: Dict[str, Any]) -> None:
        """
        保存审批实例主信息

        表：lark_approval_instance
        """
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO lark_approval_instance (
                    instance_code,
                    approval_code,
                    status,
                    start_time,
                    end_time,
                    user_id,
                    raw_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    end_time = VALUES(end_time),
                    raw_json = VALUES(raw_json)
                """

                cursor.execute(
                    sql,
                    (
                        instance.get("instance_code"),
                        instance.get("approval_code"),
                        instance.get("status"),
                        instance.get("start_time"),
                        instance.get("end_time"),
                        instance.get("user_id"),
                        self._json_dumps(instance),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    # =========================
    # 3. 审批任务 / 节点
    # =========================

    def save_tasks(self, instance_code: str, tasks: List[Dict[str, Any]]) -> None:
        """
        保存审批任务节点

        表：lark_approval_task
        """
        if not tasks:
            return

        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO lark_approval_task (
                    task_id,
                    instance_code,
                    user_id,
                    status,
                    start_time,
                    end_time,
                    raw_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    end_time = VALUES(end_time),
                    raw_json = VALUES(raw_json)
                """

                for task in tasks:
                    cursor.execute(
                        sql,
                        (
                            task.get("id"),
                            instance_code,
                            task.get("user_id"),
                            task.get("status"),
                            task.get("start_time"),
                            task.get("end_time"),
                            self._json_dumps(task),
                        ),
                    )
            conn.commit()
        finally:
            conn.close()

    # =========================
    # 4. 表单字段
    # =========================

    def save_form_fields(
        self, instance_code: str, fields: List[Dict[str, Any]]
    ) -> None:
        """
        保存审批表单字段

        表：lark_approval_form_field
        """
        if not fields:
            return

        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO lark_approval_form_field (
                    instance_code,
                    field_id,
                    field_name,
                    field_type,
                    field_value,
                    raw_json
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """

                for field in fields:
                    cursor.execute(
                        sql,
                        (
                            instance_code,
                            field.get("id"),
                            field.get("name"),
                            field.get("type"),
                            self._json_dumps(field.get("value")),
                            self._json_dumps(field),
                        ),
                    )
            conn.commit()
        finally:
            conn.close()
