import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from src.auth.api.auth import router as auth_router

app = FastAPI(
    title="JWT 认证系统",
    description="用户注册、登录、JWT令牌认证示例",
    version="1.0.0"
)

# 注册路由 - 这里才是正确的位置
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "message": "JWT 认证系统运行中",
        "docs": "/docs",
        "endpoints": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "me": "GET /auth/me (需要认证)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
