# 운영·복구 절차

자동 갱신 파이프라인이 깨졌을 때의 대응 매뉴얼입니다.

## 에러코드 레퍼런스 (사용자 배너)

사용자에게 보이는 배너 우측 하단에는 작은 글씨로 `[ERR-...]` 형태의 코드가 붙습니다. 사용자는 신경 쓸 필요 없고, 이 표를 보고 개발자가 원인을 즉시 특정할 수 있습니다.

| 코드 | 의미 | 사용자 문구 | 상세·대응 |
|---|---|---|---|
| `ERR-STALE-DATA · Nd` | 최신 추첨일이 N일(8일 이상) 지났음. 매주 토요일 추첨이므로 정상은 ≤7일 | "데이터가 N일째 갱신되지 않았어요. 수동 등록으로 입력해 주세요" | 아래 [사례 ①~③](#복구-단계-원인별) 중 하나. Actions 로그와 이슈 확인 |
| `ERR-FETCH-FAILED` | `lotto_cache.json`을 fetch하지 못함. localStorage 저장분으로 임시 구동 | "최신 정보를 불러오지 못해 저장된 데이터로 표시 중이에요" | 호스팅/네트워크/CORS 문제. 배포 경로와 파일 존재 확인 |
| `ERR-NO-DATA` | 공식 파일도 없고, localStorage도 비어 있고, smok95 원본 직접 요청도 실패 | "데이터를 불러올 수 없어요. 잠시 후 다시 시도해 주세요" | 최초 방문자 + 완전 장애. 즉시 조치 필요 |

**정상 상태**: 배너가 뜨지 않음. 서브타이틀에 "최종 추첨 YYYY-MM-DD"가 표시됨.

## 평시

- **매주 일요일 11:00 KST**: GitHub Actions가 `lotto_cache.json`을 자동 갱신합니다.
- 새 커밋은 `github-actions[bot]`이 푸시합니다.
- 사용자는 아무것도 할 필요가 없습니다.

## 이상 신호 감지

### 웹사이트에서
- 상단에 **노란 배너**: "데이터가 N일째 갱신되지 않았습니다" → Actions가 최소 1회 실패
- 상단에 **빨간 배너**: "공식 데이터를 불러오지 못했습니다" → 저장소 파일 자체가 접근 불가

### GitHub에서
- Actions 탭 → "Sync lotto data" 실패 표시 (빨간 X)
- Issues 탭 → "[자동 sync 실패] YYYY-MM-DD" 자동 생성된 이슈

## 복구 단계 (원인별)

### 사례 ①: Actions가 일시적 네트워크 오류로 실패

**증상**: 이슈 본문에 URLError/timeout 흔적, 재시도하면 성공할 가능성 큼.

**대응**:
1. Actions 탭 → 실패한 워크플로우 → "Re-run all jobs"
2. 성공하면 이슈 닫기
3. 반복되면 사례 ②로 진행

### 사례 ②: smok95 원본 스키마 변경

**증상**: 이슈 본문에 `KeyError: 'draw_no'` 또는 검증 실패 메시지.

**대응**:
1. 직접 URL 확인: <https://smok95.github.io/lotto/results/all.json>
2. 필드명이 바뀌었다면 `scripts/sync_lotto.py`의 `normalize()` 함수 수정
   ```python
   def normalize(raw):
       for item in raw:
           # item["draw_no"] → 실제 필드명으로 변경
           ...
   ```
3. 로컬에서 `python scripts/sync_lotto.py --dry-run`으로 검증
4. 커밋 & 푸시 → Actions 자동 재실행 또는 수동 "Run workflow"

### 사례 ③: smok95 저장소가 영구 삭제됨

**증상**: `https://smok95.github.io/lotto/results/all.json`이 404, 저장소 자체가 GitHub에서 삭제됨.

**대응 전략**: 아래 A / B / C 중 하나. 구현 난이도는 **A < C < B**. 속도는 **C(즉시) → A(수 시간) → B(반나절)** 순.

---

#### A. 대체 GitHub 미러로 교체 (권장, 가장 쉬움)

**1단계. 후보 저장소 찾기**

GitHub 검색창에서 아래 키워드로 검색:
- `lotto 645 korea json`
- `로또 당첨번호 크롤러`
- `korea-lotto api`
- `lotto data updated` (최근 커밋이 있는지 확인용)

후보 선별 기준 (모두 충족해야 함):
- [ ] 최근 1개월 이내 커밋이 있음 (= 유지보수되는 저장소)
- [ ] JSON 형식 전체 데이터를 제공 (or 회차별 API 제공)
- [ ] GitHub Pages 또는 raw.githubusercontent.com으로 직접 fetch 가능
- [ ] 1회차부터의 과거 데이터 포함 (신뢰도 검증용)
- [ ] 라이선스가 재사용을 허용 (MIT/Apache/CC-BY 등)

**2단계. 스키마 확인**

후보 URL을 브라우저로 직접 열거나 curl로 받아서 구조 확인:
```bash
curl -s "<후보 URL>" | python -m json.tool | head -40
```

우리가 필요한 최소 필드:
- 회차 번호 (어떤 이름이든)
- 추첨일 (어떤 형식이든)
- 당첨번호 6개
- 보너스 번호

**3단계. `scripts/sync_lotto.py` 수정**

예시: 후보 저장소의 스키마가 `{no, draw_date, picks: [..], bonus}` 라면:

```python
# 기존 (smok95)
GITHUB_ALL_URL = "https://smok95.github.io/lotto/results/all.json"

def normalize(raw):
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
```

```python
# 변경 후 (예: 가상의 대체 미러 owner/lotto-data)
GITHUB_ALL_URL = "https://raw.githubusercontent.com/owner/lotto-data/main/all.json"

def normalize(raw):
    out = []
    for item in raw:
        # ISO 날짜 or 한국형(2025.04.12) 등 입력 형식에 따라 조정
        date_str = item["draw_date"].replace(".", "-").replace("/", "-")
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        out.append({
            "round": int(item["no"]),
            "date": date_str,
            "numbers": sorted(int(n) for n in item["picks"]),
            "bonus": int(item["bonus"]),
        })
    out.sort(key=lambda x: x["round"])
    return out
```

`normalize()`만 바꾸고 `validate()`는 그대로 둡니다 — 검증 규칙은 출처와 무관합니다.

**4단계. 로컬에서 검증**

```bash
# 원본 응답이 기대한 스키마인지 빠르게 확인
python scripts/sync_lotto.py --dry-run
```

성공 시 출력:
```
원본 다운로드: https://...
  원본 1219건 수신
  현재 저장소: 1219회차 / 신규: 1219회차
✅ 변경사항 없음   또는   [dry-run] N회차 신규. 파일 쓰지 않음.
```

**5단계. 크로스체크 (중요)**

대체 소스의 데이터가 **실제 당첨번호와 일치하는지** 반드시 확인. 실수 데이터를 받으면 `validate()`는 통과해도 "틀린 번호"를 커밋하게 됩니다.

```bash
# 기존 lotto_cache.json과 대조: 같은 회차가 똑같은지 샘플링
python - <<'PY'
import json
new = json.load(open("lotto_cache.json.new"))   # dry-run 대신 잠시 저장
old = json.load(open("lotto_cache.json"))
old_map = {d["round"]: d for d in old}
mismatch = 0
for d in new:
    if d["round"] in old_map and d != old_map[d["round"]]:
        print("불일치:", d["round"], d, old_map[d["round"]])
        mismatch += 1
print(f"샘플 점검 완료. 불일치 {mismatch}건")
PY
```

불일치가 0건이어야 안전합니다. 1건이라도 있으면 스키마 매핑을 재검토하세요.

**6단계. 커밋 & 배포**

```bash
git add scripts/sync_lotto.py
git commit -m "fix(sync): smok95 → <대체 저장소> 전환"
git push
```

GitHub Actions 탭 → "Sync lotto data" → "Run workflow"로 수동 실행 → 성공 확인 → 자동 이슈 닫기.

**7단계. 문서 업데이트**

- `scripts/sync_lotto.py` 상단 주석에 새 출처와 전환 사유 기록
- `docs/DATA.md`의 "데이터 출처" 섹션과 `README.md`의 "데이터 출처" 단락을 새 저장소로 갱신

---

#### B. 동행복권 공식 API 직접 사용 (smok95류 미러 없을 때)

동행복권은 회차별 JSON 엔드포인트를 운영합니다.

```
GET https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=N
```

응답 예 (회차 1219):
```json
{
  "returnValue": "success",
  "drwNo": 1219,
  "drwNoDate": "2026-04-12",
  "drwtNo1": 3, "drwtNo2": 11, "drwtNo3": 22,
  "drwtNo4": 28, "drwtNo5": 34, "drwtNo6": 41,
  "bnusNo": 7,
  ...
}
```

이 방식은 전체 데이터를 한 번에 못 받으므로 **증분 방식**으로 바꿔야 합니다.

**구현 스케치** (`scripts/sync_lotto.py`):

```python
DHL_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={n}"

def fetch_one(round_no):
    raw = _open_url(DHL_URL.format(n=round_no)).decode("utf-8")
    d = json.loads(raw)
    if d.get("returnValue") != "success":
        return None   # 해당 회차 아직 추첨 전
    return {
        "round": d["drwNo"],
        "date": d["drwNoDate"],
        "numbers": sorted(d[f"drwtNo{i}"] for i in range(1, 7)),
        "bonus": d["bnusNo"],
    }

def fetch_incremental(current_max):
    new_draws = []
    n = current_max + 1
    while True:
        draw = fetch_one(n)
        if draw is None:
            break
        new_draws.append(draw)
        n += 1
    return new_draws
```

`main()`에서 `fetch_source()` 대신 `fetch_incremental(len(current))`를 호출하고, 기존 리스트에 append. 나머지 validate/save 로직은 동일.

**주의사항**:
- 동행복권 서버에 부담 주지 않도록 회차 사이에 `time.sleep(0.5)` 추가 권장
- 브라우저는 CORS 차단으로 직접 호출 불가 — "📡 지금 동기화" 버튼은 이 방식으로 못 바꿈. 서비스는 Actions가 갱신한 `lotto_cache.json`만 읽게 유지
- `returnValue`가 `"fail"`일 때는 그 회차가 아직 추첨 전이란 뜻 → 정상 종료

---

#### C. 당분간 수동 등록으로 버티기 (즉시 가능, 최후 수단)

A/B 대체 소스를 찾을 시간이 없을 때 임시 대응:
1. 매주 토요일 저녁 추첨 후 [동행복권 공식 페이지](https://www.dhlottery.co.kr/gameResult.do?method=byWin)에서 당첨번호 확인
2. 웹사이트에서 "✏️ 당첨번호 수동 등록" 폼으로 입력
3. "💾 JSON 다운로드" → 받은 `lotto_cache.json`을 저장소에 커밋 & 푸시
4. 매주 반복

장점: 코드 변경 0, 즉시 가능  
단점: 사람이 5분/주 붙잡혀야 함. 장기 해결책 아님 → A나 B로 빠른 전환 권장.

### 사례 ④: Actions 권한 문제로 push 실패

**증상**: 이슈에 `Permission denied` 또는 `403`.

**대응**:
1. 저장소 Settings → Actions → General → "Workflow permissions"
2. "Read and write permissions" 선택 + "Allow GitHub Actions to create and approve pull requests" 체크
3. 실패한 워크플로우 재실행

## 롤백 — 복구 중에 `lotto_cache.json`이 손상됐을 때

대체 소스 교체 도중 잘못된 데이터가 커밋되었다면:

```bash
# 1. 자동 sync 커밋을 찾아 그 직전 커밋 SHA 확인
git log --oneline -- lotto_cache.json | head -10

# 2. 문제 커밋 이전 상태로 되돌리기
git checkout <정상_SHA> -- lotto_cache.json
git commit -m "revert(data): 잘못된 sync 결과 롤백"
git push
```

`lotto_cache.json`은 1회차부터의 전체 스냅샷이라 파일 단위 롤백이 안전합니다 (증분 diff가 아님).

## 수동으로 sync 강제 실행

```
GitHub 저장소 → Actions 탭 → "Sync lotto data" 선택
→ 우측 "Run workflow" 버튼 → "Run workflow" 클릭
```

로컬에서:
```bash
python scripts/sync_lotto.py           # 실제 갱신
python scripts/sync_lotto.py --dry-run # 검증만
```

## 검증 규칙 (sync_lotto.py의 validate 함수)

다음 중 하나라도 틀리면 **파일을 덮지 않고 종료**합니다.

- 데이터가 리스트이고 비어있지 않음
- 각 회차의 `round`는 양의 정수, 중복 없음
- `date`는 `YYYY-MM-DD` 형식
- `numbers`는 길이 6, 각 값 1~45, 중복 없음, 오름차순 정렬
- `bonus`는 1~45, `numbers`와 겹치지 않음
- 전체 배열이 `round` 오름차순 정렬
- 신규 데이터의 최신 회차가 기존보다 작지 않음

## 체크리스트 — 처음 저장소를 포크한 사람에게

- [ ] Settings → Actions → Workflow permissions: Read and write 허용
- [ ] Actions 탭에서 "Sync lotto data" 수동 1회 실행해 정상 작동 확인
- [ ] Settings → Pages: 원하는 브랜치 지정하여 사이트 배포
- [ ] 브라우저로 방문, 서브타이틀에 "최종 추첨 YYYY-MM-DD" 정상 표시 확인
