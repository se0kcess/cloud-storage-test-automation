# Cloud Storage QA Automation Framework

## 목표
AWS 기반 클라우드 스토리지 품질 검증 및 테스트 인프라 자동화 포트폴리오. 기능/API, 인증·인가, 무결성, 장애 복구를 검증하고 CI/CD 품질 게이트를 구축한다. 다양한 클라우드 플랫폼 QA 직무에 적용 가능한 공통 기술 역량을 확보한다.

## 기술 스택 및 설계
- macOS 로컬, Python 3.12, Pytest, Boto3, Requests, pytest-html
- MinIO (격리된 학습용 단일 인스턴스), Docker Compose, named volume
- GitHub Actions: 환경 구축 → health check → smoke/regression/security → report/log artifact → cleanup; 필수 CI 성공 후 merge 및 CD
- AWS 서울 리전(ap-northeast-2)을 기본 후보로 사용하되 계정 정책/비용 확인 후 확정. EC2, VPC/Subnet, Security Group, EBS, ECR, IAM/OIDC, S3, CloudWatch. 배포는 가능한 경우 SSM을 사용하고 MinIO 포트는 공개하지 않는다.
- Terraform으로 반복 가능한 인프라 구축, Kind로 Kubernetes 실습 (Deployment, Service, PVC, probes). EKS 및 Locust는 선택.
- 동일한 공통 테스트를 local, ec2, aws 대상에서 실행하는 사용자 정의 pytest --target 옵션. AWS S3는 기본 SDK 인증 체인, 리전별 bucket 생성 규칙 및 전역 이름 고유성에 대응한다. MinIO는 endpoint 및 path-style 주소 지정. AWS S3에서 컨테이너 장애 주입 금지.

## 목표 디렉터리
```
cloud-storage-qa/
  AGENTS.md
  README.md
  .gitignore
  .env.example
  compose.yaml
  requirements.txt
  pytest.ini
  .github/workflows/{ci.yml,cd.yml}
  clients/s3_client.py
  tests/conftest.py
  tests/common/{test_bucket.py,test_object.py,test_integrity.py}
  tests/minio/{test_auth.py,test_restart.py}
  tests/aws/{test_iam.py,test_s3_policy.py}
  infra/Dockerfile
  infra/kubernetes/{deployment.yaml,service.yaml,pvc.yaml}
  infra/terraform/
  scripts/
  docs/{PROJECT_SPEC.md,requirements.md,test-plan.md,test-cases.md,defect-report.md}
  reports/ (gitignored)
```

## 단계별 구현 계획
1. GitHub 저장소 cloud-storage-qa, git 초기화, Python venv, 기본 구조, README, gitignore, 환경 변수 예시. 기존 저장소 여부 먼저 확인.
2. 검증된 MinIO 릴리스/빌드 방법 선택, Dockerfile, Compose, loopback 9000/9001, health check, volume 영속성 수동 검증.
3. Boto3 CRUD 실습, 요구사항/리스크/테스트 케이스 문서, 공통 client adapter.
4. Pytest fixture, marker, parameterize, 기능·경계·인증·무결성 자동화. 로컬 실행 결과 기록.
5. GitHub Actions CI, HTML/JUnit/log artifacts, 실패 시 cleanup, branch protection/quality gate의 성공과 실패 검증. MVP 완료.
6. AWS 계정/비용/권한 확인, EC2/VPC/SG/EBS 설계 및 승인 후 구축. MinIO는 사설 접근 또는 터널만 허용.
7. ECR 이미지 배포 및 OIDC 기반 CD, CI가 검증한 동일 이미지 digest 사용, 배포 후 smoke, 실패 시 이전 버전 복구 절차.
8. AWS S3 공통 API 검증 및 IAM/정책 검증. 전용 테스트 리소스만 사용. MinIO와 AWS 결과 비교.
9. Terraform 코드화, fmt/validate/plan, 승인 후 apply/destroy. state와 secrets 제외, 잔존 리소스 확인.
10. Kind, PVC, readiness/liveness, Pod 재생성 후 데이터 유지 및 복구 시간 검증. 단일 인스턴스는 HA가 아님.
11. README, 아키텍처, 테스트 결과, 문제 해결 기록, 면접 예상 질문. 선택: Locust 및 CloudWatch 지표.

## 테스트 요구사항 / 후보 케이스
| ID | 검증 | 기대 결과 |
|---|---|---|
| TC-001 | Bucket 생성/조회/삭제 | 정상 상태 전이 |
| TC-002 | 이름 길이 2/3/4/62/63/64 | 유효 범위만 허용; SDK 검증과 서버 검증 구분 |
| TC-003 | Object 업로드/다운로드/삭제 | CRUD 성공 |
| TC-004 | 0B/1B/1KiB/1MiB/10MiB | 데이터 크기와 SHA-256 일치 |
| TC-005 | 존재하지 않는 Object | 권한 조건 충족 시 404/NoSuchKey |
| TC-006 | 비어 있지 않은 Bucket 삭제 | BucketNotEmpty |
| TC-007 | 같은 Key 재업로드 | 버저닝 미활성 조건에서 최신 데이터 반환 |
| TC-008 | 잘못된 Access/Secret Key | 인증 거부; 환경별 오류 코드 확인 |
| TC-009 | 제한 권한 사용자 접근 | 정책상 허용/거부 일치 |
| TC-010 | 컨테이너 재시작/재생성 | 데이터 유지 및 복구 시간 측정 |
| TC-011 | Pod 삭제 후 재생성 | PVC 데이터 유지 및 readiness 회복 |
| TC-012 | CI 의도적 실패 | merge/deploy 차단 및 로그 보존 |
| TC-013 | 동시 요청 및 네트워크 중단 | 정의한 성공/실패 조건, 데이터 무결성 |

## 품질 게이트 및 측정
필수 테스트 100% 통과, 데이터 불일치 및 비인가 성공 0건. 복구 60초는 초기 가설이며 측정 후 확정. 성능 P95 기준은 부하 조건/환경을 정의하고 baseline을 측정한 후 설정. 자동화 실행 시간과 동일 범위 수동 테스트 시간, 요구사항 커버리지, 반복 실행 실패율, 인프라 준비 시간, 실제 결함 증거 기록. 실제 결과 없는 수치 주장 금지.

## 참고 공식 문서
- https://github.com/minio/minio
- https://docs.docker.com/
- https://docs.pytest.org/
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- https://docs.github.com/en/actions
- https://docs.aws.amazon.com/
- https://developer.hashicorp.com/terraform/docs
- https://kind.sigs.k8s.io/docs/user/quick-start/
