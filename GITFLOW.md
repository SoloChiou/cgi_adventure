# Git 標準流程

本文件是專案 Git、分支與部署規則的唯一來源。

## 執行與授權原則

```text
部署授權
│
├─ 使用者明確要求部署至 Development 或 Production
│  └─ 依照本文件執行對應流程，不必逐項重複詢問
│
├─ 使用者未要求部署
│  └─ 不得自行 Commit、Push、Merge 或觸發部署
│
└─ 執行環境要求權限核准
   └─ 仍須遵守工具權限與安全限制
```

## 分支與部署環境

```text
Development
├─ develop Branch
├─ Development Frontend
├─ Development Backend
├─ Development Database
└─ Developing LIFF ID

Production
├─ main Branch
├─ Production Frontend
├─ Production Backend
├─ Production Database
└─ Published LIFF ID
```

`main` 必須隨時維持可部署。尚未完成、無法啟動或未通過必要驗證的程式，不得合併至 `main`。

合併至 `main` 前必須確認：

- 功能已完成。
- Backend 相關 Tests 通過。
- Frontend Production Build 通過。
- Migration 已檢查。
- Diff 沒有非預期修改。
- Development Render 與受影響的核心流程已驗證。
- 涉及 LINE MINI App 時，已完成 LINE Developing 手機實機測試。

## 工作分支原則

```text
工作類型
│
├─ 中高風險功能｜從最新 develop 建立
│  └─ feature/<功能名稱>
│
├─ 錯誤修正｜從目前目標分支建立
│  └─ fix/<問題名稱>
│
└─ 只更新 Production 的低風險文件｜從最新 main 建立
   └─ docs/<文件名稱>
```

跨多個檔案、Migration、Authentication、API Contract 或其他中高風險修改，必須使用短期工作分支。小型文字修正或低風險文件修改不需要建立不必要的長期分支。

## 標準功能部署流程

```text
Git Flow
│
├─ 1. Feature Branch｜開發與提交
│  │
│  ├─ git status
│  │  └─ 查看目前分支，以及修改是否已加入暫存區
│  │
│  ├─ git diff
│  │  └─ 查看尚未 git add 的修改，只讀取、不會修改檔案
│  │
│  ├─ git add <檔案路徑>
│  │  └─ 將指定修改加入暫存區，準備 Commit
│  │
│  ├─ git diff --cached --check
│  │  └─ 檢查準備提交的內容；沒有輸出通常代表通過
│  │
│  ├─ git commit -m "簡短且明確的修改說明"
│  │  └─ 將暫存區內容建立成本機 Commit
│  │
│  └─ git push -u origin <工作分支名稱>
│     ├─ 將工作分支推送至 GitHub
│     ├─ origin：遠端 Repository 的名稱
│     └─ -u：設定本機分支追蹤同名遠端分支
│
├─ 2. Develop｜合併與 Development 部署
│  │
│  ├─ git fetch origin
│  │  ├─ 下載遠端最新分支與 Commit 資訊
│  │  ├─ 更新 origin/main、origin/develop 等本機紀錄
│  │  └─ 不會合併，也不會修改工作中的檔案
│  │
│  ├─ git switch develop
│  │  └─ 切換至本機 develop 分支
│  │
│  ├─ git pull --ff-only origin develop
│  │  ├─ 取得遠端 develop 的最新內容
│  │  └─ 只允許 Fast-forward 更新本機 develop
│  │
│  ├─ git merge --ff-only <工作分支名稱>
│  │  ├─ 將工作分支快轉合併至 develop
│  │  └─ 不額外建立 Merge Commit
│  │
│  └─ git push origin develop
│     └─ 推送 develop，觸發 Development Render 部署
│
├─ 3. Development｜驗證
│  │
│  ├─ 確認 Frontend 與 Backend 正常
│  ├─ 確認受影響的核心流程正常
│  └─ 若涉及 LINE MINI App，使用 LINE Developing 實機測試
│
├─ 4. Main｜正式合併與 Production 部署
│  │
│  ├─ git fetch origin
│  │  └─ 先取得遠端最新狀態，不進行合併
│  │
│  ├─ git switch main
│  │  └─ 切換至本機 main 分支
│  │
│  ├─ git pull --ff-only origin main
│  │  └─ 只允許 Fast-forward 更新本機 main
│  │
│  ├─ git merge --ff-only develop
│  │  └─ 將已完成 Development 驗證的 develop 快轉合併至 main
│  │
│  └─ git push origin main
│     ├─ 推送 main，觸發 Production Render 部署
│     └─ 不得使用 git push --force 改寫 main 歷史
│
└─ 5. 完成確認
   │
   ├─ git status
   │  └─ 確認目前分支與遠端同步，且工作區乾淨
   │
   └─ git log --oneline --decorate -5
      └─ 查看最近 5 筆 Commit 與分支位置
```

## `--ff` 與 `--ff-only`

```text
Fast-forward 選項
│
├─ --ff｜--fast-forward 的縮寫
│  ├─ 可以快轉時直接快轉
│  └─ 不能快轉時，仍可能建立 Merge Commit
│
└─ --ff-only｜一個完整選項，不是 --ff 加上 -only
   ├─ 只允許快轉
   └─ 分支已分岔時停止並報錯，不會自動合併
```

本專案使用 `--ff-only`，避免 Git 在未確認分支差異時自動建立 Merge Commit。

如果 `--ff-only` 失敗：

```text
停止合併
│
├─ git log --oneline --left-right develop...feature/<功能名稱>
│  └─ 查看兩個分支各自擁有的 Commit
│
├─ git diff develop...feature/<功能名稱>
│  └─ 查看兩個分支的內容差異
│
└─ 不要使用 --force
   └─ 先確認分岔原因，再決定如何處理
```

> `git pull` 本身會先執行 Fetch。流程仍保留 `git fetch origin`，方便先取得並查看遠端最新狀態。

## 純文件更新流程

適用於 `GITFLOW.md`、`README.md` 等不影響程式執行的低風險文件修改。如果目前分支還有未進 Production 的功能，不要直接合併整個 `develop`，應只將文件帶到獨立的 `docs/*` 分支。

```text
純文件更新
│
├─ 1. 暫存目前尚未提交的文件
│  │
│  ├─ git status
│  │  └─ 確認要帶走的修改只有文件
│  │
│  └─ git stash push -u -m "Add Git flow documentation"
│     ├─ 暫時收起尚未提交的修改，讓工作區恢復乾淨
│     ├─ -u：連同尚未被 Git 追蹤的新文件一起收起
│     └─ -m：替這筆 Stash 加上容易辨識的說明
│
├─ 2. 從最新 Main 建立文件分支
│  │
│  ├─ git fetch origin
│  │  └─ 取得 GitHub 最新分支與 Commit 資訊，不進行合併
│  │
│  ├─ git switch main
│  │  └─ 切換至本機 main
│  │
│  ├─ git pull --ff-only origin main
│  │  └─ 將本機 main 安全更新至 GitHub main 的最新位置
│  │
│  └─ git switch -c docs/<文件名稱>
│     └─ 從最新 main 建立單一目的的文件分支
│
├─ 3. 取回並檢查文件
│  │
│  ├─ git stash pop
│  │  ├─ 將最近一筆 Stash 套用到目前的文件分支
│  │  └─ 套用成功後刪除該筆 Stash
│  │
│  ├─ git status
│  │  └─ 確認沒有混入其他程式修改
│  │
│  └─ git diff -- <文件路徑>
│     └─ 查看該文件的實際修改內容
│
├─ 4. 提交並推送文件分支
│  │
│  ├─ git add <文件路徑>
│  ├─ git diff --cached --check
│  ├─ git commit -m "Add Git workflow documentation"
│  └─ git push -u origin docs/<文件名稱>
│
├─ 5. 合併至 Main
│  │
│  ├─ git switch main
│  ├─ git pull --ff-only origin main
│  ├─ git merge --ff-only docs/<文件名稱>
│  └─ git push origin main
│     └─ 只將文件 Commit 推送至 GitHub main
│
└─ 6. 完成確認
   │
   ├─ git status
   │  └─ 確認 main 已與 origin/main 同步且工作區乾淨
   │
   └─ git log --oneline --decorate -5
      └─ 確認文件 Commit 已包含在 main
```

如果 `git stash pop` 發生 Conflict，Git 會保留原本的 Stash。先處理衝突並確認文件內容，不要重複執行 `git stash pop`。

## 工作分支清理

```text
功能已合併、部署並驗證完成
│
├─ git branch --merged <目標分支>
│  └─ 確認工作分支的 Commit 已包含在目標分支
│
├─ git branch -d <工作分支名稱>
│  └─ 刪除 Local 工作分支
│
└─ git push origin --delete <工作分支名稱>
   └─ 刪除 Remote 工作分支
```

刪除前必須確認工作分支的 Commit 已包含在目標分支，避免遺失尚未合併的工作。已合併的分支不得繼續承接新修改；部署後發現的新問題應建立新的 `fix/*` 分支。
