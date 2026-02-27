from fastapi.testclient import TestClient
# 从 src 文件夹里的 main.py 导入 app
from src.main import app
from src.db.database import create_db_and_tables

client = TestClient(app)

# Create tables before tests run
create_db_and_tables()
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

def test_read_users():
    """测试获取用户列表接口"""
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)