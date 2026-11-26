# cloud-storage-test-automation

S3 호환 오브젝트 스토리지 QA 자동화 실습 프로젝트입니다.
기능·인증/인가·데이터 무결성·장애 복구를 검증하고, 재현 가능한 실행 방법과 실제 증거를 남깁니다.

- 저장소: https://github.com/se0kcess/cloud-storage-test-automation
- 전체 요구사항 및 단계: [프로젝트 명세](docs/PROJECT_SPEC.md)
- 기존 로컬 시작 안내: [보존본](docs/reference/starter-readme.md)

## 단계별 학습 흐름

| Phase | 실습 | 얻을 수 있는 검증 증거 |
|---|---|---|
| 1 | Git/GitHub, Python 3.12 venv, 기본 구조 | 환경 점검 및 의존성 기록 |
| 2 | Docker/MinIO, Compose, named volume | health check 및 재생성 후 데이터 유지 |
| 3 | Boto3 CRUD, 공통 client, 테스트 설계 | 요구사항과 케이스의 연결 |
| 4 | Pytest fixture/marker/parameterize | API·경계값·권한·SHA-256 검증 결과 |
| 5 | GitHub Actions CI | 성공/실패 품질 게이트 및 HTML/JUnit artifacts |
| 6 | AWS EC2/VPC/IAM/EBS/S3/CloudWatch 설계 | 비용·권한·네트워크 검토 및 승인 후 실행 증거 |
| 7 | ECR/OIDC CD | 검증한 이미지 digest 배포 및 복구 기록 |
| 8 | AWS S3 및 IAM/정책 검증 | MinIO와 AWS 공통/차이 비교 |
| 9 | Terraform | fmt/validate/plan, 승인 후 apply/destroy 기록 |
| 10 | 로컬 Kind Kubernetes | PVC 유지, probes 및 복구 시간 측정 |
| 11 | 포트폴리오 정리 | 아키텍처·실제 결과·한계·문제 해결 기록 |

EKS와 성능 도구는 선택 사항입니다. AWS 유료 리소스는 비용과 plan 등 변경 내용을 검토하고 명시적으로 승인한 뒤 생성합니다.

## Phase 1 실행

프로젝트 루트에서 실행합니다. 현재 로컬 폴더명은 `cloud-storage-qa`이며 GitHub 저장소명과 달라도 정상입니다.

```bash
python3.12 -m venv .venv  # 새 환경에서 한 번 실행
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m pip check
python scripts/check_environment.py
```

`requirements.txt`는 PyPI에서 배포 및 지원 Python을 확인한 직접 의존성의 버전을 고정합니다.
공간 확보 후 전체 설치·import·환경 점검을 완료했습니다. 간접 의존성을 포함한 실제 설치 버전은 `requirements.lock.txt`로 기록했습니다.
Linux CI 검증과 보안 취약점 감사는 아직 수행하지 않았습니다.

아직 S3 테스트는 없습니다. `pytest`의 `no tests ran`은 기능 검증 성공을 의미하지 않습니다.
`--target`과 파괴 테스트 실행 차단은 이후 Phase에서 구현합니다.

## 안전한 실습 원칙

실제 자격증명, `.env`, 테스트 reports, Terraform state를 Git에 넣지 않습니다.
공통 테스트는 실행별 고유 bucket과 cleanup fixture를 사용하며, provider 전용/파괴 테스트를 분리합니다.
MinIO 버전과 빌드 가능 여부는 Phase 2에서 공식 upstream을 확인한 뒤 고정합니다.
MinIO는 격리된 실습 환경에서만 사용하고 인터넷에 공개하지 않습니다.
AWS 인증은 기본 SDK 인증 체인, GitHub Actions에서는 OIDC와 최소 권한을 사용합니다.

## 현재 범위

Phase 1의 기본 파일, 원격 연결, 의존성 설치와 개발 환경 점검을 완료했습니다.
첫 커밋과 push는 아래 실습 가이드의 검토 절차에 따라 진행합니다.
MinIO 실행, S3 API 테스트, CI/CD, AWS 리소스 생성 및 Kubernetes 배포는 아직 수행하지 않았습니다.
