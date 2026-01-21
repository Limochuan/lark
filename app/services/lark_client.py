import os
import requests


# 飞书获取 app_access_token 的接口（内部应用）
LARK_TOKEN_URL = "https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal"


def get_app_access_token() -> str:
    """
    获取飞书 app_access_token
    """

    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")

    if not app_id or not app_secret:
        raise RuntimeError("未配置 LARK_APP_ID 或 LARK_APP_SECRET")

    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    resp = requests.post(LARK_TOKEN_URL, json=payload, timeout=10)

    print("\n==== 获取 app_access_token 返回 ====")
    print("STATUS:", resp.status_code)
    print("RAW RESPONSE:", repr(resp.text))
    print("=================================\n")

    if resp.status_code != 200:
        raise RuntimeError(f"获取 token 失败，HTTP 状态码={resp.status_code}")

    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败：{data}")

    token = data.get("app_access_token")
    if not token:
        raise RuntimeError("返回数据中未包含 app_access_token")

    return token
