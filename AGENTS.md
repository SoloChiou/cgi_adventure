# AGENTS.md

## 1. 文件定位與閱讀順序

```text
開始處理任務
├─ 1. 閱讀本文件
│  └─ 取得工作方式、工程邊界與品質要求
│
├─ 2. 閱讀 PROJECT_SPEC.md
│  └─ 取得產品方向、功能範圍、資料模型、流程與遊戲規則
│
└─ 3. 閱讀任務相關程式與測試
   └─ 理解現況後再進行最小合理修改
```

`PROJECT_SPEC.md` 是產品行為與遊戲規則的單一真實來源。本文件不重複保存公式、數值、模型清單、端點細節或 MVP 內容量。

若兩份文件衝突：

```text
文件衝突
├─ 產品行為或遊戲規則：以 PROJECT_SPEC.md 為準
├─ 工作方式或工程品質：以 AGENTS.md 為準
└─ 無法依此分類：停止實作並向使用者確認
```

---

## 2. 核心工程原則

```text
工程原則
├─ 伺服器權威
│  ├─ 用戶端只提交操作意圖與允許的識別碼
│  └─ 後端負責驗證及所有遊戲結果
│
├─ 規則與表現分離
│  ├─ Domain／Service 產生結構化結果
│  └─ Template 只負責顯示，不重新計算規則
│
├─ 可重現與可測試
│  ├─ 亂數來源必須可注入或控制
│  └─ 固定 seed 或可預測 RNG 應能重現結果
│
├─ 資料一致性
│  ├─ 資源發放與角色狀態更新必須原子完成
│  └─ 必須防止重複提交、並行結算與部分寫入
│
└─ MVP 優先
   ├─ 先完成最小可玩的垂直切片
   └─ 不為未確認需求提前建立系統
```

數值與交易完整性優先於操作方便性與視覺效果。

---

## 3. 架構責任

```text
Request
└─ View／Form
   └─ Application Service
      └─ Domain Rules
         └─ Model／Repository
```

```text
各層責任
├─ View／Form
│  └─ HTTP、權限、輸入驗證、服務協調與輸出
│
├─ Application Service
│  └─ 使用案例流程、交易邊界與跨領域協調
│
├─ Domain Rules
│  └─ 戰鬥、獎勵、成長與其他純規則計算
│
├─ Model／Repository
│  └─ 持久化、查詢、關聯與資料庫約束
│
└─ Template／JavaScript
   └─ 顯示與漸進增強，不決定遊戲結果
```

不要把核心規則寫進 View、Template、JavaScript 或 Model Signal。新增遊戲內容時優先採資料驅動，不要在核心服務加入特定怪物、技能或物品名稱的硬編碼分支。

### 3.1 內容設計與考據責任

```text
中國鬼怪文學內容流程
├─ 1. 確認內容定位
│  └─ 依 PROJECT_SPEC.md 判斷來源作品、內容範圍與 MVP 優先序
│
├─ 2. 記錄設計關係
│  └─ 在 CONTENT_DESIGN.md 記錄場地、人物、怪物、物品、職業與技能的關係及改編理由
│
├─ 3. 建立可執行內容
│  └─ 由 seed_game 保存可重建的正式內容與數值，再寫入資料庫
│
└─ 4. 驗證來源資料
   ├─ 原典內容記錄來源作品與具體出處
   ├─ 融合、簡化或遊戲化內容標示為改編
   └─ 無特定原典出處的內容標示為原創並說明設計依據
```

不同典籍中的同名角色或相似設定不得未經說明直接視為同一內容。不確定的宗教、歷史、民俗或原典說法不得宣稱為確定事實。內容題材調整不得改變伺服器權威、交易完整性、規則可重現性與測試要求。

`PROJECT_SPEC.md` 保存世界觀方向、內容範圍與遊戲規則；`CONTENT_DESIGN.md` 保存內容關係、考據與改編理由；`seed_game` 保存可執行內容與數值；資料庫只作為執行時資料來源，不得成為無法由版本控制內容重建的唯一來源。

---

## 4. Backend 與資料庫要求

```text
Backend 要求
├─ 交易
│  ├─ 會改變角色或發放資源的流程使用明確交易邊界
│  ├─ 需要時鎖定正確且範圍最小的資料列
│  └─ 任何步驟失敗時不得留下部分結果
│
├─ 約束
│  ├─ Service 層驗證使用案例規則
│  └─ Database Constraint 保護可由資料庫表達的不變條件
│
├─ 查詢
│  ├─ 使用適當的關聯預載避免 N+1
│  └─ 不為尚未出現的效能問題提前加入 Cache Layer
│
└─ 可攜性
   ├─ 保持本機與部署資料庫的合理可遷移性
   └─ 資料庫行為不同時，清楚記錄實際保證並加入對應測試
```

所有用戶端輸入皆不可信。不得接受或直接套用由前端提交的角色狀態、能力值、亂數、傷害、獎勵、物品數量、時間或勝負。

---

## 5. Frontend 要求

```text
Frontend 原則
├─ 遵循 PROJECT_SPEC.md 指定的介面與互動方向
├─ 一般 Web 頁面優先支援漸進增強與 Server-rendered fallback
├─ LINE 身分與平台功能可以依賴 LIFF SDK
├─ JavaScript 不得保存或決定權威遊戲狀態
├─ 優先確保手機尺寸、文字可讀性與錯誤提示
└─ 視覺裝飾、動畫與大型 UI 抽象最後處理
```

未經使用者明確要求，不更換前端架構、不加入 UI Framework，也不將 Server-rendered 頁面改造成 SPA。

### 5.1 LINE MINI App 整合

LINE MINI App、LIFF 與 LINE Login 的產品需求以 `PROJECT_SPEC.md` 為準。開始整合、升級 SDK 或準備發布前，必須重新查閱 LINE Developers 官方文件，不依賴記憶中的平台規格。

```text
LINE 整合邊界
├─ Frontend LIFF Adapter
│  ├─ 集中處理 liff.init、登入狀態、token 取得與平台能力偵測
│  └─ 不把 LINE profile 或 decoded token 當成後端權威身分
│
├─ Backend LineIdentityService
│  ├─ 向 LINE Platform 驗證 token、Channel 與有效期限
│  ├─ 將驗證結果正規化為內部 ExternalIdentity
│  └─ 不讓 LINE API 原始回應散落在 Game Service
│
├─ Game Service
│  └─ 僅依賴內部 account／player 身分，不直接依賴 LIFF 或 LINE user profile
│
└─ 執行環境
   ├─ 分別處理 LIFF Browser 與外部瀏覽器
   ├─ Endpoint 與內容使用 HTTPS
   └─ 處理手機 Full View、安全區域、初始化等待、失敗與重試
```

```text
LINE 安全要求
├─ 不記錄 ID token、access token、URL fragment 或完整敏感回應
├─ 不接受前端自行提交的 LINE user ID 作為登入依據
├─ Channel secret 不得進入 Repository；LIFF ID 等非祕密設定使用環境配置管理
├─ 登出、解除綁定與刪除帳號依最新官方規範處理 deauthorization
└─ 未取得使用者同意，不以 cookie 或 Web Storage 串聯 LINE 身分與外部追蹤資料
```

```text
通用敏感資訊要求
├─ 密碼、Secret Key、API Key、Token、私鑰與連線憑證不得進入 Repository
│
├─ 有效敏感值只能由環境變數、未追蹤的本機設定或部署平台 Secret 管理
│
├─ `.env.example` 只保存變數名稱與無法直接使用的提示值，不提供有效憑證
│
├─ Docker Compose、測試資料、文件與程式碼不得提供可直接登入的固定密碼
│
├─ Log、錯誤訊息、URL、測試輸出與完成回報不得揭露敏感值
│
└─ 本機開發便利功能必須限制於 DEBUG，且不得降低 Production 的驗證要求
```

---

## 6. Scope Control

```text
處理需求
├─ 規格內功能
│  └─ 依 PROJECT_SPEC.md 實作並驗證
│
├─ 規格中的待決策事項
│  └─ 不自行定案；需要時請使用者確認
│
├─ 規格明確排除或延後的功能
│  └─ 除非使用者明確要求，否則不實作
│
└─ 規格未提及的新系統
   ├─ 若是完成當前需求不可缺少的最小實作：說明假設後進行
   └─ 若會擴大產品或架構範圍：停止並請使用者決定
```

可以在完成要求後提出未來建議，但不得順帶實作。不要因為內容目標尚未填滿，就複製低品質資料或提前擴充系統。

---

## 7. Infrastructure 與 Dependency

```text
技術選擇
├─ 先使用專案既有 Stack
├─ 標準執行環境與技術棧以 PROJECT_SPEC.md 的技術架構為準
├─ 先確認標準函式庫與現有 Dependency 能否完成需求
├─ 不為小型功能增加 Package
├─ 不為未知需求提前加入基礎設施
└─ 重要 Dependency 若確實必要，完成後說明名稱、原因與用途
```

除非 `PROJECT_SPEC.md`、使用者要求或已出現的實際問題需要，不主動加入新的前端建置鏈、即時系統、背景工作、Cache、Message Queue 或分散式架構。

---

## 8. 測試要求

```text
測試優先順序
├─ 1. Domain Rules
│  ├─ 固定輸入與亂數可重現結果
│  ├─ 公式、上下限與條件分支
│  └─ 不合法狀態不會繼續傳播
│
├─ 2. Application Service
│  ├─ 完整使用案例流程
│  ├─ 成功與失敗結果
│  └─ 獎勵、成長與其他副作用只發生一次
│
├─ 3. 資料一致性與安全
│  ├─ 寫入失敗時全部回滾
│  ├─ 重複與並行請求不造成重複結果
│  └─ 用戶端無法偽造權威資料
│
├─ 4. Query 與整合
│  ├─ 必要關聯不造成 N+1
│  └─ 頁面或端點符合規格流程
│
├─ 5. LINE 平台整合
│  ├─ Mock LINE Platform，不以正式 LIFF URL 或正式 API 進行大量測試
│  ├─ 涵蓋 token 成功、過期、錯誤 Channel 與驗證失敗
│  └─ 涵蓋 LIFF Browser、外部瀏覽器、初始化失敗與重試
│
└─ 6. UI
   └─ 核心操作與重要顯示；UI Snapshot 優先度最低
```

修改規則時，必須同步修改或新增對應的決定性測試、邊界測試及失敗測試。機率功能需要統計測試時，使用合理樣本量與容許誤差，避免不穩定測試。

---

## 9. 程式品質與修改流程

```text
修改流程
├─ 1. 閱讀相關規格、程式與測試
├─ 2. 確認目前行為與真正修改範圍
├─ 3. 檢查工作區既有變更並保留使用者內容
├─ 4. 採取最小、清楚、可測試的修改
├─ 5. 避免無關 Refactor 與提前抽象
├─ 6. 執行與風險相稱的測試
└─ 7. 修正此次變更造成的錯誤
```

優先使用清楚、易讀、小型、直接的程式。不要只因另一種架構看起來更漂亮，就重寫正常運作的模組。

---

## 10. 規格同步規則

```text
變更類型
├─ 產品方向、功能範圍或使用者流程改變
│  └─ 更新 PROJECT_SPEC.md
│
├─ 公式、數值、判定、模型或端點契約改變
│  └─ 更新 PROJECT_SPEC.md
│
├─ 工作方式、品質標準或開發流程改變
│  └─ 更新 AGENTS.md
│
└─ 純內部重構且不改變可觀察行為
   └─ 不修改規格文件
```

不要把 `PROJECT_SPEC.md` 的詳細內容複製進本文件。若實作需要改變產品規格，先完成規格決策再修改程式。

---

## 11. Codex 執行與完成回報

```text
實作任務
├─ 1. Inspect Repository
├─ 2. 找出相關檔案
├─ 3. 直接修改程式
├─ 4. 執行必要指令
├─ 5. 執行相關測試
└─ 6. 修正發現的錯誤
```

如果可以直接修改 Repository，不要只提供 Example Code 要使用者自行貼上。

```text
完成回報
├─ 完成項目
├─ 測試結果
├─ 重要技術決策
└─ 尚未解決問題
```

---

## 12. 決策優先順序

```text
決策優先順序
├─ 1. 規格一致性
├─ 2. 數值與交易完整性
├─ 3. 伺服器權威與安全性
├─ 4. 規則可重現性
├─ 5. 核心遊戲循環
├─ 6. Simplicity
├─ 7. User Readability
├─ 8. Maintainability
├─ 9. Performance
└─ 10. Visual Polish
```

目前 MVP 階段，Visual Polish 優先度最低。

---

## 13. Git 與部署流程

只有在使用者明確要求部署至 Development 或 Production 時，才依照 `GITFLOW.md` 執行對應流程。已在該次要求中授權的正常 Git 步驟不必逐項重複確認，但仍須遵守執行環境的權限核准與安全限制。

LINE Developers Console 的 Channel 建立、Endpoint 設定、權限調整、發布、Review 與 Verified MINI App 送審均屬外部狀態變更，只有使用者明確要求時才執行。發布前必須核對當時最新的 LINE MINI App Policy、台灣 Provider 資格、隱私權政策、服務條款、UI、安全與效能要求。
