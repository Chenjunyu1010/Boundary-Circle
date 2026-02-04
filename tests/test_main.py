from fastapi.testclient import TestClient
# 从 src 文件夹里的 main.py 导入 app
from src.main import app

client = TestClient(app)

def test_read_root():
    """测试根路径是否返回 200 和正确信息"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to SE Project API", "status": "active"}

def test_health_check():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_predict_demo():
    """测试 AI 接口的输入输出"""
    response = client.get("/predict?input_text=hello")
    assert response.status_code == 200
    # 验证返回的数据里是否包含我们输入的内容
    assert "hello" in response.json()["input"]