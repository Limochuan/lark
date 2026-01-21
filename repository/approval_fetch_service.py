"""
approval_fetch_service.py

职责说明：
1. 专门负责“从飞书主动拉取审批实例完整数据”
2. 不关心 HTTP 路由
3. 不写数据库
4. 返回的就是飞书 v4 原始 data
"""

import requests
from app.services.lark_client import get_app_access_token

LARK_BASE_URL = "https://open.larksuite.com"


def fetch_approval_instance_from_lark(instance_code: str) -> dict:
    """
    从飞书审批 v4 接口获取完整审批实例数据

    使用场景：
    - 回调数据不完整时补拉
    - 历史审批数据补录
    - 人工排错 / 对账
    """

    if not instance_code:
        raise ValueError("instance_code 不能为空")

    token = get_app_access_token()

    url = f"{LARK_BASE_URL}/open-apis/approval/v4/instances/{instance_code}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    resp = requests.get(url, headers=headers, timeout=10)

    # HTTP 层校验
    if resp.status_code != 200:
        raise RuntimeError(
            f"飞书审批实例接口失败，HTTP={resp.status_code}，内容={resp.text}"
        )

    # JSON 校验
    try:
        payload = resp.json()
    except Exception as e:
        raise RuntimeError(
            f"飞书审批实例接口返回非 JSON，错误={e}，内容={resp.text}"
        )

    # 飞书业务 code 校验
    if payload.get("code") != 0:
        raise RuntimeError(
            f"飞书接口业务错误 code={payload.get('code')} msg={payload.get('msg')}"
        )

    return payload.get("data", {})
