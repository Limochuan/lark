from fastapi import APIRouter, Request  # FastAPI 路由与请求对象
from fastapi.responses import JSONResponse  # 用于返回 JSON 响应
import datetime  # 生成当前时间戳
import traceback  # 打印完整异常堆栈，便于排查问题

# 引入审批回调的业务服务层
# Controller 层不直接处理业务逻辑
from app.services.approval_service import ApprovalService

# 创建路由对象，供 main.py 引入注册
router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    """
    飞书审批回调入口

    该函数只做三件事：
    1. 接收并读取飞书回调的原始 JSON
    2. 做最基础的数据存在性校验
    3. 将完整数据交给 Service 层处理
    """
    try:
        # 读取 HTTP 请求体中的 JSON 数据
        data = await request.json()

        # 打印原始回调内容，便于调试和问题追溯
        print("\n==== 收到审批回调（原始） ====")
        print(data)
        print("=================================\n")

        # 从回调数据中获取审批实例 code
        instance_code = data.get("instance_code")

        # 如果没有 instance_code，说明不是有效的审批回调
        if not instance_code:
            raise ValueError("回调数据中缺少 instance_code")

        # 实例化审批业务服务
        service = ApprovalService()

        # 将原始回调数据交由 Service 层统一处理
        service.process_callback(data)

        # 正常处理完成，返回成功响应
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,  # 业务成功标识
                "msg": "received",  # 固定返回信息
                "timestamp": datetime.datetime.now().isoformat()  # 当前时间
            }
        )

    except Exception as e:
        # 捕获所有异常，避免回调接口直接崩溃
        print("\n==== 回调处理异常 ====")
        print(e)

        # 打印完整异常堆栈信息
        traceback.print_exc()

        # 返回错误响应，飞书侧会记录失败
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,  # 业务失败标识
                "msg": "callback error",  # 错误说明
                "error": str(e)  # 异常信息
            }
        )
