import os
import json
import requests
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.utils.approval_parser import parse_approval_form

router = APIRouter()

# =========================
# 飞书应用配置（从环境变量读取）
# =========================
LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")

LARK_TOKEN_URL = "https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal"
LARK_APPROVAL_INSTANCE_URL = "https://open.larksuite.com/open-apis/approval/v4/instances"


# =========================
# 获取 app_access_token
# =========================
def get_app_access_token() -> str:
    """
    使用 app_id 和 app_secret 换取 app_access_token
    该 token 用于后续调用审批实例接口
    """

    payload = {
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }

    resp = requests.post(LARK_TOKEN_URL, json=payload, timeout=10)

    print("==== 获取 app_access_token 返回 ====")
    print(f"STATUS: {resp.status_code}")
    print(f"RAW RESPONSE: {resp.text}")

    resp.raise_for_status()
    data = resp.json()

    return data["app_access_token"]


# =========================
# 获取审批实例详情
# =========================
def get_approval_instance(instance_code: str, token: str) -> dict:
    """
    根据 instance_code 获取审批实例完整数据
    """

    url = f"{LARK_APPROVAL_INSTANCE_URL}/{instance_code}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    resp = requests.get(url, headers=headers, timeout=10)

    print("==== 飞书审批实例接口返回 ====")
    print(f"请求 URL: {url}")
    print(f"HTTP 状态码: {resp.status_code}")
    print(f"响应 Header: {resp.headers}")
    print(f"原始响应内容: {resp.text}")

    resp.raise_for_status()
    return resp.json()["data"]


# =========================
# 审批回调入口
# =========================
@router.post("/approval/callback")
async def approval_callback(request: Request):
    """
    飞书审批回调统一入口
    """

    try:
        body = await request.json()

        print("==== 收到审批回调（原始数据） ====")
        print(json.dumps(body, indent=2, ensure_ascii=False))

        # 回调基础字段
        event_type = body.get("type")
        status = body.get("status")
        instance_code = body.get("instance_code")
        approval_code = body.get("approval_code")
        uuid = body.get("uuid")

        print("=================================")
        print(f"event_type: {event_type}")
        print(f"status: {status}")
        print(f"approval_code: {approval_code}")
        print(f"instance_code: {instance_code}")
        print(f"uuid: {uuid}")
        print("=================================")

        # 只处理审批实例 & 已通过
        if event_type != "approval_instance" or status != "APPROVED":
            return JSONResponse({"msg": "忽略非审批通过事件"})

        # 获取 token
        token = get_app_access_token()

        # 拉取完整审批实例
        approval_instance = get_approval_instance(instance_code, token)

        print("\n==== 审批实例完整数据（飞书 API 返回） ====")
        print(json.dumps(approval_instance, indent=2, ensure_ascii=False))
        print("==========================================\n")

        # =========================
        # 解析表单（关键步骤）
        # =========================
        parsed_form = parse_approval_form(approval_instance.get("form"))

        print("==== 审批表单字段（解析后） ====")
        print(json.dumps(parsed_form, indent=2, ensure_ascii=False))
        print("================================")

        # 这里以后可以：
        # - 写数据库
        # - 调 ERP
        # - 推送 Teams / 邮件
        # - 发 MQ / Webhook

        return JSONResponse({
            "msg": "审批回调处理成功",
            "data": parsed_form
        })

    except Exception as e:
        print("==== 审批回调处理异常 ====")
        print(str(e))
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
