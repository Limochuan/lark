import time
import requests
import os

LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")

_TOKEN_CACHE = {
    "token": None,
    "expire_at": 0
}

def get_app_access_token() -> str:
    now = int(time.time())

    # 命中缓存（提前 5 分钟刷新）
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["expire_at"] - 300:
        return _TOKEN_CACHE["token"]

    url = "https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal"
    resp = requests.post(url, json={
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    })

    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Get token failed: {data}")

    token = data["app_access_token"]
    expire = data["expire"]

    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expire_at"] = now + expire

    return token
