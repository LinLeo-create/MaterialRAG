MaterialRAG for Windows
=======================

系統需求
--------
- Windows 10 或 Windows 11（64 位元）
- 第一次建立索引時需要網路連線以下載 Embedding 模型

使用方式
--------
1. 將整個 MaterialRAG 資料夾解壓縮到本機磁碟。
2. 雙擊 MaterialRAG.exe。
3. 瀏覽器會自動開啟；若沒有開啟，請使用視窗中顯示的網址。
4. 在設定頁輸入 Gemini API Key。金鑰會使用 Windows DPAPI 加密保存。

資料位置
--------
索引、模型與設定預設保存在：
%LOCALAPPDATA%\MaterialRAG

移除程式時，如需同時刪除所有使用者資料，可另外刪除上述資料夾。

注意事項
--------
- 請勿只複製 MaterialRAG.exe；必須保留 _internal 資料夾。
- 第一次下載模型可能需要數分鐘，時間取決於網路速度。
- 關閉命令視窗即可停止 MaterialRAG 服務。
