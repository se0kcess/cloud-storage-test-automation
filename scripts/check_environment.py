"""네트워크 및 AWS 접근 없이 Python 실행 환경만 검증한다."""

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def main() -> int:
    failures = []
    print(f"Python: {sys.version.split()[0]}")
    if sys.version_info[:2] != (3, 12):
        failures.append("Python 3.12가 필요합니다.")
    if sys.prefix == sys.base_prefix:
        failures.append("가상환경 Python으로 실행하세요.")
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    if not requirements.exists():
        failures.append("requirements.txt 생성 및 의존성 설치가 필요합니다.")
    else:
        for line in requirements.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            package, expected = line.split("==", 1)
            try:
                actual = version(package)
            except PackageNotFoundError:
                failures.append(f"{package}: 미설치")
                continue
            print(f"{package}: {actual}")
            if actual != expected:
                failures.append(f"{package}: 고정 버전 {expected}와 다릅니다.")
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print("PASS: 개발 환경 확인 완료 (S3 API 테스트는 실행하지 않음)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
