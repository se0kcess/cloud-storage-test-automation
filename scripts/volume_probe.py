"""Phase 2 전용 1KiB 영속성 실습. 공통 테스트 프레임워크는 Phase 3~4에서 구현."""

import argparse
import hashlib
import json
import os
import time
import uuid
from pathlib import Path

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "reports" / "phase02-persistence.json"
ENDPOINT = "http://127.0.0.1:9000"  # AWS/외부 서버로 변경할 수 없게 고정


def wait_ready():
    start = time.monotonic()
    while time.monotonic() - start < 60:
        try:
            if requests.get(f"{ENDPOINT}/minio/health/ready", timeout=2).status_code == 200:
                print(f"READY: 대기 {time.monotonic() - start:.2f}초")
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise RuntimeError("60초 안에 ready 상태가 되지 않았습니다.")


def client():
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    # Compose와 동일하게 프로세스 환경변수를 우선한다. AWS 기본 키는 사용하지 않는다.
    user = os.environ.get("MINIO_ROOT_USER", values.get("MINIO_ROOT_USER"))
    password = os.environ.get("MINIO_ROOT_PASSWORD", values.get("MINIO_ROOT_PASSWORD"))
    if not user or not password:
        raise RuntimeError("실습용 MinIO 자격증명이 없습니다.")
    return boto3.client(
        "s3", endpoint_url=ENDPOINT, aws_access_key_id=user,
        aws_secret_access_key=password, region_name="ap-northeast-2",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                      connect_timeout=3, read_timeout=5, retries={"max_attempts": 0}),
    )


def run(action):
    if action == "wait":
        wait_ready()
        return
    s3 = client()
    if action == "seed":
        if STATE.exists():
            raise RuntimeError("기존 실습 기록이 있습니다. verify 또는 cleanup 후 다시 실행하세요.")
        data = os.urandom(1024)
        state = {"bucket": f"phase02-{uuid.uuid4().hex}", "key": "persistence.bin",
                 "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        STATE.parent.mkdir(exist_ok=True)
        s3.create_bucket(Bucket=state["bucket"])
        # 업로드 실패 시에도 cleanup할 수 있도록 bucket 생성 직후 기록한다.
        STATE.write_text(json.dumps(state, indent=2) + "\n")
        s3.put_object(Bucket=state["bucket"], Key=state["key"], Body=data)
        print(f"SEEDED: {state['bucket']} / {state['size']}B")
        return
    state = json.loads(STATE.read_text())
    if not state["bucket"].startswith("phase02-") or state["key"] != "persistence.bin":
        raise RuntimeError("Phase 2 실습 기록이 아닙니다. 작업을 거부합니다.")
    if action == "cleanup":
        # 실습에서 만든 단일 key와 bucket만 삭제. 다른 object가 있으면 bucket 삭제 실패.
        s3.delete_object(Bucket=state["bucket"], Key=state["key"])
        s3.delete_bucket(Bucket=state["bucket"])
        STATE.unlink()
        print("CLEANED: 이번 영속성 실습 bucket/object만 정리했습니다.")
        return
    response = s3.get_object(Bucket=state["bucket"], Key=state["key"])
    with response["Body"] as body:
        data = body.read()
    if len(data) != state["size"] or hashlib.sha256(data).hexdigest() != state["sha256"]:
        raise RuntimeError("데이터 크기 또는 SHA-256 불일치")
    print(f"VERIFIED: {len(data)}B / SHA-256 일치")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["wait", "seed", "verify", "cleanup"])
    args = parser.parse_args()
    try:
        run(args.action)
    except ClientError as exc:
        parser.exit(1, f"FAIL: S3 오류 {exc.response['Error']['Code']}\n")
    except (BotoCoreError, OSError, ValueError, KeyError, RuntimeError) as exc:
        # SDK 예외나 환경값을 그대로 출력하지 않는다.
        parser.exit(1, f"FAIL: {type(exc).__name__}; 설정/서버/실습 기록을 확인하세요.\n")
