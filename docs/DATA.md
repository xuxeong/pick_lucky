# 데이터 스키마와 수집 흐름

## 데이터 출처

**원본**: [동행복권](https://www.dhlottery.co.kr/) — 한국 로또 6/45 공식 추첨 결과  
**중간 미러**: [smok95/lotto](https://github.com/smok95/lotto) — GitHub 저장소에서 자동 수집 및 공개  
**실제 다운로드 URL**: `https://smok95.github.io/lotto/results/all.json`

이 프로젝트는 매번 동행복권 API에 직접 요청하지 않고, GitHub Pages에 호스팅된 전체 회차 JSON을 한 번에 받아옵니다. 안정적이고 CORS도 허용되어 있어 브라우저에서 직접 fetch 가능.

## 캐시 파일 스키마 (`lotto_cache.json`)

프로젝트 내부 표준 형식. 웹과 CLI가 공유합니다.

```json
[
  {
    "round": 1,
    "date": "2002-12-07",
    "numbers": [10, 23, 29, 33, 37, 40],
    "bonus": 16
  },
  {
    "round": 2,
    "date": "2002-12-14",
    "numbers": [9, 13, 21, 25, 32, 42],
    "bonus": 2
  }
  // ... 최신 회차까지 오름차순 정렬
]
```

### 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `round` | integer | 회차 번호 (1부터 시작, 단조 증가) |
| `date` | string | 추첨일 `YYYY-MM-DD` |
| `numbers` | int[6] | 당첨번호 6개, **오름차순 정렬** |
| `bonus` | integer | 보너스 번호 (1~45) |

### 불변 조건

- 배열은 `round` 오름차순 정렬
- `round` 값은 중복 없음
- `numbers`는 길이 6, 각 원소 1~45, 중복 없음, 정렬됨
- `numbers`와 `bonus`는 값이 겹치지 않음

## GitHub 원본 형식

`GITHUB_ALL_URL`에서 받는 원본의 필드명은 다릅니다.

```json
[
  {
    "draw_no": 1,
    "date": "2002-12-07T00:00:00",
    "numbers": [10, 23, 29, 33, 37, 40],
    "bonus_no": 16
  }
]
```

변환 규칙 (Python `sync_data()` / JS `normalizeData()` 공통):

| 원본 (GitHub) | 내부 (캐시) |
|---|---|
| `draw_no` | `round` |
| `bonus_no` | `bonus` |
| `date` (ISO 8601, `T`포함) | `date` (`T` 앞부분만, = YYYY-MM-DD) |
| `numbers` | `numbers` (그대로, 단 정렬 보정) |

## 데이터 흐름

### 웹 (index.html)

```
[브라우저 로드]
      ↓
loadData()
      ↓
1. localStorage["lotto_cache"] 있는가?
   YES → lottoData에 로드 → 끝
   NO  → 2로
      ↓
2. fetch("lotto_cache.json") 성공?
   YES → normalizeData → localStorage 저장 → 끝
   NO  → 3으로
      ↓
3. fetch(GITHUB_ALL_URL)  (폴백)
      ↓
   normalizeData → localStorage 저장 → 끝
```

사용자가 "📡 최신 데이터 동기화" 버튼을 누르면 `syncFromGithub()`가 실행되어 **GitHub를 강제로 다시 받습니다**. 이때 **사용자가 수동 등록한 회차(= GitHub에 없는 회차)는 보존**됩니다.

### CLI (lotto_predictor.py)

```
[python lotto_predictor.py]
      ↓
load_cache() → lotto_cache.json
      ↓
캐시 있고 --sync 없음 → 캐시 그대로 사용
캐시 없음 또는 --sync   → sync_data() 호출
                         ↓
                      GitHub 다운로드 → 변환 → save_cache() → export_excel()
      ↓
analyze() → print_stats() → print_predictions()
```

## 수동 등록

웹에서 "✏️ 당첨번호 수동 등록" 폼으로 새 회차를 추가할 수 있습니다.

```javascript
lottoData.push({ round, date, numbers: [정렬됨], bonus });
lottoData.sort((a, b) => a.round - b.round);
localStorage.setItem("lotto_cache", JSON.stringify(lottoData));
```

중복 회차는 `addDraw()`에서 거부됩니다.

### 저장소에 영구 반영하는 방법

localStorage는 브라우저에만 있으므로, 다른 기기나 배포본에 반영하려면:

1. "💾 JSON 다운로드" 버튼으로 `lotto_cache.json` 파일 내려받기
2. 저장소의 `lotto_cache.json`을 받은 파일로 교체
3. git commit & push

## Excel 백업

`python lotto_predictor.py --sync` 실행 시, `openpyxl`이 있으면 `lotto_backup_{회차}_{날짜}.xlsx`가 자동 생성됩니다 (스크립트와 같은 폴더).

Excel은 `.gitignore`에 포함되어 있어 git에는 커밋되지 않습니다.

Excel → 캐시 역변환:
```bash
python lotto_predictor.py import lotto_backup_1219회_20250412.xlsx
```
→ Excel의 `당첨번호` 시트 또는 첫 시트를 읽어 `lotto_cache.json`을 덮어씁니다.

## 데이터 크기 감각

2026-04 기준, 약 1200+ 회차 × 1회차당 60~70바이트 → **약 200KB** 정도의 JSON. localStorage 5MB 한도에 비해 작으므로 걱정 없음.
