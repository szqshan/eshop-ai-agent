@echo off
chcp 65001 >nul
echo ==========================================
echo   跨境电商 AI Agent 知识库 · 启动服务
echo ==========================================
echo.
echo [1/2] 启动自动同步（每60秒从GitHub拉取）...
start "自动同步" cmd /k "D:\E_shop_ai_agent\自动同步.bat"
timeout /t 2 >nul

echo [2/2] 启动 Docsify 文档服务...
echo.
echo 本地访问：http://localhost:5000
echo 公网访问：http://217.164.129.130:5000
echo.
docsify serve D:\E_shop_ai_agent\电商知识库 --port 5000
