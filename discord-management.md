# Discord + NAS 多用戶管理規範

## 架構總覽

```
Discord 伺服器 (Thoth-NAS)
├── 📋 資訊
│   └── #info（唯讀，只有 Bot 能發訊）
├── 👤 成員頻道
│   ├── #小king（私有）
│   ├── #member-a（私有）
│   └── ...
├── 💬 公共
│   ├── #general（閒聊）
│   ├── #bot-help（提問）
│   └── #project-requests（申請開項目）
└── 📁 項目
    ├── #xxx（A + B + Bot）
    └── #yyy（A + B + C + Bot）

飛牛 NAS
├── /vol1/1000/projects/
│   ├── project-xxx/   ← Bot 建共享目錄，設 ACL 權限
│   └── project-yyy/   ← Bot 建共享目錄，設 ACL 權限
└── /vol1/<uid>/
    └── 每個用戶的個人目錄（私有）
```

## 角色體系

| 角色 | 權限 | 誰有 |
|------|------|------|
| Admin | 全權限，管理伺服器 | 小king |
| Member | 自己頻道 + 公共頻道 + 被邀請的項目頻道 | 所有成員 |
| Bot | 所有頻道 + NAS 管理員（trim-cli + sudo），遵守隔離規則 | Thoth |

## 身份隔離

- **記憶隔離**：Bot 在成員頻道不載入 Admin 的私人記憶（MEMORY.md）
- **權限隔離**：成員只能操作自己 NAS 目錄 + 被授權的共享目錄
- **對話隔離**：Bot 不跨頻道提及他人內容
- **統一人格**：Bot 在所有頻道都是 Thoth，性格一致

---

## 新成員加入流程（全自動）

### 觸發方式

Admin 在任何頻道告訴 Bot：

> 「新成員：Discord ID = xxx, 用戶名 = member-a」

或成員加入 Discord 伺服器後，Admin 確認身份。

### Bot 自動執行

#### 1. NAS 帳號

```bash
trim-cli login -u lam151251 -p '***'
trim-cli user add member-a --password '<隨機密碼>' --yes
```

#### 2. Discord 初始化

1. **分配 Member 角色**
2. **建立專屬頻道**：
   - 頻道名：成員名稱
   - 位置：👤 成員頻道 分類下
   - 權限：@everyone 拒絕查看、該成員可讀寫、Bot 可讀寫
3. **發送歡迎訊息**（含 NAS 密碼）：
   ```
   🏛️ 歡迎來到你的專屬頻道！

   這裡只有你和管理員和 Thoth 可見。
   直接發訊息就可以叫我做事：
   - NAS 檔案管理
   - 查詢資訊
   - 自動化任務

   🔑 你的 NAS 帳號已建立：
   - 用戶名：member-a
   - 密碼：xxxxxx（首次登入請修改）

   如有問題到 #bot-help 提問。
   ```
4. **記錄成員資訊**到 `memory/discord-members.json`

---

## 開新項目流程（全自動）

### 觸發方式

成員在 **#project-requests** 頻道發訊：

> 「開新項目：項目名稱 = web-app，描述 = 網站開發，邀請成員 = @member-a, @member-b」

### Bot 自動執行

#### Step 1：Discord 頻道

1. 在 📁 項目 分類下建立頻道 `#web-app`（直接用項目名，不加 `project-` 前綴）
2. 設定權限：
   - @everyone：拒絕查看
   - 申請者：可讀寫
   - 被邀請成員：可讀寫
   - Bot：可讀寫
3. 發送項目資訊訊息：
   ```
   📁 項目：web-app
   描述：網站開發
   成員：@member-a, @member-b
   NAS 目錄：projects/web-app
   建立時間：2026-07-31
   ```

#### Step 2：NAS 共享目錄

```bash
# 建立項目目錄
trim-cli file mkdir /vol1/1000/projects/web-app

# 設定共享權限給項目成員
trim-cli file share add /vol1/1000/projects/web-app web-app \
  --permset '[{"uid":1001,"perm":"rw"},{"uid":1002,"perm":"rw"}]'
```

所有被邀請的成員自動獲得讀寫權限，可通過「他人共享」存取。

#### Step 3：記錄項目資訊

Bot 更新 `memory/discord-projects.json`：

```json
{
  "projects": [
    {
      "name": "web-app",
      "description": "網站開發",
      "discordChannelId": "xxx",
      "nasPath": "/vol1/1000/projects/web-app",
      "members": ["501559258492698637", "xxx", "yyy"],
      "createdBy": "小king",
      "createdAt": "2026-07-31",
      "status": "active"
    }
  ]
}
```

#### Step 4：通知

在項目頻道發訊：
```
✅ 項目 web-app 已建立！
📁 NAS 共享目錄已就緒，成員可通過「他人共享」存取。
```

---

## 邀請成員加入項目（全自動）

### 觸發方式

項目成員在項目頻道發訊：

> 「邀請 @member-c 加入項目」

### Bot 自動執行

1. **Discord**：把被邀請者加到項目頻道權限（可讀寫）
2. **NAS**：通過 trim-cli 把 member-c 加到共享目錄權限裡（讀寫）
3. **通知**：在項目頻道發訊 `✅ @member-c 已加入項目 web-app`
4. **更新**：更新 `memory/discord-projects.json` 的成員列表

---

## 移除成員 / 退出項目（全自動）

### 成員主動退出

> 「退出項目 web-app」

Bot 執行：
1. Discord：移除該成員的頻道權限
2. NAS：通過 trim-cli 移除該成員的共享目錄權限
3. 通知項目頻道
4. 更新記錄

### Admin 踢出成員

同理，Admin 指示 Bot 執行。

---

## 項目歸檔 / 刪除（全自動）

### 歸檔

> 「歸檔項目 web-app」

Bot 執行：
1. Discord：頻道設為唯讀，名稱改為 `#archived-web-app`
2. NAS：共享目錄權限改為全員只讀，頻道名改為 `#archived-xxx`
3. 更新項目狀態為 `archived`

### 刪除

> 「刪除項目 web-app」

Bot 執行：
1. Discord：刪除頻道
2. NAS：刪除共享目錄（先確認無重要數據）
3. 從記錄中移除

---

## Bot 行為規範

### 在成員私人頻道
- 只處理該成員的請求
- 只操作該成員的 NAS 個人目錄
- 不提及其他成員或項目內容

### 在項目頻道
- 處理所有項目成員的請求
- 操作該項目的共享目錄
- 不操作成員的個人目錄
- 記錄誰做了什麼（可選）

### 在 #項目申請 頻道
- 監聽項目申請，自動建立 Discord 頻道 + NAS 共享目錄
- 申請者必須是已註冊成員
- 建立前檢查項目名稱是否已存在
- 回覆申請進度（建立中 → 完成）
- 支援查詢指令：`我的項目`

### 在公共頻道
- 只回應被 @mention 或直接問的問題
- 不執行敏感操作（刪除、系統修改）
- 只有 Admin 能觸發管理操作

### 在 #info 頻道
- 不回應任何訊息（唯讀頻道）
- 只有 Bot 能發佈/更新資訊

---

## 安全規則

1. **成員只能看到**：自己的私人頻道 + 被邀請的項目頻道 + 公共頻道
2. **成員只能操作**：自己的 NAS 目錄 + 被授權的共享目錄
3. **敏感操作需 Admin**：刪除項目、踢除成員、修改伺服器結構
4. **Bot 不洩露**：不跨頻道提及他人內容、不顯示 Admin 的私人資訊
5. **日誌**：Bot 記錄所有項目操作（建立、邀請、刪除等）到 `memory/discord-audit.log`
6. **命名衝突**：建項目前檢查同名項目，已存在則拒絕
7. **Session 管理**：Bot 每次操作 NAS 前確保 trim-cli 已登入
8. **密碼安全**：NAS 密碼只通過私人頻道發送，建議成員首次登入修改
9. **成員離開清理**：刪除 NAS 帳號時同步移除所有項目的共享權限 + Discord 頻道權限

---

## 成員查詢指令

| 指令 | 位置 | 功能 |
|------|------|------|
| `我的項目` | 任何頻道 | 列出你參與的所有項目 |
| `我的資訊` | 私人頻道 | 查看你的 NAS 帳號資訊 |
| `項目列表` | #項目申請 | 列出所有公開項目（隱藏你沒權限的） |

---

## 成員離開 / 刪除流程（全自動）

### 觸發方式

Admin 在私人頻道告訴 Bot：
> 「移除成員 member-a」

### Bot 自動執行

1. **NAS**：移除該成員在所有共享目錄的權限
2. **NAS**：刪除該成員的 NAS 帳號（保留個人目錄資料 30 天）
3. **Discord**：移除該成員在所有項目頻道的權限
4. **Discord**：刪除該成員的私人頻道
5. **Discord**：移除 Member 角色
6. **更新**：從 `memory/discord-members.json` 移除，記錄到審計日誌

---

## 飛牛 NAS 操作速查（Bot 用）

| 操作 | 命令 |
|------|------|
| 建用戶 | `trim-cli user add <name> --password '<pw>' --yes` |
| 刪用戶 | `trim-cli user del <name> --yes` |
| 改密碼 | `trim-cli user mod <name> --password '<pw>'` |
| 列用戶 | `trim-cli user list` |
| 建目錄 | `trim-cli file mkdir <path>` |
| 建共享 | `trim-cli file share add <path> <name> --permset '<json>'` |
| 刪共享 | `trim-cli file share del <name>` |
| 查權限 | `trim-cli file acl get <path>` |
| 列共享 | `trim-cli file share list` |

### permset JSON 格式

```json
[{"uid":1001,"perm":"rw"},{"uid":1002,"perm":"r"}]
```

- `rw` = 讀寫
- `r` = 只讀
