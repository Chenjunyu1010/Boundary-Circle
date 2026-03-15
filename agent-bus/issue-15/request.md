# Issue #15 - 创建用户认证界面（登录/注册）

## 📋 任务描述

创建 Streamlit 用户认证界面，包括登录、注册、登出功能，实现 Token 存储和会话管理。

---

## ✅ 验收标准

- [ ] 登录/注册表单完整
- [ ] 表单验证正确（邮箱格式、密码强度）
- [ ] 成功登录后保存 token 到 session_state
- [ ] 错误提示清晰
- [ ] 登出功能正常
- [ ] 未登录用户无法访问受保护页面

---

## 🛠️ 需要实现的内容

### 1. 新增文件
```
frontend/
├── pages/
│   └── 1_🔐_登录注册.py
└── utils/
    ├── __init__.py
    ├── api.py          # API 调用封装
    └── auth.py         # 认证工具
```

### 2. 页面功能

**登录 Tab**：
- 邮箱输入框
- 密码输入框（隐藏）
- 登录按钮
- 错误提示
- 成功跳转

**注册 Tab**：
- 用户名输入框
- 邮箱输入框
- 密码输入框
- 确认密码输入框
- 注册按钮
- 表单验证

### 3. API 调用
```python
# 登录
POST /auth/login
请求：{"username": email, "password": password}
响应：{"access_token": "...", "token_type": "bearer"}

# 注册
POST /auth/register
请求：{"username": "...", "email": "...", "password": "..."}
响应：UserRead
```

### 4. 状态管理
```python
st.session_state.access_token = "..."
st.session_state.user_id = 123
st.session_state.username = "..."
st.session_state.logged_in = True
```

---

## 🧪 测试要求

- [ ] 所有页面可以正常导航
- [ ] 表单验证正常工作
- [ ] API 调用成功处理响应和错误
- [ ] 未登录用户无法访问受保护页面

---

## 📚 参考资料

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Session State](https://docs.streamlit.io/develop/concepts/management/session-state)
- [frontend_demo.py - 现有原型](../frontend_demo.py)

---

## 💬 注意事项

- 使用 `st.spinner()` 显示加载状态
- 错误信息清晰友好
- 成功操作后使用 `st.balloons()` 或 `st.toast()` 反馈
- 使用 `st.tabs()` 切换登录/注册
