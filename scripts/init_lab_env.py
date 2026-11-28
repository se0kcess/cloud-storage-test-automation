"""로컬 실습 전용 비밀값을 생성한다. 기존 .env는 덮어쓰지 않는다."""

import os
import secrets
from pathlib import Path

path = Path(__file__).resolve().parents[1] / ".env"
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    print("기존 .env 유지. 값은 출력하지 않습니다.")
else:
    with os.fdopen(fd, "w") as stream:
        stream.write(
            f"MINIO_ROOT_USER=lab-{secrets.token_hex(8)}\n"
            f"MINIO_ROOT_PASSWORD={secrets.token_urlsafe(32)}\n"
            "S3_ENDPOINT_URL=http://127.0.0.1:9000\n"
            "AWS_DEFAULT_REGION=ap-northeast-2\n"
        )
    print("실습용 .env 생성 완료 (0600). 비밀값은 출력하지 않습니다.")
