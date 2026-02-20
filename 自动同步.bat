@echo off
chcp 65001 >nul
echo 自动同步已启动，每 60 秒从 GitHub 拉取最新内容...
echo 不要关闭此窗口。
echo.
:loop
git -C "D:\E_shop_ai_agent" pull origin master
timeout /t 60 /nobreak >nul
goto loop
