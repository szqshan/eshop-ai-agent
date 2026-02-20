@echo off
chcp 65001 >nul
echo ==========================================
echo   跨境电商 AI Agent 知识库 · 启动服务
echo ==========================================
echo.
echo 启动 Docsify 文档服务 (端口 5000)...
echo.
echo 本地访问：http://localhost:5000
echo 公网访问：http://217.164.129.130:5000
echo.
echo 把公网地址发给群成员即可！
echo （如公网 IP 变了，运行 curl https://api.ipify.org 重新查询）
echo.
docsify serve D:\E_shop_ai_agent\电商知识库 --port 5000
