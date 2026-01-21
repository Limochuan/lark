from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback
import json

from app.services.approval_service import get_approval_instance

router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    """
    飞书审批回调入口
    - 接收飞书推送的审批事件
    - 使用 instance_code 拉取完整审批实例
    - 解析审批表单 form 字段
    """
    try:
        # 读取回调原始数据
        data = await request.json()

        print("\n==== 收到审批回调（原始数据） ====")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("=================================\n")

        approval_code = data.get("approval_code")
        instance_code = data.get("instance_code")
        status = data.get("status")
        event_type = data.get("type")
        uuid = data.get("uuid")

        print("approval_code:", approval_code)
        print("instance_code:", instance_code)
        print("status:", status)
        print("event_type:", event_type)
        print("uuid:", uuid)

        if not instance_code:
            raise ValueError("回调数据中缺少 instance_code")

        # 拉取完整审批实例
        approval_instance = get_approval_instance(instance_code)

        print("\n==== 审批实例完整数据（飞书 API 返回） ====")
        print(json.dumps(approval_instance, ensure_ascii=False, indent=2))
        print("==========================================\n")

        # ========= 关键修复点 =========
        # 飞书返回的 form 是 JSON 字符串，需要反序列化
        raw_form = approval_instance.get("form")

        if not raw_form:
            print("审批实例中未包含 form 字段")
            form_list = []
        elif isinstance(raw_form, str):
            try:
                form_list = json.loads(raw_form)
            except json.JSONDecodeError:
                raise ValueError("form 字段不是合法的 JSON 字符串")
        elif isinstance(raw_form, list):
            form_list = raw_form
        else:
            raise ValueError(f"未知的 form 类型: {type(raw_form)}")

        print("\n==== 审批表单字段（解析后） ====")
        for item in form_list:
            field_name = item.get("name")
            field_type = item.get("type")
            field_value = item.get("value")

            print(f"字段名: {field_name}")
            print(f"字段类型: {field_type}")
            print(f"字段值: {field_value}")
            print("------")
        print("================================\n")

        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("\n==== 审批回调处理异常 ====")
        print(str(e))
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "msg": "callback error",
                "error": str(e)
            }
        )
