# NMB
新闻杂志管理系统后端

## 开发启动

- 安装依赖（建议使用 `uv`）：
```bash
uv sync --all-extras --dev
```

- 运行应用：
```bash
uv run uvicorn app.main:app --reload
```

- 运行测试：
```bash
uv run pytest -q
```

## 环境变量

参考 `app/core/config.py` 中的 `Settings`，可在 `.env` 文件设置：
- `DATABASE_URL`（默认：`mysql+pymysql://user:pass@localhost:3306/magazine_db`）
- `REDIS_URL`
- `ELASTICSEARCH_URL`
- `JWT_SECRET_KEY`

## API 前缀

- 所有接口挂载于：`/api/v1`

## 目录结构

```
app/
  api/
    v1/
      auth.py
      health.py
      magazines.py
      members.py
      payments.py
      routes.py
      search.py
      subscriptions.py
  core/
    config.py
    db.py
  models/
    base.py
    download.py
    magazine.py
    magazine_category.py
    member_tier.py
    payment.py
    user.py
    user_membership.py
  schemas/
    common.py
    user.py
  services/
  utils/
    security.py
alembic/
  env.py
  versions/
```
