# CGI Adventure

第一版可玩垂直切片，採 Python／Django Server-rendered HTML、CSS 與少量 JavaScript。標準本機環境使用 Docker Compose 與 PostgreSQL；也可直接使用 SQLite 執行輕量開發環境。

```text
標準本機啟動（Docker Compose）
├─ 1. 建立本機環境變數
│  └─ cp .env.example .env
│     ├─ 填入 POSTGRES_PASSWORD、DJANGO_SECRET_KEY 與 DEV_ADMIN_PASSWORD，不得留白
│     └─ `.env` 已被 Git 排除，不得提交、貼入文件或輸出至 Log
│
├─ 2. 建置並啟動 Django 與 PostgreSQL
│  └─ docker compose up --build
│     └─ 啟動時自動執行 Migration 與 seed_game
│
├─ 3. 使用本機開發登入帳號
│  ├─ 帳號：讀取 .env 的 DEV_ADMIN_USERNAME
│  ├─ 密碼：讀取 .env 的 DEV_ADMIN_PASSWORD
│  └─ DEBUG=True 時登入頁會自動預填，但 Repository 不保存有效憑證
│
├─ 4. 開啟遊戲
│  └─ http://127.0.0.1:8000/
│
└─ 5. 停止容器
   └─ docker compose down
      └─ 保留 PostgreSQL Volume，稍後啟動仍可使用本機資料
```

正式環境不得使用本機帳號入口取代 LINE 身分驗證。

```text
Docker 環境驗證
├─ 1. Django 系統檢查
│  └─ docker compose exec web python manage.py check
│
├─ 2. Migration 漂移檢查
│  └─ docker compose exec web python manage.py makemigrations --check --dry-run
│
└─ 3. 自動化測試
   └─ docker compose exec web python manage.py test
```

```text
輕量替代流程（不使用 Docker）
├─ 1. 安裝相依套件
│  └─ python -m pip install -r requirements.txt
│
├─ 2. 建立 SQLite 資料庫
│  └─ python manage.py migrate
│
├─ 3. 載入初始遊戲內容
│  └─ python manage.py seed_game
│
├─ 4. 建立開發登入帳號
│  └─ python manage.py createsuperuser
│
└─ 5. 啟動開發伺服器
   └─ python manage.py runserver
```

```text
不同電腦同步
├─ 程式碼、Migration 與 seed_game
│  └─ 使用 Git 同步
│
├─ 每台電腦的環境設定
│  └─ 由 .env.example 建立各自的 .env
│
└─ PostgreSQL 本機資料
   └─ Docker Volume 不會跨電腦同步；需要時在各電腦重新執行 Migration 與 seed_game
```
