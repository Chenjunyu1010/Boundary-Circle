# Agent Configuration - Boundary Circle

**Project**: Boundary Circle (边界圈) - 智能团队组建社交平台  
**Course**: BSAI301 Software Engineering - 澳门科技大学  
**Team**: EX2-Team-12

---

## 🎯 项目定位

这是一个**软件工程课程项目**，强调：
- 工程质量和开发流程 > 功能数量
- 团队协作和代码审查
- 完整的 CI/CD 和测试覆盖
- 规范化的文档和版本控制

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|----------|
| **Backend** | FastAPI | Python 3.9+ |
| **Frontend** | Streamlit | 原型阶段 |
| **Database** | SQLite | 零配置单文件 (`boundary_circle.db`) |
| **ORM** | SQLModel | v0.0.37 (Pydantic + SQLAlchemy 二合一) |
| **AI/LLM** | 待定 | DeepSeek / OpenAI / 其他 API (Milestone 3) |
| **Container** | Docker | 容器化部署 (期末演示用) |
| **CI/CD** | GitHub Actions | 自动化测试 |
| **Testing** | pytest | 单元测试 |

---

## 📝 编码规范

### Python 代码风格
- 遵循 **PEP 8** 规范
- 函数和变量使用 `snake_case`
- 类名使用 `PascalCase`
- 所有公开函数必须有 docstring

### FastAPI 约定
- 所有路由必须包含在 `src/` 目录下的独立模块中
- 使用 Pydantic 模型进行请求/响应验证
- 所有 API 端点必须有 OpenAPI 描述
- 错误处理使用 FastAPI 的 `HTTPException`

### 类型注解
- **强制** 所有函数参数和返回值必须有类型注解
- 使用 `typing` 模块处理复杂类型
- 禁止使用 `Any` 类型（除非绝对必要）

### 测试规范
- 测试文件位于 `tests/` 目录
- 测试函数命名：`test_<功能>_<场景>_<预期结果>()`
- 使用 pytest fixtures 进行测试数据 setup
- CI 必须通过所有测试

---

## 🚫 约束与禁止事项

### 类型安全（BLOCKING）
- ❌ 禁止使用 `as Any` 强制类型转换
- ❌ 禁止使用 `@ts-ignore` / `@typescript-ignore`
- ❌ 禁止使用 `# type: ignore`  suppressing 类型错误

### 代码质量
- ❌ 禁止空 catch 块 `catch(e) {}` / `except: pass`
- ❌ 禁止删除失败的测试来"通过"CI
- ❌ 禁止提交包含硬编码密码/密钥的代码
- ❌ 禁止直接在代码中写 SQL（必须使用 ORM 或参数化查询）

### Git 规范
- ❌ 禁止 force push 到 main/master 分支
- ✅ 所有功能开发必须在 feature 分支
- ✅ 提交信息遵循 Conventional Commits 规范

---

## 🔄 开发工作流

### 新功能开发
1. 创建 feature 分支：`git checkout -b feature/<功能名>`
2. 实现功能 + 编写测试
3. 运行本地测试：`pytest`
4. 提交代码并创建 PR
5. 等待 CI 通过 + 代码审查
6. Merge 到 main 分支

### 代码审查清单
- [ ] 代码符合 PEP 8 规范
- [ ] 所有函数有类型注解
- [ ] 新增代码有对应测试
- [ ] 无类型错误（mypy/pyright 检查通过）
- [ ] 无敏感信息泄露
- [ ] 提交信息规范

---
## 测试结果申报规范

在完成任何功能代码开发或 Bug 修复后，必须填写测试信息并规范地申报测试结果，确保质量可见和可追踪。

### 1. 测试后须填写的信息项
每次执行完测试后，需整理并记录以下信息：
- **测试执行环境**：如操作系统 (Windows/Ubuntu)、Python 版本。
- **受测功能模块**：本次测试主要覆盖的文件或 API 端点（如 `tests/test_users.py`，核心模块 `src.api.users`）。
- **运行命令与耗时**：实际敲击的完整测试命令（如 `pytest -v`）及执行总耗时。
- **具体测试数据**：
  - **Passed (通过)**：数量
  - **Failed (失败)**：数量及简要失败原因分析（如有）
  - **Warnings/Skipped**：数量及原因

### 2. 测试结果申报流程
1. **生成与提取结果**：本地完整运行 `pytest`，并提取终端输出的尾部结果摘要（如 `=== 15 passed, 2 warnings in 0.52s ===`）。
2. **PR / 提交说明中申报**：在 GitHub Pull Request 的描述中或通过团队交流频道，使用标准模板进行申报：
   ```text
   【测试结果申报】
   - 💻 环境配置：Windows 11, Python 3.9
   - 🎯 测试模块：用户注册与圈子查询
   - 🚀 执行命令：`pytest -v`
   - 📊 摘要数据：`20 passed, 0 failed in 0.85s`
   - 📝 备注说明：所有核心边界条件均已覆盖，无失败用例。
   ```
3. **Agent 自动汇报要求**：如果是 Agent 代理执行的测试，必须先以类似格式向用户显式输出测试报告。在得到用户“确认测试结果无误”的许可后，才允许进行后续的 `git commit` 操作。

---

## 🤖 Agent 行为准则

### 默认行为
- ✅ **先探索后实现** - 修改前先读取相关文件
- ✅ **遵循现有模式** - 保持代码风格一致性
- ✅ **最小化变更** - Bugfix 时只修复问题，不重构
- ✅ **验证优先** - 修改后运行 lsp_diagnostics 和测试
- 🔴 **严格分支工作流与提交前确认 (CRITICAL)** - 绝不直接向 `main` 分支提交代码。开发新功能时必须先创建并切换到 `feature/<名称>` 分支。在执行任何 `git commit` 或 `git push` 操作前，必须先向用户报告修改内容并请求许可。只有在用户明确同意后，才能提交并推送到该分支。
### 委托策略
- **前端 UI 任务** → 委托 `visual-engineering` category
- **复杂架构问题** → 咨询 `oracle` agent
- ** unfamiliar 库** → 启动 `librarian` agent 查文档
- **代码探索** → 启动 `explore` agent（后台并行）

### 完成标准
任务完成前必须验证：
- [ ] 所有 todo 完成
- [ ] 修改文件 diagnostics 干净
- [ ] 测试通过（`pytest`）
- [ ] 无类型错误

---

---

## 🧠 经验教训与避坑指南 (Lessons Learned)

### 1. 架构降维减负 (Architecture Simplification)
作为没有太多工程经验的大学生团队，容易犯的错误是一开始就搭建宏大的工业级架构。以下是已生效的务实调整：
- **数据库**：用 **SQLite**（零配置单文件 `boundary_circle.db`）替代 PostgreSQL。
- **ORM 工具**：用 **SQLModel** 替代 SQLAlchemy。把数据模型和 Pydantic 校验二合一，代码量减半。
- **AI/检索**：搁置 ChromaDB 本地部署，计划使用 **LLM API**（DeepSeek / OpenAI / 其他，待定）。规避复杂的向量数据库搭建和 C++ 编译报错。

### 2. Docker 的正确打开方式
软工课老师喜欢看 Docker 部署，但对日常开发极其不友好。
- **日常开发（不要用 Docker）**：直接终端运行 `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`。
- **期末演示/交付（使用 Docker）**：用于向老师展示容器化能力。构建 `docker build -t boundary-circle:v1 .`，运行 `docker run -d -p 8000:8000 boundary-circle:v1`。

### 3. 常见报错排查 (Troubleshooting)
- **`ModuleNotFoundError: No module named 'src'`**
  - **原因**：典型的路径错误，终端停留在 `C:\Users\chenj`，而非项目根目录。
  - **解决**：在终端中使用 `cd D:\Code\MyRepositories\SoftwareEngineering\course-project-ex2-team-12` 切换到根目录后，再执行启动命令。
- **接口自测 (Swagger UI)**
  - 启动服务器后，直接访问 `http://localhost:8000/docs`。使用 "Try it out" 测试接口收发，无需手写前端。

---

## 🧮 匹配算法说明 (Matching Algorithm)

### 算法选择：加权评分 + Jaccard 相似度

**原因**：简单、可解释、冷启动友好、适合学生团队实现

### 核心公式

```python
# 1. 技能标签匹配 → Jaccard 相似度
Jaccard(A, B) = |A ∩ B| / |A ∪ B|

# 示例：用户 A 技能 {Python, FastAPI}，用户 B 技能 {Python, React}
# Jaccard = 1 / 3 = 0.33

# 2. 兴趣标签匹配 → Jaccard 相似度（同上）

# 3. 可用性匹配 → 取较小值
availability_score = min(user_availability, target_availability)

# 4. 综合评分 → 加权和
final_score = 0.5×skill_score + 0.3×interest_score + 0.2×availability_score
```

### 权重配置

| 因素 | 权重 | 说明 |
|------|------|------|
| **技能匹配** | 0.5 (50%) | 最重要，确保能力互补 |
| **兴趣匹配** | 0.3 (30%) | 共同兴趣促进合作 |
| **可用性匹配** | 0.2 (20%) | 时间协调性 |

### 实现位置

```
src/services/matching.py  # 匹配算法核心逻辑
src/api/matching.py       # FastAPI 路由端点
```

### 未来扩展（可选）

- **LLM 解释生成**：调用 大模型 API 生成匹配原因文本
- **协同过滤**：积累历史组队数据后可增强
- **遗传算法**：批量组队优化（课程项目不推荐）

---
## 📁 项目结构约定

```
course-project-ex2-team-12/
├── src/                    # 后端源代码
│   ├── main.py            # FastAPI 入口
│   ├── models/            # 数据模型 (SQLModel)
│   │   └── core.py        # User, Circle 模型定义
│   ├── api/               # API 路由
│   │   ├── users.py       # 用户端点
│   │   └── circles.py     # 圈子端点
│   └── db/                # 数据库配置
│       └── database.py    # SQLite + SQLModel 配置
│   └── services/          # 业务逻辑层
│       └── matching.py    # 组队匹配算法
├── tests/                  # 测试代码
│   ├── test_*.py          # 测试文件
│   └── conftest.py        # pytest fixtures
├── docs/                   # 项目文档
│   ├── proposal.md        # 项目提案
│   └── course-requirements.md  # 课程要求
├── frontend_demo.py        # Streamlit 原型
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 配置
├── agents.md              # Agent 协作规范 (本文件)
└── chat.md                # 经验教训记录

---

## 🔑 核心 API 端点（规划）

| 模块 | 端点 | 状态 |
|------|------|------|
| **Root** | `GET /` | ✅ 已实现 |
| **Health** | `GET /health` | ✅ 已实现 |
| **Users** | `GET/POST /users/`, `GET /users/{id}` | ✅ 已实现 (Milestone 1) |
| **Circles** | `GET/POST /circles/`, `GET /circles/{id}` | ✅ 已实现 (Milestone 1) |
| **Auth** | `POST /auth/register`, `POST /auth/login` | ⏳ Milestone 2 |
| **Circles Join** | `POST /circles/{id}/join` | ⏳ Milestone 2 |
| **Tags** | `GET/POST /tags`, `PUT /tags/{id}` | ⏳ Milestone 2 |
| **Matching** | `GET /matching/recommendations` | ⏳ Milestone 3 (简单算法：Jaccard + 加权评分) |
| **Teams** | `POST /teams`, `POST /teams/{id}/invite` | ⏳ Milestone 3 |

---

## 📚 文档要求

所有代码变更需同步更新：
- 新增 API 端点 → 更新 `README.md` API 列表
- 修改数据结构 → 更新 `docs/proposal.md`
- Bugfix → 在提交信息中说明原因

---

**Last Updated**: 2026-03-06  
**Maintainer**: EX2-Team-12
