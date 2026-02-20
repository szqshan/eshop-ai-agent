@echo off
chcp 65001 >nul
echo 正在开启防火墙端口 5000...
netsh advfirewall firewall add rule name="电商知识库-Docsify-5000" dir=in action=allow protocol=TCP localport=5000
if %errorlevel%==0 (
    echo 成功！端口 5000 已开放。
) else (
    echo 失败，请确认以管理员身份运行。
)
pause
