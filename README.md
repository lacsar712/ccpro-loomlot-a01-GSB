# LoomLot-01 · 染坊缸染与色牢度抽检

靛蓝染坊台：按 **染坊 → 染缸 → 染程 → 固色静置 → 色牢度** 工序推进，聚焦缸染调度、固色静置窗与抽检，不是库存出入库系统。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Backend | FastAPI + SQLAlchemy 2 + Pydantic v2 + Postgres + JWT |
| Frontend | Svelte 4 + Vite + svelte-spa-router |
| 部署 | docker-compose（db + backend + frontend/nginx） |

## 端口

| 服务 | 端口 |
| --- | --- |
| 前端 | **3600** |
| 后端 API | **8600** |
| PostgreSQL | **5439** |

数据库账号：`loomlot` / `loomlot` / 库名 `loomlot`。

## 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 染坊主管 |
| `dyer` | `123456` | 染程操作员 |

容器启动时 entrypoint 自动建表并 seed。种子含一条**进行中固色静置**（挂在染色中染程上）与布重记录，开箱即可演示「未满窗禁检 → 登记布重 → 结束静置 → 恢复抽检」全链路。

## 快速启动

```bash
cd D:\work\document\bytecode\claudeCodePro\LoomLot\LoomLot-01
docker compose up -d --build
```

浏览器：http://localhost:3600  
API：http://localhost:8600/api/health

停止：

```bash
docker compose down
```

## 业务实体

1. **DyeHouse** — `name`, `waterNote`, `notes`
2. **Vat** — `dyeHouseId`, `vatCode`, `fiberType`, `capacityL`, `status` ∈ `ready|dyeing|drain`
3. **DyeLot** — `vatId`, `recipeName`, `fabricKg`, `startedAt`, `operatorName`；列表输出附 `resting`（是否静置中）
4. **FixationDwell（固色静置）** — `dyeLotId`, `startedAt`, `plannedEndAt`, `actualEndAt`(可空), `dutyOfficer`；`active=true` 当且仅当 `actualEndAt` 为空
5. **FabricWeight（布重千克记录）** — `dyeLotId`, `weighedAt`, `weightKg`(>0), `recorderName`
6. **FastnessCheck** — `dyeLotId`, `checkedAt`, `washFastness`(1–5), `rubFastness`(>0), `tempC`, `notes`

### 规则

- 仅当染缸状态为 `ready` 或 `dyeing` 时可新建染程，否则 409
- 新建染程后，染缸状态自动设为 `dyeing`
- 可选接口：`POST /api/vats/{id}/drain` 将染缸置为 `drain`

#### 固色静置

- 计划结束时刻必须晚于开始时刻，否则 400
- 同一染程同时只允许一条未结束（进行中）静置，重复挂起 409（中文明细）
- **排液缸（`drain`）上的染程禁止新开静置**，冲突 409
- 未写实际结束时刻即视为「进行中 / 未满窗」
- **存在进行中静置的染程禁止新建色牢度抽检**，冲突 409（中文明细）；静置结束后自动恢复。拦截与「进行中」判定共用同一查询（`FixationDwell.active_query`）
- 结束静置：写入实际结束时刻，且不得早于开始时刻（否则 400）
- 结束动作在**同一事务**内要求该染程至少已有一条布重千克记录可对账，否则 400，静置不结束
- 染程列表每行带 `resting` 标记，标识当前是否静置中（与拦截共用同一进行中查询口径）

## 主要 API

- `POST /api/auth/login`（OAuth2 表单）
- `GET /api/auth/me`
- `GET/POST/PUT/DELETE /api/dye-houses`
- `GET/POST/PUT/DELETE /api/vats` · `POST /api/vats/{id}/drain`
- `GET/POST/PUT/DELETE /api/dye-lots`（输出含 `resting`）
- `GET/POST /api/fixation-dwells` · `GET /api/fixation-dwells/{id}` · `POST /api/fixation-dwells/{id}/end`
  - 查询参数：`dyeLotId`、`activeOnly`
- `GET/POST/PUT/DELETE /api/fabric-weights`
- `GET/POST/PUT/DELETE /api/fastness-checks`（新建时若染程静置中 → 409）
- `GET /api/dashboard/stats`

除登录外需 `Authorization: Bearer <token>`。字段对外为 camelCase。

## 目录

```
LoomLot-01/
├── docker-compose.yml
├── backend/          # FastAPI
├── frontend/         # Svelte 4 + Vite + nginx
└── README.md
```

## 本地开发

### 数据库

```bash
docker compose up -d db
```

### 后端

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg2://loomlot:loomlot@127.0.0.1:5439/loomlot"
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
uvicorn app.main:app --reload --port 8600
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

开发态 Vite 将 `/api` 代理到 `http://127.0.0.1:8600`。
