# Boundary Circle - 更新日志 (Changelog)

本项目遵循阶段性开发策略，确保软件工程课程项目能够按时、高质量地交付。以下是项目的更新记录。

## [v0.1.0] - 里程碑 1 (核心后端骨架搭建) - 2026-02-27

### 架构调整说明 (Architecture Simplification)
为了降低开发门槛、减少环境配置带来的不可控因素，我们对初始 AI 生成的宏大架构进行了“降维减负”调整：
* **移除 PostgreSQL**，切换至 **SQLite**。实现“开箱即用”，小组成员克隆代码后可直接运行，无需配置 Docker 或安装本地数据库软件。
* **移除复杂的 SQLAlchemy 配置**，引入 **SQLModel**。结合 FastAPI 实现了数据模型与 Pydantic 模型的完美统一，大幅减少了代码量和出错概率。
* 暂时搁置 ChromaDB 和复杂的 AI 对接，先确保基础的 CRUD 业务逻辑畅通（里程碑 3 中再引入轻量级 AI 匹配机制）。

### 新增功能 (Features)
* 增加了 FastAPI 的应用生命周期管理（启动时自动创建 SQLite 数据库和表）。
* **数据库层 (`src/db/database.py`)**: 实现了基础的 SQLite 引擎与 Session 依赖注入。
* **模型层 (`src/models/core.py`)**: 定义了 `User` (用户) 和 `Circle` (圈子) 的基础数据模型（包含 Base, Create, Read 等用于接口校验的衍生模型）。
* **API 接口 - 用户 (`src/api/users.py`)**:
  * `POST /users/`: 注册创建新用户。
  * `GET /users/`: 获取用户列表（支持分页）。
  * `GET /users/{user_id}`: 根据 ID 获取特定用户。
* **API 接口 - 圈子 (`src/api/circles.py`)**:
  * `POST /circles/`: 创建新圈子（校验创建者是否存在）。
  * `GET /circles/`: 获取圈子列表（支持分页）。
  * `GET /circles/{circle_id}`: 获取特定圈子详情。

### 修改项 (Changed)
* 重写了 `src/main.py`，注册了真正的路由 `/users` 和 `/circles`，并接管了应用的启动事件。
* 更新了 `requirements.txt`，添加了 `sqlmodel`, `pydantic-settings`, `pytest`, `httpx` 等实际运行需要的依赖。
* 重写了 `README.md`，更新了技术栈描述，并加入了清晰的“阶段性开发计划 (Milestones)”。
* 修复了 `tests/test_main.py`，使基本的集成测试能够跑通，并加入了在测试前创建测试表的逻辑。

### 遗留问题 / 下一步计划 (Todo / Next Steps)
* **里程碑 2**: 引入 `Tag` 和 `Team` 模型，实现“加入圈子填写标签”以及“发布组队需求”的后端 API。
* **前端集成**: 需要前端同学使用 Streamlit 对接目前已经完成的 `/users` 和 `/circles` 接口。
