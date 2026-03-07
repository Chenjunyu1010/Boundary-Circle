from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    """测试根路径是否返回 200 和正确信息"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to Boundary Circle API",
        "status": "active",
        "docs_url": "/docs"
    }

def test_health_check():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}