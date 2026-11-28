# Phase 2 — 실제 실행 결과

실행일: 2026-11-28 (Asia/Seoul).

## 검증 환경과 빌드

- 호스트: macOS arm64, Python 3.12.1.
- Docker Desktop 4.14.1 / Engine 20.10.21 / Compose v2.12.2.
- Docker VM: CPU 4개, 메모리 약 8GB. 시작 시 호스트 여유 공간 약 6.3GiB.
- MinIO: `RELEASE.2025-10-15T17-29-55Z`, 커밋 `9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a`.
- 소스 tar SHA-256과 builder/runtime manifest digest 검증 후 빌드 성공. 정확한 고정값은 `infra/Dockerfile` 참조.
- 실행 바이너리: `minio --version`에서 위 릴리스와 커밋, `go1.24.8 linux/arm64` 확인.
- 이미지 ID: `sha256:2e7a15b19174e97b7af700b5addc1d793b40dbe493b8fd94f22d5490177da584`.
- 이미지 크기: 113,797,907 bytes. Go build 단계는 141.7초였으며 전체 빌드 시간은 별도 측정하지 않았다.
- 이미지 ID는 이번 로컬 산출물 식별자다. 원격 레지스트리에 게시한 RepoDigest나 다른 환경에서의 재현 빌드 일치를 의미하지 않는다.

## 실제 확인 결과

| 항목 | 실제 결과 |
|---|---|
| `docker compose config --quiet` | 종료 코드 0 |
| 기존 .env 보존 | 생성 스크립트 재실행 전후 파일 해시 동일 |
| .env 파일 권한 | 0600 |
| 빈 자격증명 거부 | 환경변수를 빈 값으로 override한 config 검증이 비정상 종료됨 |
| Python 구문 검사 | 신규 스크립트 ast.parse 성공 |
| 비 root 실행 | `10001:10001` |
| Docker health | healthy |
| 호스트 API 경로 | `/minio/health/ready` HTTP 200 |
| 콘솔 경로 | `http://127.0.0.1:9001` HTTP 200; 로그인 기능은 미검증 |
| 실제 포트 매핑 | 9000/tcp와 9001/tcp 모두 HostIp 127.0.0.1 |
| 데이터 mount | named volume `cloud-storage-qa-lab_minio-data` → `/data` |
| 최초 업로드/다운로드 | 고유 실습 bucket의 1KiB 파일, 크기와 SHA-256 일치 |

## 재시작과 재생성 실험

한 개의 고유 bucket/object로 아래 실험을 순서대로 한 번씩 수행했다.
각 작업 전후 container ID와 volume 이름을 확인하고 준비 대기 후 파일을 내려받았다.

| 작업 | container ID | volume 이름 | 파일 크기 / SHA-256 | 명령 시작 → ready |
|---|---|---|---|---|
| `docker compose restart minio` | 동일 | 동일 | 1024B / 일치 | 1.62초 |
| `up -d --force-recreate minio` | 변경 | 동일 | 1024B / 일치 | 1.45초 |
| `down` 후 `up -d minio` | 변경 | 동일 | 1024B / 일치 | 1.67초 |

측정은 Python monotonic clock으로 명령 시작부터 ready probe 종료까지 수행했다.
0.5초 polling, subprocess 실행과 요청 지연이 포함된다. 각 데이터 무결성 검증은 ready 확인 후 별도로 수행했다.
이 값은 단일 실행 관측값이며 P95/SLA/반복 안정성이나 전체 서비스 복구 시간의 보장이 아니다.
원본 단계별 결과는 Git 제외 경로 `reports/phase02-execution.json`에 보존했다.

## 발견한 실행 환경 이슈

### 내부 health는 성공했지만 호스트 API는 연결 거부

첫 구성은 `internal: true` 네트워크를 사용했다. 이 환경에서 컨테이너 health는 healthy였지만,
`.NetworkSettings.Ports`는 비어 있었고 호스트의 127.0.0.1:9000 요청은 ConnectionRefused로 실패했다.
`.HostConfig.PortBindings`에는 요청한 loopback 매핑이 있어 설정만 확인해서는 문제를 발견할 수 없었다.

전용 bridge 네트워크로 변경하고 실습 컨테이너/네트워크를 다시 만든 뒤 실제 포트 매핑과 HTTP 200을 확인했다.
volume은 삭제하지 않았다. 이 결과는 현재 Docker Desktop/Engine 조합에서 재현한 현상이며 다른 버전 전체의 동작으로 일반화하지 않는다.

### 구버전 manifest 조회 제한

Docker CLI 20.10의 manifest inspect는 OCI manifest media type 오류를 반환했다.
공식 Docker Registry API로 manifest digest와 arm64 지원을 확인했고, 같은 digest를 사용한 실제 build는 성공했다.

## 요구사항 연결과 검증 한계

- **TC-010 일부:** 컨테이너 재시작/재생성 후 데이터 유지와 command-to-ready 관측 완료.
- **TC-004 일부:** 1KiB 파일 한 개의 크기와 SHA-256 비교만 완료. 0B~10MiB 전체 범위 미검증.
- 인증된 업로드/다운로드는 수행했으나 root 계정을 사용한 로컬 실습이다. 제한 사용자·잘못된 키·IAM 정책은 미검증.
- 비정상 종료, 호스트/디스크 손실, volume 삭제, 동시 요청, 장기 보존, HA, 성능과 Linux CI는 미검증.
- 소스·이미지 고정과 보안 취약점 감사는 별개다. 이번 단계에서 취약점 감사는 수행하지 않았다.
- upstream은 아카이브 상태다. 운영 환경이나 인터넷 공개 서비스에 사용하지 않는다.
- Docker 공식 문서는 28.0.0 이전 localhost 게시 포트의 같은 L2 네트워크 접근 가능성을 경고한다. 현재 20.10 환경의 LAN 격리는 검증하지 않았다. 업데이트 없이 신뢰할 수 없는 네트워크에 노출하지 않는다.

## 정리 후 상태

probe가 생성한 단일 object와 bucket만 `cleanup`으로 삭제했다. 다른 object가 있으면 bucket 삭제가 실패하도록 설계했다.
최종 health/console 응답과 healthy 상태를 확인한 뒤 `docker compose down`으로 서버와 실습 네트워크를 중지·제거했다.
`cloud-storage-qa-lab_minio-data` volume 존재를 다시 확인했다. 이미지와 build cache는 보존했다.
현재 서버는 실행 중이 아니며 다음 실습 때 `docker compose up -d minio`로 다시 시작할 수 있다.
AWS 리소스 생성, Git 커밋과 원격 push는 수행하지 않았다. 기존 phase-01-evidence.md 제외 정책은 유지했다.

## 근거 및 재실행

- [실습 가이드와 전체 명령](phase-02-minio.md)
- [선택한 공식 MinIO 릴리스](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z)
- [MinIO 저장소 아카이브 상태](https://github.com/minio/minio)
- [Docker 게시 포트의 버전별 제약](https://docs.docker.com/engine/network/port-publishing/)
