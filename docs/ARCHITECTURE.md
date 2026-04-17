# 아키텍처

## 전체 구조

```
┌──────────────────────────────────────────────────────────────┐
│                     데이터 소스 (외부)                          │
│         https://smok95.github.io/lotto/results/all.json       │
│              ↑ 원본: 동행복권 dhlottery.co.kr                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ (최초 1회 또는 수동 동기화)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     lotto_cache.json                          │
│      [ {round, date, numbers[6], bonus}, ... ]  (1회 ~ 최신)   │
└──────────────────────────────────────────────────────────────┘
           ▲                                 ▲
           │                                 │
    ┌──────┴──────┐                  ┌───────┴────────┐
    │  CLI 도구    │                  │   웹사이트       │
    │  (Python)    │                  │   (HTML+JS)     │
    │              │                  │                 │
    │ lotto_       │                  │  index.html     │
    │ predictor.py │                  │  + localStorage │
    └─────────────┘                  └────────────────┘
```

## 두 구현의 공유 자산

**예측 로직은 Python과 JavaScript 양쪽에 똑같이 구현**되어 있습니다. 동일한 5가지 전략, 동일한 통계 지표, 동일한 결과를 내도록 설계되어 있습니다.

| 개념 | Python (lotto_predictor.py) | JavaScript (index.html) |
|---|---|---|
| 캐시 로드 | `load_cache()` | `loadData()` / `fetch("lotto_cache.json")` |
| 통계 분석 | `analyze(data)` | `analyze(data)` |
| 가중치 표본 | `weighted_sample(weights)` | `weightedSample(weights)` |
| 균형 검증 | `is_balanced(nums, stats)` | `isBalanced(nums, stats)` |
| 전략 배열 | `STRATEGIES` | `STRATEGIES` |

→ **하나를 수정했다면 반드시 다른 쪽도 같이 수정**해야 동작이 일치합니다. 수정 시 [docs/STRATEGIES.md](STRATEGIES.md)를 참조하세요.

## 데이터 흐름 (웹)

1. 사용자가 `index.html` 접속
2. `loadData()` 실행:
   - 1순위: `localStorage["lotto_cache"]` — 이전 방문 시 저장된 데이터 (+ 수동 등록분)
   - 2순위: 같은 경로의 `lotto_cache.json` 파일 — 저장소에 커밋된 메인 데이터
   - 3순위: GitHub (`smok95.github.io/lotto/results/all.json`) 폴백
3. `analyze()` → 통계 계산
4. 5개 전략 각각 `fn(stats)` 실행 → 6개 번호 생성
5. DOM에 렌더

사용자가 "최신 데이터 동기화" 버튼을 누르면 `syncFromGithub()`이 실행되어 GitHub 원본을 다시 받고, 기존에 수동 등록한 회차(= GitHub에 없는 회차)는 보존됩니다.

## 데이터 흐름 (CLI)

1. `python lotto_predictor.py` 실행
2. `load_cache()` → `lotto_cache.json` 로드
3. 캐시가 없거나 `--sync` 플래그가 있으면 `sync_data()` 실행 (GitHub에서 받음)
4. `analyze()` → 통계
5. `print_stats()` + `print_predictions()` 터미널 출력

`--sync` 시 `openpyxl`이 설치되어 있으면 Excel 백업 파일(`lotto_backup_{회차}_{날짜}.xlsx`)도 함께 생성됩니다.

## 저장소 파일

```
pick_lucky/
├── index.html              웹사이트 (단일 파일, HTML+CSS+JS)
├── lotto_predictor.py      CLI 도구
├── lotto_cache.json        당첨번호 캐시 (git에 커밋됨)
├── README.md               프로젝트 소개
├── .gitignore              __pycache__, *.pyc, *.xlsx 제외
└── docs/                   상세 문서
    ├── ARCHITECTURE.md     (이 문서)
    ├── WEB.md
    ├── CLI.md
    ├── STRATEGIES.md
    └── DATA.md
```

## 배포

- **웹**: GitHub Pages 등 정적 호스팅에 `index.html` + `lotto_cache.json`을 함께 올리면 끝. 빌드 단계 없음.
- **CLI**: 별도 배포 불필요. Python 3 + (선택) `openpyxl`, `certifi`만 있으면 실행됨.

## 의존성

### Python (선택 사항)
- `openpyxl` — Excel 백업 생성/읽기. 없으면 해당 기능만 건너뜀.
- `certifi` — Windows Python에서 SSL 인증서 검증용. 없으면 검증 비활성화 fallback.

### JavaScript
없음. 순수 vanilla JS + `fetch` + `localStorage`.
