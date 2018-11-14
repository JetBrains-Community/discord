@echo off

set reg50=::&set reg51=::&(reg /?>nul 2>&1 && set reg51=)
if %errorlevel%==5005 set reg50=
set qkey=HKEY_CURRENT_USER\Console&set qprop=QuickEdit
%reg51%if defined qedit_val (echo y|reg add "%qkey%" /v "%qprop%" /t REG_DWORD /d %qedit_val%&goto :mainstart)
%reg50%if defined qedit_val (reg update "%qkey%\%qprop%"=%qedit_val%&goto :mainstart)
%reg51%for /f "tokens=3*" %%i in ('reg query "%qkey%" /v "%qprop%" ^| FINDSTR /I "%qprop%"') DO set qedit_val=%%i
%reg50%for /f "tokens=3*" %%i in ('reg query "%qkey%\%qprop%"') DO set qedit_val=%%i
if "%qedit_val%"=="0" goto :mainstart
if "%qedit_val%"=="0x0" goto :mainstart
%reg51%echo y|reg add "%qkey%" /v "%qprop%" /t REG_DWORD /d 0
%reg50%if "%qedit_val%"=="" reg add "%qkey%\%qprop%"=0 REG_DWORD
%reg50%if "%qedit_val%"=="1" reg update "%qkey%\%qprop%"=0
start "" "cmd" /c set qedit_val=%qedit_val% ^& call "%~dpnx0"&exit

:mainstart
TITLE JetBot
python launch.py
pause Enter to exit...
