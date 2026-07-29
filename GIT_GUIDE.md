
# Git 基本使用指南

## 1. 初始化設定

第一次使用 Git 時，設定名稱與電子郵件：

```powershell
git config --global user.name "你的名稱"
git config --global user.email "你的電子郵件"
```

## 2. 建立 Git Repository

進入專案目錄並初始化：

```powershell
cd C:\你的專案
git init
git branch -M main
```

加入檔案並建立第一次 commit：

```powershell
git add .
git commit -m "Initialize project"
```

連接 GitHub Repository：

```powershell
git remote add origin https://github.com/你的帳號/專案名稱.git
git push -u origin main
```

## 3. 取得別人的 Repository

下載 GitHub 專案：

```powershell
git clone https://github.com/對方帳號/專案名稱.git
cd 專案名稱
```

如果對方修改了你的專案，建議請對方在 GitHub 建立 Pull Request，再透過 GitHub 審查及合併。

## 4. 開發流程

開始新功能前，同步最新進度：

```powershell
git switch main
git pull
```

建立新的功能分支：

```PowerShell
git switch -c feature/功能名稱
```

完成修改後提交：

```powershell
git add .
git commit -m "說明本次修改"
git push -u origin feature/功能名稱
```

接著在 GitHub 建立 PR (Pull Request)：

Pull Request 合併後，更新本機 `main`：

```powershell
git switch main
git pull
```

刪除已合併的本機分支：

```powershell
git branch -d feature/功能名稱
```

## 5. 安全原則

- 不要直接在 `main` 開發新功能。
- 不要提交密碼、Token、`.env` 或其他機密資料。
- 使用 `.gitignore` 排除環境、快取、量測資料及輸出檔。
- 不要隨意使用 `git reset --hard`、`git push --force` 或 `git branch -D`。
- 推送前先完成相關測試。
- 功能修改應透過 Pull Request 合併至 `main`。

基本流程：

```text
建立功能分支
→ 修改與測試
→ Commit
→ Push
→ Pull Request
→ 合併
→ 更新 main
```
