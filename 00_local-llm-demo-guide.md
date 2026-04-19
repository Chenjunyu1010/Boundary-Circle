# 本地 LLM 联调与前端完整链路说明

这份文档用于在本地跑通当前项目的完整演示链路，覆盖：

- `.env` 中的 LLM API 配置
- `stress` 种子数据的重置与导入
- 后端与前端的启动方式
- 可直接登录的测试账号与统一密码

## 1. 适用范围

当前项目技术栈：

- 后端：FastAPI
- 前端：Streamlit
- 数据库：本地 SQLite
- LLM 接入方式：OpenAI-compatible `/chat/completions`

LLM 目前主要用于自由文本关键词提取：

- 保存个人 freedom tag 时提取关键词
- 保存团队 freedom requirement 时提取关键词
- Matching 阶段不再实时调用 LLM，只使用数据库中已保存的关键词

## 2. 首次准备

在仓库根目录执行：

```bash
python -m pip install -r requirements.txt
```

仓库根目录是：

```text
D:\Code\MyRepositories\SoftwareEngineering\course-project-ex2-team-12
```

## 3. `.env` 配置

先复制模板：

```powershell
Copy-Item .env.example .env
```

### 3.1 最小可运行配置

如果你只是想启动项目，不要求真实 LLM 提取，可以把 `.env` 写成：

```env
APP_ENV=development
SECRET_KEY=replace-with-a-local-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_HASH_ITERATIONS=100000

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=
```

这种情况下：

- 项目可以正常运行
- 注册、登录、圈子、标签、组队、匹配都可用
- freedom text 仍然可以保存
- 关键词提取会退化为空结果

### 3.2 启用真实 LLM 提取

如果你要测试真实 LLM 提取，把 `.env` 配成类似这样：

```env
APP_ENV=development
SECRET_KEY=your-local-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_HASH_ITERATIONS=100000

LLM_PROVIDER=openai_compatible
LLM_API_KEY=your-api-key
LLM_MODEL=qwen3-coder-next
LLM_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
```

说明：

- `LLM_PROVIDER` 使用 `openai_compatible`
- `LLM_API_KEY` 是你的平台 key
- `LLM_MODEL` 是要调用的模型名
- `LLM_BASE_URL` 是兼容 OpenAI Chat Completions 的基础地址

## 4. 推荐本地启动流程

### 4.1 重置 `stress` 数据集

```bash
python -m scripts.seed_data stress --reset
```

### 4.2 导入 `stress` 数据集

```bash
python -m scripts.seed_data stress
```

### 4.3 启动后端

```bash
uvicorn src.main:app --reload
```

启动后可访问：

- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### 4.4 启动前端

另开一个终端，在仓库根目录执行：

```bash
streamlit run frontend/Home.py
```

前端默认访问后端地址：

```text
http://127.0.0.1:8000
```

如果需要显式指定：

```powershell
$env:API_BASE_URL="http://127.0.0.1:8000"
streamlit run frontend/Home.py
```

正常联调建议：

- `MOCK_MODE=false`
- 使用真实后端

## 5. 关于 `stress` 数据集

当前推荐使用：

```bash
python -m scripts.seed_data stress
```

`stress` 现在用于完整前端链路验证，特点包括：

- 用户规模扩大到 40-60 样本
- 包含学习、项目、运动、娱乐等多种圈子类型
- 有 `float` 类型标签，例如 `GPA`
- 包含范围型数值匹配规则，而不是只有精确数值匹配
- 包含更复杂的成员交叉关系、团队规则与邀请状态

## 6. 测试账号与密码

所有种子账号统一密码都是：

```text
SeedData123!
```

`stress` 的用户名规则是：

```text
seed_stress_<slug>
```

邮箱规则是：

```text
seed_stress_<slug>@example.test
```

例如：

- `seed_stress_amir@example.test`
- `seed_stress_bella@example.test`
- `seed_stress_diana@example.test`
- `seed_stress_ethan@example.test`
- `seed_stress_hazel@example.test`
- `seed_stress_olivia@example.test`
- `seed_stress_ryan@example.test`
- `seed_stress_violet@example.test`

## 7. 推荐验证内容

建议优先检查这些链路：

- 登录后浏览不同 category 的圈子
- 创建团队并验证范围型数值规则
- 用户匹配与团队匹配的排序和说明文案
- 邀请、加入申请、成员标签展示
- freedom text 保存后的关键词提取与匹配表现
