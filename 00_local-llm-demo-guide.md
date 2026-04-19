# 本地 LLM 联调与前端完整链路说明

这份文档用于本地跑通当前项目的完整演示链路，覆盖：

- `.env` 中的 LLM API 配置
- 后端和前端的启动方式
- `stress2` 种子数据的导入与重置
- 可直接登录的测试账号和统一密码
- 适合前端验证的典型场景

## 1. 适用范围

当前项目是：

- 后端：FastAPI
- 前端：Streamlit
- 数据库：本地 SQLite
- LLM 接入方式：OpenAI-compatible `/chat/completions`

LLM 目前只在“保存自由文本时提取关键词”使用：

- 保存个人 freedom tag 时调用 LLM 提取关键词
- 保存团队 freedom requirement 时调用 LLM 提取关键词
- Matching 阶段不再实时调用 LLM，只使用数据库中已经保存的关键词

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

```bash
cp .env.example .env
```

如果你在 Windows PowerShell 下没有 `cp`，可以用：

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

- 项目能正常运行
- 注册、登录、圈子、标签、组队、匹配都能用
- freedom text 仍然可以保存
- 但关键词提取会退化成空结果，或只触发后端很保守的 ASCII 缩写回退

### 3.2 启用真实 LLM 提取

如果你要测试真实大模型提取，把 `.env` 配成这样：

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

- `LLM_PROVIDER` 目前使用 `openai_compatible`
- `LLM_API_KEY` 是你的平台 key
- `LLM_MODEL` 是你要调用的模型名
- `LLM_BASE_URL` 是兼容 OpenAI Chat Completions 的基地址

当前项目里实际验证较多的是：

- `qwen3-coder-next`

原因是：

- 更快
- 比较适合当前这种短文本关键词提取
- 比早期尝试的更重模型更稳定，超时更少

## 4. 启动后端

在仓库根目录执行：

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

启动后可访问：

- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

后端启动时会自动：

- 创建本地 SQLite 数据库
- 位置在 `data/boundary_circle.db`
- 对已知缺失列做轻量兼容升级

## 5. 启动前端

另开一个终端，在仓库根目录执行：

```bash
streamlit run frontend/Home.py
```

前端默认访问后端地址：

```text
http://127.0.0.1:8000
```

如果你的前端需要显式指定后端地址，可以在启动前设置：

```powershell
$env:API_BASE_URL="http://127.0.0.1:8000"
streamlit run frontend/Home.py
```

正常联调时建议：

- `MOCK_MODE=false`
- 使用真实后端

如果你只是想看前端静态 fallback，可以设置：

```powershell
$env:MOCK_MODE="true"
streamlit run frontend/Home.py
```

但这不适合本次 LLM 和匹配链路联调。

## 6. 导入种子数据

### 6.1 推荐数据集

现在推荐用：

```bash
python scripts/seed_data.py stress2
```

这是目前最适合前端完整链路验证的数据集。

`stress2` 的特点：

- 用户数量更多
- 圈子更多
- 团队更多
- 邀请状态更丰富
- freedom text 更丰富
- 中英文技术关键词混合更多
- 更适合观察匹配排序、关键词重合、锁队、邀请流、join request 等场景

### 6.2 重置 `stress2`

如果要只清空 `stress2`，不影响其他本地数据：

```bash
python scripts/seed_data.py stress2 --reset
```

### 6.3 其他数据集

项目里目前有：

- `demo`
- `stress`
- `stress2`

建议：

- `demo`：小样本展示
- `stress`：旧的较大样本
- `stress2`：当前最适合前端完整链路验证的数据集

## 7. 测试账号与密码

所有种子账号的统一密码都是：

```text
SeedData123!
```

`stress2` 的用户名规则是：

```text
seed_stress2_<slug>
```

邮箱规则是：

```text
seed_stress2_<slug>@example.test
```

例如：

- `seed_stress2_amir`
- `seed_stress2_bella`
- `seed_stress2_diana`
- `seed_stress2_hazel`
- `seed_stress2_luna`
- `seed_stress2_nora`
- `seed_stress2_sam`
- `seed_stress2_tina`
- `seed_stress2_wendy`
- `seed_stress2_kira`

如果你懒得记，直接按这个规律猜就行。

## 8. 推荐优先登录的账号

虽然 `stress2` 里账号很多，但你不需要每个都登录。建议先用下面几个：

### 8.1 `seed_stress2_amir`

用途：

- 看 AI / backend / automation / matching
- 适合观察团队匹配与关键词重合

### 8.2 `seed_stress2_diana`

用途：

- 看 research / prompt / evaluation 类型样本
- 适合观察 freedom text 对匹配排序的影响

### 8.3 `seed_stress2_bella`

用途：

- 看 design / Figma / Agent UX 相关样本
- 适合验证“标签不是纯后端”的匹配表现

### 8.4 `seed_stress2_hazel`

用途：

- 看邀请和 join request
- 适合检查收件箱、响应邀请、团队状态变化

### 8.5 `seed_stress2_luna`

用途：

- 看 PM / 协作 / 需求整理类样本
- 适合验证非技术强项用户在匹配中的排序位置

## 9. 推荐完整验证流程

建议按下面顺序走。

### 9.1 基础启动检查

1. 启动后端
2. 启动前端
3. 导入 `stress2`
4. 打开前端首页
5. 使用一个 `seed_stress2_*` 账号登录

如果失败，先检查：

- 后端是否启动在 `8000`
- 前端是否指向 `http://127.0.0.1:8000`
- `.env` 是否在仓库根目录

### 9.2 圈子与成员浏览

登录后进入圈子页，检查：

- 能看到多个圈子
- 能进入圈子详情
- 能看到成员列表
- 不同成员的标签和自由文本是有差异的

重点观察：

- 有些成员信息完整
- 有些成员故意做了稀疏化
- 这是正常设计，用于测试前端对不完整数据的容错

### 9.3 团队创建与 requirement 保存

在某个圈子中创建团队时，填写：

- 团队描述
- required tags
- `freedom_requirement_text`

如果 `.env` 已配置真实 LLM：

- 提交后会调用大模型提取关键词
- 团队详情里应能看到保存的 requirement text
- 也应能看到提取出的 keywords

如果未配置 LLM：

- 团队仍然可以创建
- 只是 freedom keywords 可能为空，或只回退出极少数明显技术缩写

### 9.4 个人 freedom tag 保存

进入圈子详情，编辑自己的 freedom tag text，例如：

```text
我希望做 AI 自动化、Python 后端、FastAPI 接口整合，也能使用 AI 开发工具提升效率。
```

保存后检查：

- 文本是否保存成功
- 重新进入页面是否能读回
- 如果真实 LLM 开启，是否能看到合理关键词

### 9.5 Matching 页面验证

现在的匹配规则是：

```text
final_score = 0.7 * coverage_score + 0.2 * jaccard_score + 0.1 * keyword_overlap_score
```

并且：

- LLM 只在保存时提取
- Matching 时不再调用 LLM
- 匹配时使用数据库里已经保存的 keywords

前端上建议重点看：

- `Final score`
- `Coverage`
- `Similarity`
- `Keyword overlap`

以及：

- 命中的 tags
- 命中的 freedom keywords
- explanation 文案是否合理

## 10. 典型验证场景

### 场景 1：高匹配候选人

观察点：

- `coverage_score` 高
- `jaccard_score` 高
- `keyword_overlap_score` 也高
- `final_score` 排名靠前

适合验证：

- 综合排序是否正常

### 场景 2：标签还行，但 freedom text 更强

观察点：

- 基础 tag 匹配不是最强
- 但 freedom keywords 重合明显
- 最终排序会被小幅拉高

适合验证：

- freedom matching 是 rerank-only，而不是替代标签匹配

### 场景 3：短语中包含同一个技术词

例如：

- 团队侧：`熟练使用AI开发工具`
- 用户侧：`会用AI工具`

当前实现中，这两边会因为都能抽出 `AI` 而匹配到。

适合验证：

- 短语级关键词的嵌入式 ASCII 技术词匹配

### 场景 4：保存时提取，匹配时不调 LLM

验证方式：

1. 保存 freedom text
2. 观察提取后的 keywords 已落库
3. 多次进入 Matching 页面
4. 结果应稳定，不会每次重新请求模型

适合验证：

- 当前 v2 设计的稳定性和速度

### 场景 5：锁队与解锁

观察点：

- 某些团队接近满员或已锁定
- 接受邀请后，团队可能从 `Recruiting` 变成 `Locked`
- 成员退出后，又可能解锁

适合验证：

- 团队状态流转
- 邀请与 leave team 对列表展示的影响

### 场景 6：邀请与 join request

观察点：

- 普通邀请
- 已接受邀请
- 已拒绝邀请
- join request

适合验证：

- 收件箱显示
- 响应后状态是否变化
- 团队成员数是否同步更新

## 11. LLM 联调建议

### 11.1 建议模型

当前更推荐：

```text
qwen3-coder-next
```

原因：

- 响应更快
- 更适合当前短文本关键词提取
- 人工逐样本测试时更稳定

### 11.2 什么时候看起来像“没提取出来”

常见原因：

- `.env` 没配对
- 后端没有重启，仍在用旧配置
- 模型响应超时
- 输入文本太空泛，没有足够具体的关键词
- 模型把短语提成了别的近义表达

### 11.3 现在的设计边界

当前不是：

- 保存时提取结构化 trait/domain/workstyle
- Matching 时实时用 LLM 解释

当前是：

- 只提取 `keywords`
- 解释文本是模板生成，不是实时 LLM 生成
- matching 的关键词比较有 canonicalization，但不是语义向量理解

## 12. 常见问题

### 12.1 改了 `.env` 为什么没生效

因为后端配置在启动时读取。改完 `.env` 后需要重启 `uvicorn`。

### 12.2 前端打不开真实数据

先检查：

- 后端是否真的在跑
- `API_BASE_URL` 是否是 `http://127.0.0.1:8000`
- `MOCK_MODE` 是否误设成了 `true`

### 12.3 为什么有些用户资料看起来不完整

这是故意设计的稀疏样本，用于前端容错和匹配边界测试。

### 12.4 为什么不是每个匹配结果都有 keyword overlap

因为：

- 有些用户或团队 freedom keywords 本来就不重合
- keyword overlap 只是总分的一小部分
- `coverage_score` 仍然是主导因子

### 12.5 为什么团队和用户短语不同也能匹配

如果短语中都嵌入了相同的 ASCII 技术词，例如 `AI`、`SQL`，当前匹配逻辑会把它们视为重合。

## 13. 推荐命令汇总

安装依赖：

```bash
python -m pip install -r requirements.txt
```

复制环境文件：

```bash
cp .env.example .env
```

启动后端：

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

启动前端：

```bash
streamlit run frontend/Home.py
```

导入 `stress2`：

```bash
python scripts/seed_data.py stress2
```

重置 `stress2`：

```bash
python scripts/seed_data.py stress2 --reset
```

跑 seed 相关测试：

```bash
pytest -v tests/test_seed_data.py tests/test_seed_consistency.py tests/test_seed_integration.py
```

## 14. 一句话建议

如果你是为了“演示和联调当前完整系统”，最推荐的本地流程是：

1. 配好 `.env`
2. 启动后端
3. 启动前端
4. 导入 `stress2`
5. 用 `seed_stress2_amir` 或 `seed_stress2_bella` 登录开始测
