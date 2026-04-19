# OCAC 網站部署指南

## 概覽

本站使用 Hugo 靜態網站產生器，部署到 Cloudflare Pages。  
所有內容以 Markdown 撰寫，push 到 GitHub 後自動建構部署。

---

## 第一步：推送到 GitHub

### 1. 建立 GitHub Repository

到 https://github.com/new 建立新 repo：

- Repository name: `ocac-website`（或你喜歡的名稱）
- Visibility: **Public**（Cloudflare Pages 免費方案支援 public/private 都可以）
- 不要勾選 Initialize（我們已經有 commit 了）

### 2. 推送本地 Repo

在終端機中，進入 `ocac-hugo/` 資料夾執行：

```bash
cd ocac-hugo

# 設定你的 Git 身份（如果還沒設定）
git config user.name "mashbean"
git config user.email "mashbean@gmail.com"

# 連結 GitHub remote（把 YOUR_USERNAME 換成你的 GitHub 帳號）
git remote add origin https://github.com/YOUR_USERNAME/ocac-website.git

# 推送
git push -u origin main
```

> 如果 push 速度慢（因為圖片約 275MB），可能需要等幾分鐘。

---

## 第二步：設定 Cloudflare Pages

### 1. 登入 Cloudflare Dashboard

到 https://dash.cloudflare.com 登入（沒帳號就註冊，免費）。

### 2. 建立 Pages 專案

- 左側選單點 **Workers & Pages**
- 點 **Create** → **Pages** → **Connect to Git**
- 授權 GitHub，選擇 `ocac-website` repo

### 3. 設定建構參數

| 欄位 | 值 |
|------|-----|
| Production branch | `main` |
| Build command | `hugo --gc --minify` |
| Build output directory | `public` |
| Root directory | （留空） |

在 **Environment variables** 加入：

| Variable name | Value |
|---------------|-------|
| `HUGO_VERSION` | `0.147.0` |

點 **Save and Deploy**，等待第一次建構完成。

### 4. 綁定自訂網域 ocac.tw

建構成功後：

- 進入專案 → **Custom domains** → **Set up a custom domain**
- 輸入 `ocac.tw`
- Cloudflare 會告訴你需要設定的 DNS 記錄

**DNS 設定方式取決於你的網域在哪裡管理：**

**方案 A — 網域已在 Cloudflare（推薦）**  
Cloudflare 會自動新增 CNAME 記錄，點確認即可。

**方案 B — 網域在其他註冊商**  
到你的域名管理後台，新增 CNAME 記錄：

```
類型: CNAME
名稱: @（或 ocac.tw）
目標: ocac-website.pages.dev（Cloudflare 會告訴你確切值）
```

或者，把 nameserver 轉移到 Cloudflare（免費方案即可），這樣管理最方便。

> DNS 生效通常需要幾分鐘到幾小時。HTTPS 證書 Cloudflare 會自動處理。

---

## 日常維護：編輯與新增內容

### 編輯現有文章

1. 找到對應的 Markdown 檔案，例如：
   - `content/zh/archive/petamu-project.md`（中文）
   - `content/en/archive/petamu-project.md`（英文）

2. 用任何文字編輯器打開，修改內容

3. 推送更新：
```bash
git add content/zh/archive/petamu-project.md
git commit -m "更新 PETAMU Project 文章內容"
git push
```

Cloudflare 會在幾十秒內自動重新建構部署。

### 新增文章

在對應的資料夾建立 `.md` 檔案，格式如下：

```markdown
---
title: "文章標題"
date: 2024-03-15T00:00:00+08:00
draft: false
image: "/images/k2/items/cache/your-image.jpg"
tags:
  - "標籤一"
  - "標籤二"
---

文章內容用 Markdown 語法撰寫。

**粗體** 和 *斜體* 都可以用。

![圖片說明](/images/your-image.jpg)
```

中英文各需一個檔案：
- `content/zh/archive/new-article.md`
- `content/en/archive/new-article.md`

### 新增圖片

把圖片放到 `static/images/` 對應的資料夾，然後在 Markdown 中引用：

```markdown
![圖片說明](/images/k2/galleries/123/photo.jpg)
```

---

## 目錄結構速查

```
ocac-hugo/
├── hugo.toml              ← 網站設定（標題、選單、語言）
├── content/
│   ├── zh/                ← 中文內容
│   │   ├── archive/       ← 歷年活動
│   │   ├── artists/       ← 藝術家
│   │   ├── artspaces/     ← 藝術空間
│   │   ├── about/         ← 關於
│   │   ├── visit/         ← 參觀
│   │   └── contact/       ← 聯絡
│   └── en/                ← 英文內容（結構同上）
├── layouts/               ← HTML 版面模板
│   ├── _default/          ← 預設版面（list, single, baseof）
│   ├── partials/          ← 共用元件（header, footer）
│   └── index.html         ← 首頁
├── static/
│   ├── css/main.css       ← 樣式表
│   ├── js/main.js         ← JavaScript
│   └── images/            ← 所有圖片
└── public/                ← 建構輸出（不需 commit）
```

---

## 本地預覽

如果你想在推送前先預覽：

```bash
# 安裝 Hugo（macOS）
brew install hugo

# 啟動本地伺服器
cd ocac-hugo
hugo server -D

# 打開瀏覽器 http://localhost:1313
```

---

## 費用

| 項目 | 年費 |
|------|------|
| Cloudflare Pages | 免費 |
| GitHub | 免費 |
| ocac.tw 網域續約 | ~NT$800-1,200 |
| **總計** | **~NT$1,000/年** |
