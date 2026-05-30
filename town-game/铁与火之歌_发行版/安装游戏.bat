@echo off
chcp 65001 >nul
title 铁与火之歌 - 安装程序

echo.
echo ========================================
echo   铁与火之歌 - 19世纪欧洲手工艺人传奇
echo   安装程序
echo ========================================
echo.
echo 欢迎安装「铁与火之歌」文字冒险游戏
echo.
echo 本游戏需要以下环境：
echo   - Windows 7 或更高版本
echo   - 无额外依赖，开箱即用
echo.
echo ========================================
echo.

:: 设置安装路径
set INSTALL_DIR=%PROGRAMFILES%\铁与火之歌
set GAME_NAME=铁与火之歌

:: 检查是否已安装
if exist "%INSTALL_DIR%" (
    echo 检测到已安装版本，将进行更新安装。
    echo.
)

:: 创建安装目录
echo [1/4] 创建安装目录...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: 复制文件
echo [2/4] 复制游戏文件...
copy /Y "%~dp0dist\铁与火之歌.exe" "%INSTALL_DIR%\" >nul
if errorlevel 1 (
    echo 错误：无法复制游戏文件！
    pause
    exit /b 1
)

:: 复制数据文件（如果有）
if exist "%~dp0data" (
    xcopy /Y /E /I "%~dp0data" "%INSTALL_DIR%\data" >nul
)

:: 复制文档
copy /Y "%~dp0README.md" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "%~dp0BACKGROUND.md" "%INSTALL_DIR%\" >nul 2>&1
copy /Y "%~dp0PROFESSION_GUIDE.md" "%INSTALL_DIR%\" >nul 2>&1

:: 创建卸载程序
echo [3/4] 创建卸载程序...
(
echo @echo off
echo chcp 65001 ^>nul
echo title 铁与火之歌 - 卸载程序
echo echo.
echo echo 正在卸载「铁与火之歌」...
echo echo.
echo echo 删除安装目录...
echo rmdir /S /Q "%INSTALL_DIR%"
echo echo.
echo echo 删除桌面快捷方式...
echo del /Q "%USERPROFILE%\Desktop\铁与火之歌.lnk" 2^>nul
echo echo.
echo echo 卸载完成！
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

:: 创建桌面快捷方式
echo [4/4] 创建桌面快捷方式...
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo Set shortcut = WshShell.CreateShortcut^("%USERPROFILE%\Desktop\铁与火之歌.lnk"^)
echo shortcut.TargetPath = "%INSTALL_DIR%\铁与火之歌.exe"
echo shortcut.WorkingDirectory = "%INSTALL_DIR%"
echo shortcut.Description = "19世纪欧洲手工艺人传奇"
echo shortcut.Save
) > "%TEMP%\create_shortcut.vbs"
cscript //nologo "%TEMP%\create_shortcut.vbs" >nul
del /Q "%TEMP%\create_shortcut.vbs" >nul 2>&1

:: 创建开始菜单快捷方式
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\铁与火之歌" (
    mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\铁与火之歌"
)
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo Set shortcut = WshShell.CreateShortcut^("%APPDATA%\Microsoft\Windows\Start Menu\Programs\铁与火之歌\铁与火之歌.lnk"^)
echo shortcut.TargetPath = "%INSTALL_DIR%\铁与火之歌.exe"
echo shortcut.WorkingDirectory = "%INSTALL_DIR%"
echo shortcut.Description = "19世纪欧洲手工艺人传奇"
echo shortcut.Save
) > "%TEMP%\create_shortcut2.vbs"
cscript //nologo "%TEMP%\create_shortcut2.vbs" >nul
del /Q "%TEMP%\create_shortcut2.vbs" >nul 2>&1

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 游戏已安装到: %INSTALL_DIR%
echo 桌面快捷方式已创建
echo.
echo 点击桌面图标或开始菜单中的「铁与火之歌」即可开始游戏。
echo.
echo 感谢安装！祝你游戏愉快！
echo.
pause
