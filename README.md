# 취합체커

취합체커는 폴더 안의 파일명을 기준으로 부서 또는 내 그룹별 제출 여부를 자동 확인하는 Windows용 로컬 웹 프로그램입니다.

- 실행 방식: Python + Flask
- 화면: 웹브라우저 기반 로컬 관리자 페이지
- 저장 방식: 기본 대상은 JSON, 사용자 그룹 설정은 AppData 저장
- 배포 방식: PyInstaller로 생성한 `취합체커.exe` 단독 실행

## 개발 폴더와 배포 폴더

개발 및 테스트용 폴더:

```text
E:\03.datalab\01.서비스 개발\취합체커\submit-checker-dev
```

GitHub 연동 및 최종 배포 기준 폴더:

```text
E:\03.datalab\01.서비스 개발\취합체커\submit-checker
```

최종 배포 작업은 `submit-checker` 폴더 기준으로 진행합니다.

## 개발 모드 실행

```bat
cd /d "E:\03.datalab\01.서비스 개발\취합체커\submit-checker"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

브라우저에서 접속합니다.

```text
http://127.0.0.1:5000
```

## EXE 생성 방법

가장 쉬운 방법은 배치 파일을 실행하는 것입니다.

```bat
build_exe.bat
```

배치 파일은 아래 작업을 자동으로 수행합니다.

- `.venv` 가상환경 생성
- `requirements.txt` 패키지 설치
- PyInstaller 빌드 실행
- `release\취합체커_v1.0` 폴더에 EXE 복사

수동으로 빌드하려면 다음 명령을 사용합니다.

```bat
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm chwihap_checker.spec
```

## EXE 배포 방법

최종 배포 파일:

```text
release\취합체커_v1.0\취합체커.exe
```

다른 Windows PC에는 위 `취합체커.exe` 파일 하나만 복사해서 실행하면 됩니다.
Python, Flask, 프로젝트 폴더, templates/static/data 폴더를 별도로 복사할 필요가 없습니다.

실행 후 자동으로 브라우저가 열리며, 열리지 않는 경우 아래 주소로 접속합니다.

```text
http://127.0.0.1:5000
```

## 설정 저장 위치

EXE로 실행할 때 사용자 그룹 설정은 EXE 파일 옆이 아니라 Windows 사용자 설정 폴더에 저장됩니다.

```text
%APPDATA%\취합체커\custom_groups.json
```

따라서 EXE를 새 버전으로 교체해도 기존 사용자 그룹 설정은 유지됩니다.

## 샘플 테스트

샘플 폴더:

```text
samples
```

테스트 방법:

1. 왼쪽에서 `부서` 또는 `내그룹`을 선택합니다.
2. 검사할 대상을 체크합니다.
3. `선택대상 적용`을 누릅니다.
4. 취합폴더에 `samples` 폴더를 선택합니다.
5. `제출여부 확인`을 실행합니다.

## GitHub 업로드 방법

```bat
cd /d "E:\03.datalab\01.서비스 개발\취합체커\submit-checker"
git status
git add .
git commit -m "Prepare submit checker release"
git push
```

`.gitignore`에 의해 `.venv`, `build`, `dist`, `release`, `__pycache__`, 로그 파일은 GitHub에 올라가지 않습니다.

## 향후 업데이트 방법

1. `submit-checker-dev`에서 기능을 개발하고 테스트합니다.
2. 안정화된 소스만 `submit-checker`에 반영합니다.
3. `submit-checker`에서 `build_exe.bat`를 실행합니다.
4. `release\취합체커_v1.0\취합체커.exe`를 배포합니다.
5. 버전이 바뀌면 release 폴더명을 예: `취합체커_v1.1`로 변경합니다.
