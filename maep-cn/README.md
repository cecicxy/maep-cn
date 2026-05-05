# MAEP-CN — 多智能体执行协议（中国版）

基于预付费余额的 AI Agent 随用随扣协作协议。无需加密货币，RMB 实时结算。

## 与原版 MAEP 的区别

| 特性 | MAEP-CN | MAEP 原版 |
|------|---------|-----------|
| 支付方式 | RMB 预付费余额 | ETH 链上托管 |
| 结算速度 | 毫秒（数据库事务） | 秒级（出块确认） |
| 交易成本 | 零 | Gas 费 |
| 身份系统 | 平台注册 + 押金 | 链上 DID + 质押 |
| 结果存证 | SQLite + SHA-256 哈希 | 链上 keccak256 |
| 争议仲裁 | LLM 仲裁 + 平台执行 | 链上审计员 forceRelease |
| LLM 支持 | 智谱、MiniMax、OpenAI 等 | OpenAI、Anthropic |
| 中国可用 | ✅ | ❌ |

## 快速开始

```bash
cd maep-cn
pip install -r requirements.txt
```

### 启动服务器

```bash
python run.py
# 浏览器打开 http://localhost:8000
```

### 配置 LLM

复制 `.env.example` 为 `.env`，填入 API Key：

```bash
# 使用智谱（推荐国内用户）
LLM_PROVIDER=zhipu
LLM_API_KEY=your_zhipu_key
LLM_MODEL=glm-4-flash

# 或使用 MiniMax
LLM_PROVIDER=minimax
LLM_API_KEY=your_minimax_key
LLM_MODEL=abab6.5s-chat
```

### 运行测试

```bash
pytest tests/ -v
```

### 运行演示

```bash
# 端到端 3-agent 场景演示
python experiments/scenario_demo.py

# 延迟基准测试
python experiments/bench_latency.py
```

## 架构

```
AI Agent (Requester) ──┐
                       ├──→ REST API (FastAPI) ──→ SQLite DB
AI Agent (Provider)  ──┤         │
                       │    ┌────┴────┐
AI Agent (Auditor)   ──┘    │  LLM    │
                            │ Client  │
                            └─────────┘
```

### 协议流程

```
注册 → 委托（锁定余额）→ 执行（存证哈希）→ 结算（释放付款）
                                            ↘ 争议 → 仲裁
```

每一步都是数据库事务，保证原子性：

- **委托**：余额检查 → 扣款 → 建任务 → 锁定付款（一条事务）
- **结算**：更新付款状态 → 释放资金给 Provider（一条事务）
- **仲裁**：根据裁决结果退款或付款（一条事务）

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/agents | 注册 Agent |
| GET | /api/agents/{id} | 查询信息及余额 |
| POST | /api/agents/{id}/topup | 充值 |
| POST | /api/tasks | 创建任务（锁定预算） |
| GET | /api/tasks | 列出最近任务 |
| GET | /api/tasks/{id} | 查询任务详情 |
| POST | /api/tasks/{id}/execute | 提交执行结果 |
| POST | /api/tasks/{id}/verify | 验证并结算 |
| POST | /api/tasks/{id}/dispute | 发起争议 |
| POST | /api/tasks/{id}/arbitrate | 审计员仲裁 |
| GET | /api/stats | 平台统计 |

## 目录结构

```
maep-cn/
├── run.py                 # 启动服务器
├── agent_sdk/             # Python SDK
│   ├── protocol.py        # 状态机
│   ├── db.py              # SQLite 存储客户端
│   ├── llm_client.py      # LLM 多供应商客户端
│   ├── requester.py       # 请求方 Agent
│   ├── provider.py        # 执行方 Agent
│   └── auditor.py         # 审计方 Agent
├── api/                   # FastAPI REST API
│   ├── app.py             # 应用工厂
│   ├── routes.py          # 路由
│   └── schemas.py         # 数据模型
├── web/                   # 展示网站
│   ├── index.html
│   ├── style.css
│   └── app.js
├── experiments/           # 实验脚本
└── tests/                 # 测试
```
