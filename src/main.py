from fastapi import FastAPI

# 初始化 APP
app = FastAPI(
    title="SE Project API",
    description="Backend API for our Software Engineering Project",
    version="0.1.0"
)

# 1. 根路径 (Root Endpoint)
# 作用：确认系统是否存活
@app.get("/")
def read_root():
    return {"message": "Welcome to SE Project API", "status": "active"}

# 2. 健康检查 (Health Check)
# 作用：这也是 SE 的加分项，用于监控系统状态
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 3. (预留) AI 功能接口
# 之后你们的 AI 模型就在这里调用
@app.get("/predict")
def predict_demo(input_text: str = ""):
    return {"input": input_text, "result": "AI model placeholder"}