"""
审批数据写入数据库的仓储层（Repository）

职责说明：
1. 只负责数据库写入
2. 不关心 FastAPI / HTTP / 飞书校验
3. 不做业务判断、不改数据结构
4. 所有函数都是“给 service 层调用的”

对应数据表：
- lark_approval_raw         原始回调数据
- lark_approval_instance    审批实例主表
- lark_approval_task        审批任务节点
- lark_approval_form_field  表单字段数据
"""

import json
import pymysql
from typing import Dict, List, Any

from app.db.mysql import get_mysql_conn


class ApprovalRepository:
    """
    审批数据仓储类
    所有和 MySQL 打交道的逻辑都在这里
    """

    # =========================
    # 基础工具方法
    # =========================

    @staticmethod
    def _execute(sql: str, params: tuple):
        """
        执行单条 SQL（INSERT / UPDATE）

        :param sql: SQL 语句
        :param params: SQL 参数
        """
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _execute_many(sql: str, params_list: List[tuple]):
        """
        批量执行 SQL（常用于 task / form_field）

        :param sql: SQL 语句
        :param params_list: 参数列表
        """
        if not params_list:
            return

        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.executemany(sql, params_list)
            conn.commit()
        finally:
            conn.close()

    # =========================
    # 1. 原始回调数据
    # =========================

    @staticmethod
    def save_raw_callback(event_type: str, approval_code: str, instance_code: str, payload: Dict[str, Any]):
        """
        保存飞书回调的“完整原始数据”
        用于：
        - 兜底
        - 排错
        - 未来字段变更可回溯

        表：lark_approval_raw
        """
        sql = """
        INSERT INTO lark_approval_raw
        (event_type, approval_code, instance_code, raw_json)
        VALUES (%s, %s, %s, %s)
        """

        ApprovalRepository._execute(
            sql,
            (
                event_type,
                approval_code,
                instance_code,
                json.dumps(payload, ensure_ascii=False)
            )
        )

    # =========================
    # 2. 审批实例主表
    # =========================

    @staticmethod
    def save_approval_instance(instance: Dict[str, Any]):
        """
        保存 / 更新 审批实例主数据

        表：lark_approval_instance
        """
        sql = """
        INSERT INTO lark_approval_instance (
            instance_code,
            approval_code,
            approval_name,
            status,
            applicant_id,
            applicant_name,
            department_id,
            department_name,
            start_time,
            end_time,
            raw_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            end_time = VALUES(end_time),
            raw_json = VALUES(raw_json)
        """

        ApprovalRepository._execute(
            sql,
            (
                instance.get("instance_code"),
                instance.get("approval_code"),
                instance.get("approval_name"),
                instance.get("status"),
                instance.get("applicant_id"),
                instance.get("applicant_name"),
                instance.get("department_id"),
                instance.get("department_name"),
                instance.get("start_time"),
                instance.get("end_time"),
                json.dumps(instance, ensure_ascii=False)
            )
        )

    # =========================
    # 3. 审批任务节点
    # =========================

    @staticmethod
    def save_approval_tasks(instance_code: str, tasks: List[Dict[str, Any]]):
        """
        保存审批流程中的任务节点（审批人 / 抄送等）

        表：lark_approval_task
        """
        sql = """
        INSERT INTO lark_approval_task (
            instance_code,
            task_id,
            task_type,
            user_id,
            user_name,
            status,
            start_time,
            end_time,
            raw_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            end_time = VALUES(end_time),
            raw_json = VALUES(raw_json)
        """

        params_list = []

        for task in tasks:
            params_list.append((
                instance_code,
                task.get("task_id"),
                task.get("task_type"),
                task.get("user_id"),
                task.get("user_name"),
                task.get("status"),
                task.get("start_time"),
                task.get("end_time"),
                json.dumps(task, ensure_ascii=False)
            ))

        ApprovalRepository._execute_many(sql, params_list)

    # =========================
    # 4. 表单字段数据
    # =========================

    @staticmethod
    def save_form_fields(instance_code: str, fields: List[Dict[str, Any]]):
        """
        保存审批表单字段

        表：lark_approval_form_field
        """
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

        params_list = []

        for field in fields:
            params_list.append((
                instance_code,
                field.get("field_id"),
                field.get("field_name"),
                field.get("field_type"),
                json.dumps(field.get("value"), ensure_ascii=False),
                json.dumps(field, ensure_ascii=False)
            ))

        ApprovalRepository._execute_many(sql, params_list)
