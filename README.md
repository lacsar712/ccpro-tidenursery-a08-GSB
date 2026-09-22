# TideNursery-01 · 潮汐育苗台账

海水育苗场「塘口水质采样与投喂事件」台账种子项目（非库存 / 电商 / 医院）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11 · FastAPI · SQLAlchemy 2 · Pydantic v2 · python-jose · passlib(bcrypt) · uvicorn |
| 前端 | React 18 · Vite · TypeScript · React Router v6 |
| 数据库 | PostgreSQL 15 |
| 部署 | docker-compose · 前端 Nginx 反代 `/api` |

## 端口与账号

| 服务 | 端口 |
| --- | --- |
| 前端 | **3400** |
| 后端 API | **8400** |
| PostgreSQL | **5434** |

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 场长 |
| `technician` | `123456` | 水质技术员 |

## 一键启动

```bash
cd TideNursery-01
docker compose up --build
```

启动后访问：

- 前端：http://localhost:3400
- 后端健康检查：http://localhost:8400/api/health
- API 文档：http://localhost:8400/docs

后端 entrypoint 流程：等待数据库就绪 → `create_all` 建表 → seed 初始数据 → 启动 uvicorn。

## 功能模块

1. **Auth**：JWT 登录（OAuth2 Password），`/api/auth/login`、`/api/auth/me`
2. **Hatchery 育苗场**：`name`、`seawaterSource`、`notes`
3. **Pond 育苗塘**：`hatcheryId`、`pondCode`、`species`、`volumeM3`、`status(stocked|dry|quarantine)`；同场 `pondCode` 唯一
4. **WaterSample 水质样**：`pondId`、`sampledAt`、`tempC`、`salinityPpt`、`doMgL`、`ph`、`notes`；`doMgL > 0` 且 `ph ∈ [6,9]`，否则返回 **400**
5. **FeedEvent 投喂**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`
6. **Microscopy 生物絮团镜检**：批次挂塘口，镜检条目决定能否继续投喂
   - 批次字段：所属塘口、开检日（按**东八区**计算）、封检时刻（可空）、主检人；**同塘开检日唯一**，重复开检返回 **409**
   - 镜检条目：批次编号、视野序号、絮团密度等级（`sparse 稀` / `medium 中` / `dense 密`）、观察时刻；未封批次内视野序号唯一，重复返回 **409**
   - **封检规则**（`POST /api/microscopy-batches/{id}/close`）：
     - 至少 **3 个视野**，且**不得全是「密」**；不满足时返回 **409**，且**封检时刻保持为空**
     - 封检成功后写入封检时刻，此后**不可再追加视野**（追加返回 **409**）
   - **投喂拦截**：塘口存在未封检批次时禁止新建投喂（`POST /api/feed-events` 返回 **409**），封检后自动恢复；拦截与塘口列表的「未封镜检」标记共用同一查询（`app/services/microscopy.py`）
7. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日投喂总量 kg

### 种子数据

种子中 A-01 塘有一个**东八区今日开检、尚未封检**的镜检批次（2 个视野：稀、中，未达 3 个），因此该塘口在初始状态下禁止新建投喂；B-01 塘有一个昨日已封检批次（3 个视野：稀、中、密）作为对照。

## 前端页面

Login · Dashboard · Hatcheries · Ponds · WaterSamples · FeedEvents · Microscopy（絮团镜检）

侧栏「絮团镜检」可开检批次、追加视野、封检；塘口列表每行显示是否有未封镜检（「未封镜检 · 禁投喂」标记）。

## 本地开发（可选）

```bash
# 数据库（或用 compose 只起 db）
docker compose up -d db

# 后端
cd backend
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://tidenursery:tidenursery@localhost:5434/tidenursery
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
uvicorn app.main:app --reload --port 8400

# 前端
cd frontend
npm install
npm run dev
```

## 目录结构

```
TideNursery-01/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── auth.py
│       ├── seed.py
│       ├── models/
│       ├── schemas/
│       └── routers/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── pages/
        ├── components/
        └── api/
```
