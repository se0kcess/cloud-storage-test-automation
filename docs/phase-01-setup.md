# Phase 1 — GitHub 저장소와 Python 개발 환경

## 1. 실습 목적

다른 컴퓨터에서도 같은 의존성으로 실행할 수 있는 QA 실습 기반을 만든다.
이번 단계의 완료 조건은 원격 저장소 연결, Python 가상환경, 의존성 설치와 점검, 비밀정보 제외 확인이다.
S3 기능 검증은 다음 단계에서 서버를 준비한 후 시작한다.

## 2. 기술 개념과 동작 원리

- Git은 로컬 변경 이력을 기록한다. GitHub는 원격 저장소와 협업·CI 기능을 제공한다.
- `origin`은 원격 주소의 별칭이다. `fetch`는 원격 이력을 가져오고 `push`는 로컬 커밋을 업로드한다.
- `main`이 `origin/main`을 추적하면 로컬과 원격의 앞섬/뒤처짐을 확인할 수 있다.
- `venv`는 프로젝트의 Python 패키지 설치 공간을 분리한다. 컨테이너처럼 OS를 격리하지는 않는다.
- `python -m pip`는 현재 Python에 속한 pip를 실행한다. 다른 Python에 잘못 설치하는 실수를 줄인다.
- `==`는 버전을 고정한다. 직접 의존성과 간접 의존성까지 기록해야 실행 환경의 차이를 줄일 수 있다.
- `.gitignore`는 아직 추적하지 않은 파일을 제외한다. 이미 커밋한 비밀을 지우거나 폐기하지는 않는다.

## 3. 구현 방법과 코드

| 파일/폴더 | 역할 |
|---|---|
| `requirements.txt` | 직접 의존성 버전; 로컬 설치 검증 완료 |
| `requirements.lock.txt` | 간접 의존성을 포함한 실제 설치 버전 |
| `.env.example` | 실제 비밀값이 없는 설정 항목 예시 |
| `.gitignore` | 가상환경·비밀정보·reports·Terraform state 제외 |
| `pytest.ini` | 테스트 탐색 경로와 marker 이름 정의 |
| `scripts/check_environment.py` | Python 3.12, venv, 고정 버전 설치 여부 확인 |
| `tests/common`, `tests/minio`, `tests/aws` | 향후 공통/대상별 테스트 위치 |
| `clients`, `infra` | 향후 S3 adapter와 인프라 코드 위치 |

빈 폴더는 Git이 저장하지 않으므로 `.gitkeep`을 넣었다. 현재 API 구현과 테스트는 없다.
marker 정의 자체는 실행을 막지 않는다. AWS/파괴 테스트 실행 전 대상과 명시적 동의를 검사하는 장치는 Phase 4에서 만든다.
`.env` 파일은 Python이 자동으로 읽지 않는다. Phase 2에서 Compose와 설정 로딩 방식을 설명한다.
지금은 `.env.example`의 비밀값을 비워 두며 AWS 키는 넣지 않는다.

## 4. 터미널 실행 명령어

### 기존 실습 폴더에서 이어가기

```bash
cd /Users/se0k_cess/Downloads/cloud-storage-qa
git status --short --branch
git remote -v
source .venv/bin/activate
python --version
python -m pip check
python scripts/check_environment.py
```

### 새 컴퓨터에서 재현하기 (첫 push 이후)

```bash
git clone https://github.com/se0kcess/cloud-storage-test-automation.git
cd cloud-storage-test-automation
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python scripts/check_environment.py
```

`source`는 현재 터미널의 PATH를 바꾼다. 새 터미널을 열 때마다 다시 활성화하거나 `.venv/bin/python`을 직접 사용한다.
종료할 때는 `deactivate`를 실행한다. 패키지 변경은 의도적으로 버전을 검토할 때만 한다.
최초 설치는 공간 부족으로 중단됐으나 재시도에서 설치·import·환경 점검이 통과했다. 동일 버전 재현 시 `python -m pip install -r requirements.lock.txt`를 사용한다.

```bash
# 전체 설치 및 import 검증 성공 후에만 실행
python -m pip install -r requirements.txt
python -c 'import boto3, pytest, requests, pytest_html; print("imports OK")'
python -m pip freeze > requirements.lock.txt
python -m pip check
```

`pip freeze`는 취약점 검사나 모든 OS에 대한 호환성 보장을 제공하지 않는다.

## 5. 기대 결과 및 검증 방법

```bash
git branch -vv
git check-ignore .venv/example .env .env.local reports/example.html infra/terraform/example.tfstate
git check-ignore .env.example
python -c 'import boto3, pytest, requests, pytest_html; print("imports OK")'
python -m pytest --version
python -m pip check
python scripts/check_environment.py
```

`main`은 `origin/main`을 추적해야 한다. 민감 파일 경로는 제외 규칙에 잡혀야 한다.
반대로 `.env.example`은 출력이 없고 종료 코드 1이어야 한다. 추적해야 하는 안전한 예시 파일이기 때문이다.
pip check는 `No broken requirements found.`, 환경 점검은 `PASS`로 끝나야 한다.
테스트 파일은 Phase 4에서 추가한다. 현재 `pytest --collect-only -q`는 0개와 종료 코드 5가 예상되며 성공으로 계산하지 않는다.

실제 실행 증거는 로컬 전용 `docs/phase-01-evidence.md`에 별도로 남기며 GitHub에는 업로드하지 않는다.

## 6. 트러블슈팅

| 증상 | 확인 및 해결 |
|---|---|
| `python3.12: command not found` | Python 3.12 설치/PATH를 확인하고 `python3.12 --version`으로 검증 |
| `ModuleNotFoundError` | `source .venv/bin/activate` 후 `python -m pip install -r requirements.txt` |
| `No space left on device` | `df -h .`로 공간 확인. 사용자 데이터 정리나 디스크 확장 후 설치 재시도. `--no-cache-dir`만으로 해결되지 않을 수 있음 |
| Python 3.13 등 다른 버전 실행 | `python -c 'import sys; print(sys.executable)'`로 경로 확인 |
| `CERTIFICATE_VERIFY_FAILED` | Python 배포판의 CA 설정을 확인. pip가 정상 동작한다면 먼저 pip로 설치. TLS 검증 해제나 `--trusted-host`로 우회하지 않음 |
| DNS/연결 오류 | 네트워크·프록시·실행 권한 확인. 패키지 설치 실패를 테스트 실패와 구분 |
| `no tests ran` / 종료 코드 5 | Phase 1에서는 예상 상태. 실제 기능 검증 성공은 아님 |
| `.env`가 Git에 표시됨 | `git check-ignore -v .env`로 규칙 확인. 이미 추적한 파일에는 ignore가 적용되지 않음 |
| push 인증 실패 | GitHub의 SSH 또는 자격증명 관리자를 사용. 비밀번호·토큰을 원격 URL이나 소스에 넣지 않음 |
| `non-fast-forward` | `git fetch origin`과 `git log --oneline --graph --all`로 차이 확인 후 통합. 강제 push는 사용하지 않음 |

현재 Docker CLI/Compose는 설치 여부만 확인했다. Docker daemon, 이미지 빌드와 MinIO 호환성은 Phase 2에서 확인한다.
Python 3.12.1은 현재 설치된 버전이며 최신 패치라는 의미는 아니다. 패치 업데이트는 별도 설치 후 같은 점검으로 검증한다.

## 7. 기술면접 예상 질문

1. **Git과 GitHub는 어떻게 다른가?** Git은 변경 이력을 관리하는 도구이며 GitHub는 원격 저장소·리뷰·CI를 제공하는 서비스다.
2. **왜 venv를 사용하는가?** 프로젝트별 패키지 충돌을 줄이고 설치 공간을 분리하기 위해서다. OS 수준 격리는 하지 않는다.
3. **버전 고정만으로 재현성이 완성되는가?** 아니다. Python/OS/이미지 버전, 환경 설정과 외부 서비스 차이도 통제하고 실제 실행으로 확인해야 한다.
4. **Boto3와 Requests의 역할은?** Boto3는 AWS API 모델·서명·재시도 등을 제공하는 SDK이며 Requests는 일반 HTTP 통신 라이브러리다. health check와 API 요청의 목적에 맞춰 선택한다.
5. **.gitignore에 키를 추가하면 유출이 해결되는가?** 아니다. 이미 노출된 키는 폐기/교체해야 하며 Git 이력과 배포 경로도 점검해야 한다.
6. **설치 점검 PASS가 스토리지 품질을 보장하는가?** 아니다. 현재 점검은 개발 환경만 확인한다. 서버 기능·권한·무결성·복구는 별도 검증이 필요하다.

## 8. Git 커밋 메시지

권장 메시지: `chore: initialize phase 1 QA development environment`

먼저 아래 목록과 diff를 확인하고 로컬 커밋한다. 작성자 정보가 없다면 본인의 이름과 GitHub noreply 이메일을 저장소 범위에서 설정한다.

```bash
git status --short
git diff --check
git diff
git add README.md AGENTS.md docs .gitignore .env.example requirements.txt requirements.lock.txt pytest.ini scripts clients tests infra
git diff --cached --stat
git diff --cached
git commit -m "chore: initialize phase 1 QA development environment"
```

검토와 명시적인 업로드 승인을 받은 후 첫 push에 사용할 명령은 아래와 같다. 현재 자동으로 실행하지 않는다.

```bash
git push -u origin main
```

이 단계는 로컬 준비만으로 AWS 비용이 발생하지 않는다. GitHub Actions 사용량과 AWS 비용은 해당 Phase에서 별도로 검토한다.
