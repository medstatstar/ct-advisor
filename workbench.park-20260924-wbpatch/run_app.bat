@echo off
rem ct-advisor 本地同源服务启动器
rem 双击本文件即可在 127.0.0.1:8900 启动服务，随后用系统浏览器打开 http://127.0.0.1:8900/
cd /d "%~dp0"

rem 本地使用：仅监听本机回环（127.0.0.1），不对外网暴露。
rem 云端部署请用发布工具，它会注入 PORT 并以 0.0.0.0 绑定（见 ct-advisor-proxy.py）。
set "CT_PROXY_HOST=127.0.0.1"

set "P="
where python3 >nul 2>nul && set "P=python3"
if not defined P where python >nul 2>nul && set "P=python"
if not defined P where py >nul 2>nul && set "P=py"
if not defined P (
    echo 找不到 Python，请先安装 Python3，或把 WorkBuddy 内置 Python 加入 PATH。
    pause
    exit /b 1
)

echo 正在启动 ct-advisor 本地服务 (http://127.0.0.1:8900/) ...
echo 启动后请在系统浏览器(Edge/Chrome)打开 http://127.0.0.1:8900/ 发送问题。
echo 按 Ctrl+C 停止服务。
%P% ct-advisor-proxy.py
pause
