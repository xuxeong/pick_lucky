# CLI 도구 (lotto_predictor.py) 상세

터미널에서 실행하는 Python 스크립트입니다. `index.html`과 동일한 예측 로직을 제공하며, 추가로 Excel 백업 기능을 갖습니다.

## 실행 방법

```bash
# 기본 실행 (캐시 있으면 캐시 사용, 없으면 최초 동기화)
python lotto_predictor.py

# 강제로 최신 데이터 동기화 후 예측
python lotto_predictor.py --sync

# 오프라인 강제 (네트워크 안 씀)
python lotto_predictor.py --offline

# Excel 파일에서 캐시 가져오기 (과거 수집 데이터 이관용)
python lotto_predictor.py import <경로.xlsx>
```

## 의존성

| 패키지 | 필수 | 용도 |
|---|---|---|
| Python 3.x | ✅ | 실행 환경 (표준 라이브러리만 사용) |
| `openpyxl` | ❌ | Excel 백업 생성 / Excel → 캐시 변환. 없으면 해당 기능만 건너뜀 |
| `certifi` | ❌ | Windows Python SSL 인증서 fallback. 없으면 검증 비활성화 |

```bash
pip install openpyxl certifi
```

## 파일 상단 상수

```python
CACHE_FILE = "lotto_cache.json"                              # 캐시 경로 (스크립트와 같은 폴더)
RECENT_WINDOW = 50                                            # 최근 트렌드 분석 범위
GITHUB_ALL_URL = "https://smok95.github.io/lotto/results/all.json"  # 데이터 소스
BALL_COLORS = [...]                                           # Excel 출력용 공 색상
```

## 함수 명세

### 캐시 I/O

| 함수 | 역할 |
|---|---|
| `load_cache()` | `lotto_cache.json` 읽어 list 반환. 파일 없으면 `[]` |
| `save_cache(data)` | data를 JSON으로 저장 (UTF-8, indent=2) |
| `import_from_excel(xlsx_path)` | Excel 파일을 읽어 캐시 형식으로 변환하고 저장 |

### 데이터 동기화

| 함수 | 역할 |
|---|---|
| `sync_data()` | `GITHUB_ALL_URL`에서 전체 데이터 다운로드 → 내부 형식 변환 → 저장 → Excel 백업 |

GitHub 원본의 필드(`draw_no`, `bonus_no`, `date`(ISO))를 내부 필드(`round`, `bonus`, `date`(YYYY-MM-DD))로 매핑합니다. 다운로드 실패 시 기존 캐시로 fallback 합니다.

### Excel 출력

| 함수 | 역할 |
|---|---|
| `ball_color(n)` | 번호 → hex 색상 (웹과 동일한 규칙) |
| `export_excel(data, filename=None)` | 2개 시트 Excel 파일 생성 (`당첨번호`, `번호별통계`). 파일명 미지정 시 `lotto_backup_{회차}_{날짜}.xlsx` |

Excel 시트 1 (`당첨번호`): 회차 · 추첨일 · 번호1~6 · 보너스 (공 색상 배경). 1행 헤더 고정, 자동 필터 활성.
Excel 시트 2 (`번호별통계`): 번호 · 출현횟수 · 보너스출현.

### 통계 분석

| 함수 | 역할 |
|---|---|
| `analyze(data)` | 웹의 `analyze()`와 동일한 통계 dict 반환 |

반환 키:
- `total` — 총 회차 수
- `latest_round` — 가장 최근 회차 번호
- `freq_all: Counter` — 전체 번호별 출현 횟수
- `freq_recent: Counter` — 최근 `RECENT_WINDOW`회 번호별 출현 횟수
- `pair_count: dict[(a,b) → int]` — 쌍 동반 출현 횟수
- `gap: dict[n → int]` — 번호 n이 마지막으로 나온 이후 경과 회차
- `avg_sum` / `sum_min` / `sum_max` — 합계 평균과 권장 범위 (평균 ± 35)
- `odd_mode` — 홀수 개수의 최빈값
- `range_dist: Counter` — 10단위 구간별 출현 횟수

### 예측 전략

| 함수 | 역할 |
|---|---|
| `weighted_sample(weights)` | 가중치 dict에서 중복 없이 6개 뽑음 |
| `is_balanced(nums, stats)` | 합계/홀짝/구간편중/연속번호 제약 검사 |
| `strategy_frequency(stats)` | 전체 빈도 가중 |
| `strategy_recent(stats)` | 최근 트렌드 가중 |
| `strategy_cold(stats)` | 갭(미출현 기간) 가중 |
| `strategy_pair(stats)` | 상위 쌍을 씨앗으로, 함께 나온 번호로 채움 |
| `strategy_balanced(stats)` | 빈도 가중 + `is_balanced` 제약을 만족할 때까지 최대 500회 재시도 |
| `STRATEGIES` | `(이름, 함수)` 튜플 리스트 |

수학적 설명은 [STRATEGIES.md](STRATEGIES.md) 참조.

### 출력

| 함수 | 역할 |
|---|---|
| `print_stats(stats)` | 통계 요약을 터미널 출력 (이모지 포함) |
| `format_numbers(nums)` | 번호 리스트를 정렬된 문자열로 |
| `print_predictions(stats, sets_per_strategy=1)` | 5개 전략 각각 `sets_per_strategy`세트 출력 |

### 진입점

| 함수 | 역할 |
|---|---|
| `main()` | CLI 인자 파싱 + 전체 흐름 |

## 실행 분기 (main)

```
python lotto_predictor.py import <file>  →  import_from_excel(), 종료
python lotto_predictor.py --offline      →  캐시만 사용
python lotto_predictor.py --sync         →  sync_data() 후 예측
python lotto_predictor.py                →  캐시 있으면 사용, 없으면 sync_data()
```

## SSL 처리

```python
try:
    _ssl_ctx = ssl.create_default_context()
    import certifi
    _ssl_ctx.load_verify_locations(certifi.where())
except Exception:
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
```

Windows Python에서 시스템 인증서를 못 찾을 때를 대비해 `certifi` 번들을 먼저 시도하고, 실패하면 검증을 끕니다. 보안이 중요한 환경이라면 `certifi` 설치를 권장합니다.

## 흔한 수정 사례

### 추천 세트 수 늘리기
`print_predictions(stats, sets_per_strategy=5)`로 바꾸면 전략당 5세트씩 출력.

### 최근 트렌드 범위 바꾸기
`RECENT_WINDOW` 상수 변경. **웹의 `RECENT_WINDOW`도 같이 바꿔야** 두 결과가 일치합니다.

### Excel 백업 끄기
`sync_data()` 마지막의 `export_excel(cache)` 호출을 제거하거나, 조건을 추가.

### 다른 데이터 소스 쓰기
`GITHUB_ALL_URL`과 `sync_data()` 내부의 필드 매핑(`draw_no`/`bonus_no`/`date`) 부분을 바꾸면 됩니다.

### 새 전략 추가
1. `strategy_*(stats) → list[6 ints]` 함수 추가
2. `STRATEGIES` 리스트에 `("이름", 함수)` 추가
3. `index.html`의 `STRATEGIES`에 대응 추가
4. [STRATEGIES.md](STRATEGIES.md)에 설명 추가

## 출력 예시

```
🎱 한국 로또 6/45 예측기

📂 캐시에서 1219회차 로드 (최신 동기화: python lotto_predictor.py --sync)

📊 통계 요약
   분석 대상: 1회 ~ 1219회 (1219회차)
   평균 합계: 138.3  (권장 범위 103~173)
   최빈 홀수개수: 3개
   🔥 핫넘버 TOP6: [34, 27, 18, 13, 1, 17]
   🧊 오래된 번호 TOP6: [22, 9, 6, ...] (각각 N회차 미출현)
   📈 최근 50회 핫: [...]

🎯 1220회차 추천 번호
=======================================================
  [전체빈도 가중    ]  3  13  18  27  34  41   합:136 홀:3
  [최근트렌드 가중  ]  ...
  ...
=======================================================
⚠️  로또는 독립 시행입니다. 재미로만 활용하세요.
```
