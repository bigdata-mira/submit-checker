# 취합체커

취합체커는 지정한 폴더 안의 파일명을 기준으로 대상별 제출 여부를 자동 확인하는 로컬 웹 애플리케이션입니다.

반복적으로 제출 대상 목록과 실제 제출 파일을 대조해야 하는 업무를 줄이기 위해 만들어졌으며, 데이터베이스 없이 JSON 파일과 로컬 저장소를 사용합니다. 사용자는 웹브라우저에서 취합 대상과 폴더를 선택하고, 제출/미제출 현황을 한눈에 확인할 수 있습니다.

## 주요 기능

- 폴더 안의 파일명을 스캔하여 제출 여부 자동 판정
- 기본 부서 대상 목록 제공
- 사용자 그룹 생성 및 대상 관리
- 대상 직접 추가 및 엑셀 일괄 등록
- 선택한 대상만 검사대상으로 적용
- 제출/미제출 요약 KPI 표시
- 제출률 진행률 표시
- 결과 CSV 다운로드
- EXE 실행 시 브라우저 자동 실행
- 사용자 그룹 설정을 Windows AppData에 저장

## 설치 방법

Python으로 직접 실행하려면 Python 3.11 이상을 권장합니다.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 실행 방법

개발 모드에서는 아래 명령으로 실행합니다.

```bat
python app.py
```

브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:5000
```

EXE 배포본을 사용하는 경우에는 `취합체커.exe` 또는 릴리스에 첨부된 실행 파일을 더블클릭하면 됩니다.

## EXE 빌드 방법

PyInstaller를 사용해 Windows 실행 파일을 생성합니다.

가장 간단한 방법은 배치 파일을 실행하는 것입니다.

```bat
build_exe.bat
```

수동으로 빌드하려면 아래 명령을 실행합니다.

```bat
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm chwihap_checker.spec
```

빌드가 완료되면 실행 파일은 `dist` 폴더에 생성됩니다.

```text
dist\취합체커.exe
```

배치 파일을 사용하면 배포용 폴더에도 실행 파일이 복사됩니다.

```text
release\취합체커_v1.0\취합체커.exe
```

## 폴더 구조

```text
submit-checker/
  app.py
  build_exe.bat
  chwihap_checker.spec
  requirements.txt
  README.md
  data/
    targets.json
    custom_groups.json
  src/
    checker.py
    custom_group_routes.py
    custom_groups.py
    exporter.py
    page_state.py
    paths.py
    target_manager.py
    target_seed.py
  static/
    style.css
  templates/
    index.html
```

주요 역할은 다음과 같습니다.

- `app.py`: Flask 애플리케이션 진입점
- `src/checker.py`: 파일 스캔 및 제출 여부 판정 로직
- `src/target_manager.py`: 기본 대상 및 사용자 그룹 데이터 로딩
- `src/custom_groups.py`: 사용자 그룹 추가, 수정, 삭제 로직
- `src/exporter.py`: CSV 다운로드 생성
- `src/paths.py`: 개발 환경과 EXE 환경의 경로 처리
- `templates/index.html`: 웹 화면 템플릿
- `static/style.css`: 화면 스타일
- `data/targets.json`: 기본 취합 대상 목록
- `data/custom_groups.json`: 초기 사용자 그룹 데이터
- `chwihap_checker.spec`: PyInstaller 빌드 설정

## 사용 예시

1. 취합체커를 실행합니다.
2. 브라우저에서 `http://127.0.0.1:5000`에 접속합니다.
3. 왼쪽에서 `부서` 또는 `내그룹`을 선택합니다.
4. 검사할 대상을 체크합니다.
5. `선택대상 적용`을 누릅니다.
6. 취합 파일이 들어 있는 폴더를 선택합니다.
7. `제출여부 확인`을 실행합니다.
8. 결과 화면에서 제출 수, 미제출 수, 제출률, 제출파일명을 확인합니다.
9. 필요한 경우 CSV로 다운로드합니다.

파일명에 대상명이 포함되어 있으면 제출로 판단합니다.

```text
대상명_제출자료.xlsx
2026_업무계획_대상명.pdf
```

지원 확장자는 다음과 같습니다.

```text
hwp, hwpx, xls, xlsx, docx, pdf
```

임시 파일과 폴더는 검사 대상에서 제외됩니다.

```text
~$ 로 시작하는 파일
.tmp 파일
폴더
```

## 설정 저장 위치

EXE로 실행할 때 사용자 그룹 설정은 실행 파일 옆이 아니라 Windows 사용자 설정 폴더에 저장됩니다.

```text
%APPDATA%\취합체커\custom_groups.json
```

따라서 EXE 파일을 새 버전으로 교체해도 기존 사용자 그룹 설정은 유지됩니다.

## 라이선스

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
