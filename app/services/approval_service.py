"""
审批业务编排层（Service）

职责：
1. 接收回调 payload（或至少 instance_code）
2. 调用飞书审批 API 获取完整审批实例
3. 解析表单 form（如果是字符串则反序列化）
4. 调用 repository 写入数据库（raw / instance / tasks / fields）
"""

import json
from typing import Dict, Any, List

from app.services.lark_approval_api import get_approval_instance
from app.repository.approval_repo import ApprovalRepository


class ApprovalService:
    """
    审批业务服务：串联 拉取 → 解析 → 入库
    """

    def __init__(self):
        self.repo = ApprovalRepository()

    def process_callback(self, callback_payload: Dict[str, Any]) -> None:
        """
        用于处理飞书回调 payload（推荐用这个入口）
        """
        instance_code = callback_payload.get("instance_code")
        if not instance_code:
            raise ValueError("回调数据缺少 instance_code")

        # 1) 从飞书拉取完整审批实例数据
        approval_instance = get_approval_instance(instance_code)

        # 2) raw 表兜底：存一份“完整实例数据”（建议存这个，比回调更全）
        self.repo.save_raw_data(instance_code, approval_instance)

        # 3) 写实例主表
        instance_row = self._build_instance_row(approval_instance)
        self.repo.save_instance(instance_row)

        # 4) 写任务节点表
        task_list = approval_instance.get("task_list", []) or []
        self.repo.save_tasks(instance_code, task_list)

        # 5) 写表单字段表
        form_fields = self._normalize_form(approval_instance.get("form"))
        self.repo.save_form_fields(instance_code, form_fields)

    def process_instance_code(self, instance_code: str) -> None:
        """
        如果你不想传完整回调 payload，只传 instance_code 也可以
        """
        self.process_callback({"instance_code": instance_code})

    @staticmethod
    def _build_instance_row(approval_instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        把飞书返回的数据整理成 repo.save_instance 需要的结构
        注意：这里不写 SQL，只做字段整理
        """
        return {
            "instance_code": approval_instance.get("instance_code"),
            "approval_code": approval_instance.get("approval_code"),
            "approval_name": approval_instance.get("approval_name"),
            "status": approval_instance.get("status"),
            "start_time": approval_instance.get("start_time"),
            "end_time": approval_instance.get("end_time"),
            "user_id": approval_instance.get("user_id"),
            # 下面两个字段如果你表里没有，可以先不存或置空
            "create_time": approval_instance.get("start_time"),
            "update_time": approval_instance.get("end_time") or approval_instance.get("start_time"),
        }

    @staticmethod
    def _normalize_form(form_raw) -> List[Dict[str, Any]]:
        """
        飞书的 form 字段经常是 JSON 字符串，这里统一转成 list[dict]
        """
        if not form_raw:
            return []

        if isinstance(form_raw, str):
            try:
                return json.loads(form_raw)
            except json.JSONDecodeError:
                # 如果 form 字段不是合法 JSON 字符串，直接返回空，避免回调整体失败
                return []

        if isinstance(form_raw, list):
            return form_raw

        return []
