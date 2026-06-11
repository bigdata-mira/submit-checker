@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

echo [1/4] Python 가상환경 확인
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 python -m venv .venv
)

echo [2/4] 패키지 설치
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto error

echo [3/4] EXE 빌드
python -m PyInstaller --clean --noconfirm chwihap_checker.spec
if errorlevel 1 goto error

echo [4/4] release 폴더 생성
if not exist "release\취합체커_v1.0" mkdir "release\취합체커_v1.0"
copy /Y "dist\취합체커.exe" "release\취합체커_v1.0\취합체커.exe" > nul

echo.
echo 완료: release\취합체커_v1.0\취합체커.exe
pause
exit /b 0

:error
echo.
echo 빌드 중 오류가 발생했습니다.
pause
exit /b 1
