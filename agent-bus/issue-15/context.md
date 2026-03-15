# 项目上下文 - Boundary Circle

## 📦 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLModel + SQLite |
| 前端 | Streamlit |
| 测试 | pytest + httpx + pytest-cov |
| 部署 | Docker |

---

## 📁 现有项目结构

```
course-project-ex2-team-12/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── circles.py      # 圈子管理 API
│   │   ├── tags.py         # 标签管理 API
│   │   └── users.py        # 用户 CRUD API（无认证）
│   ├── db/
│   │   └── database.py     # 数据库连接
│   ├── models/
│   │   ├── core.py         # User, UserCreate, UserRead 模型
│   │   └── tags.py         # 标签相关模型
│   └── main.py             # FastAPI 入口
├── tests/                  # 测试目录
├── frontend_demo.py        # 简单 Streamlit 原型
├── requirements.txt        # Python 依赖
└── README.md               # 项目文档
```

---

## 🔌 现有 API 端点

### Users API (`src/api/users.py`)

```python
POST   /users/          # 创建用户
GET    /users/          # 获取用户列表
GET    /users/{user_id} # 获取用户详情
```

### 用户模型 (`src/models/core.py`)

```python
UserCreate:
  - username: str
  - email: EmailStr
  - password: str

UserRead:
  - id: int
  - username: str
  - email: EmailStr
```

---

## ⚠️ 重要约束

### 后端 Auth API 尚未实现

当前项目**没有**认证 API，需要前端使用 **Mock 模式** 开发：

```python
# 需要的 API（未实现）
POST /auth/login    # 登录
POST /auth/register # 注册
```

### 前端必须支持 Mock/真实切换

```python
# 环境变量配置
MOCK_MODE=true|false           # 默认 true
API_BASE_URL=http://127.0.0.1:8000  # 后端地址
```

---

## 📄 现有代码参考

### frontend_demo.py

```python
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# 健康检查示例
response = requests.get(f"{API_URL}/health")
if response.status_code == 200:
    st.success(f"Backend is online: {response.json()}")

# AI 预测示例
response = requests.get(
    f"{API_URL}/predict",
    params={"input_text": user_input}
)
result = response.json()
```

### requirements.txt

```
setuptools
fastapi
uvicorn
sqlmodel
python-multipart
streamlit
requests
pytest
pytest-cov
httpx
python-dotenv
pydantic-settings
```

---

## 🎯 Issue #15 范围

### 必须实现
1. `frontend/utils/api.py` - API 客户端封装
2. `frontend/utils/auth.py` - 认证工具
3. `frontend/pages/1_🔐_登录注册.py` - 登录/注册页面
4. `frontend/Home.py` - 主页面（导航）

### 不在此 Issue 范围
- 后端 Auth API 实现（其他 Issue）
- 邮箱验证
- 密码找回

---

## 🔧 开发环境

### 运行后端
```bash
cd course-project-ex2-team-12
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 运行前端
```bash
cd course-project-ex2-team-12
streamlit run frontend/Home.py
```

---

## 📝 约定

1. **文件命名**: Streamlit pages 使用 `序号_emoji_名称.py` 格式
2. **Session State**: 统一使用 `st.session_state` 管理状态
3. **错误处理**: 所有 API 调用必须 try-catch
4. **Mock 数据**: 必须模拟真实 API 响应格式
