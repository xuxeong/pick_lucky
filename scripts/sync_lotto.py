"""
smok95/lotto 원본에서 전체 데이터를 받아 검증한 뒤 lotto_cache.json을 갱신한다.

- 검증 실패 시 기존 파일을 덮지 않고 비정상 종료 (Actions 실패 → 이슈 자동 생성)
- 신규 회차가 없으면 변경사항 없음으로 정상 종료
- GitHub Actions 및 로컬에서 동일하게 실행 가능

사용:
    python scripts/sync_lotto.py              # 갱신 (커밋은 워크플로우가 담당)
    python scripts/sync_lotto.py --dry-run    # 검증만, 파일 쓰지 않음
"""

import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime

GITHUB_ALL_URL = "https://smok95.github.io/lotto/results/all.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(ROOT, "lotto_cache.json")


def _open_url(url):
    # Actions(Ubuntu)는 시스템 인증서로 성공. Windows 로컬은 certifi → CERT_NONE 순 fallback.
    req = urllib.request.Request(url, headers={"User-Agent": "pick-lucky-sync"})

    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except ImportError:
        pass

    try:
        return urllib.request.urlopen(req, timeout=30, context=ctx).read()
    except urllib.error.URLError as e:
        if not isinstance(e.reason, ssl.SSLError):
            raise
        # SSL 검증 실패 시 비검증 모드로 재시도 (Windows 로컬 전용 경로)
        print("  ⚠️  SSL 검증 실패 → 비검증 모드로 재시도 (로컬 환경 가정)")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=30, context=ctx).read()


def fetch_source():
    raw = _open_url(GITHUB_ALL_URL).decode("utf-8")
    return json.loads(raw)


def normalize(raw):
    """원본 스키마 → 내부 스키마. 필드명이 바뀌면 여기서 바로 KeyError."""
    out = []
    for item in raw:
        date_str = item["date"]
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        out.append({
            "round": int(item["draw_no"]),
            "date": date_str,
            "numbers": sorted(int(n) for n in item["numbers"]),
            "bonus": int(item["bonus_no"]),
        })
    out.sort(key=lambda x: x["round"])
    return out


def validate(data):
    """스키마·값 범위·연속성 검증. 실패 시 ValueError."""
    if not isinstance(data, list) or not data:
        raise ValueError("데이터가 비어 있거나 리스트가 아닙니다")

    seen_rounds = set()
    for d in data:
        r = d["round"]
        if not (isinstance(r, int) and r >= 1):
            raise ValueError(f"회차가 올바르지 않습니다: {d}")
        if r in seen_rounds:
            raise ValueError(f"중복 회차: {r}")
        seen_rounds.add(r)

        try:
            datetime.strptime(d["date"], "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜 형식이 YYYY-MM-DD가 아닙니다: {d}")

        nums = d["numbers"]
        if len(nums) != 6:
            raise ValueError(f"번호 개수가 6이 아닙니다: {d}")
        if any(not (1 <= n <= 45) for n in nums):
            raise ValueError(f"번호 범위(1~45) 벗어남: {d}")
        if len(set(nums)) != 6:
            raise ValueError(f"번호 중복: {d}")
        if nums != sorted(nums):
            raise ValueError(f"번호 정렬 안 됨: {d}")

        b = d["bonus"]
        if not (1 <= b <= 45):
            raise ValueError(f"보너스 범위(1~45) 벗어남: {d}")
        if b in nums:
            raise ValueError(f"보너스가 본번호와 겹침: {d}")

    rounds = [d["round"] for d in data]
    if rounds != sorted(rounds):
        raise ValueError("회차가 오름차순이 아닙니다")


def load_current():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"원본 다운로드: {GITHUB_ALL_URL}")
    raw = fetch_source()
    print(f"  원본 {len(raw)}건 수신")

    try:
        new_data = normalize(raw)
    except (KeyError, TypeError, ValueError) as e:
        print(f"❌ 스키마 파싱 실패(원본 필드 변경 의심): {e}")
        sys.exit(2)

    try:
        validate(new_data)
    except ValueError as e:
        print(f"❌ 검증 실패: {e}")
        sys.exit(2)

    current = load_current()
    current_latest = current[-1]["round"] if current else 0
    new_latest = new_data[-1]["round"]

    print(f"  현재 저장소: {current_latest}회차 / 신규: {new_latest}회차")

    if new_latest < current_latest:
        print(f"❌ 원본이 저장소보다 회차가 적습니다. 덮어쓰기 거부.")
        sys.exit(2)

    if new_latest == current_latest and new_data == current:
        print("✅ 변경사항 없음")
        return

    if dry_run:
        print(f"[dry-run] {new_latest - current_latest}회차 신규. 파일 쓰지 않음.")
        return

    save(new_data)
    added = new_latest - current_latest
    print(f"✅ 갱신 완료: +{added}회차 (최신 {new_latest}회차, {new_data[-1]['date']})")


if __name__ == "__main__":
    main()
