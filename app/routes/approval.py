from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback

# ✅ 改这里：不再直接调飞书 API，不再自己解析
from app.services.approval_service import ApprovalService

# FastAPI 路由对象，main.py 就是 import 的这个
router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    """
    飞书审批回调入口

    职责说明：
    1. 接收飞书回调原始 payload
    2. 不做业务解析
    3. 直接交给 ApprovalService 统一处理
    """
    try:
        # 读取回调原始 JSON
        data = await request.json()

        print("\n==== 收到审批回调（原始） ====")
        print(data)
        print("=================================\n")

        # 只做最基本的存在性校验（防止无意义请求）
        instance_code = data.get("instance_code")
        if not instance_code:
            raise ValueError("回调数据中缺少 instance_code")

        # 业务全部交给 Service
        service = ApprovalService()
        service.process_callback(data)

        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("\n==== 回调处理异常 ====")
        print(e)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "msg": "callback error",
                "error": str(e)
            }
        )
