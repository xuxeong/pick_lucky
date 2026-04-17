# 아키텍처

## 핵심 원칙

**저장소의 `lotto_cache.json`이 절대 기준**입니다. 사이트는 이 파일을 방문 시마다 재확인하고, GitHub Actions가 매주 자동으로 이 파일을 갱신합니다. 수동 등록·수동 동기화 버튼은 자동화가 깨졌을 때를 위한 **비상용 2차 수단**입니다.

## 전체 구조

```
┌──────────────────────────────────────────────────────────────┐
│              외부 원본 (smok95 — 동행복권 미러)                  │
│         https://smok95.github.io/lotto/results/all.json       │
└───────────────────────────┬──────────────────────────────────┘
                            │ 매주 일요일 11:00 KST
                            ▼
┌──────────────────────────────────────────────────────────────┐
│          GitHub Actions: sync-lotto.yml                       │
│          scripts/sync_lotto.py → 검증 → 커밋                    │
│          (검증 실패 시 이슈 자동 생성, 파일 덮지 않음)              │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│          lotto_cache.json  (절대 기준, git 커밋됨)              │
│      [ {round, date, numbers[6], bonus}, ... ]  (1회 ~ 최신)   │
└───────────────────────────┬──────────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
    ┌──────────┐    ┌──────────────┐  ┌──────────────┐
    │ CLI 도구  │    │ 웹사이트       │  │ 사용자 수동   │
    │ (Python) │    │ (HTML+JS)    │  │ 등록 (비상용) │
    │          │    │ + localStorage│  │              │
    └──────────┘    └──────────────┘  └──────────────┘
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
   - **1순위**: `fetch("lotto_cache.json", { cache: "no-cache" })` — 저장소의 공식 파일. 방문 시마다 재확인
   - **2순위**: `localStorage["lotto_cache"]` — 공식 파일을 못 받았을 때만 임시 구동
   - **3순위** (최후): `syncFromGithub()` — smok95 원본 직접 요청
3. 공식 파일이 있으면 `mergeOfficialWithManual()`로 localStorage의 수동 등록분 합침
   - **머지 정책: 공식이 이긴다.** 같은 회차 값이 다르면 공식으로 덮되 콘솔 경고. 공식에 없는 회차만 localStorage 것을 살림.
4. `analyze()` → 통계 계산 → 5개 전략 → DOM 렌더
5. 최신 추첨일이 8일 이상 지났으면 `renderStaleBanner()`가 경고 배너 표시

"📡 최신 데이터 동기화" 버튼은 `syncFromGithub()`를 호출해 smok95 원본을 직접 받습니다. 자동 갱신이 멈췄을 때 현 브라우저만 즉시 최신화하는 비상 수단입니다.

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
├── index.html                      웹사이트 (단일 파일, HTML+CSS+JS)
├── lotto_predictor.py              CLI 도구
├── lotto_cache.json                당첨번호 캐시 (git에 커밋됨, 절대 기준)
├── README.md                       프로젝트 소개
├── .gitignore                      __pycache__, *.pyc, *.xlsx 제외
├── scripts/
│   └── sync_lotto.py               smok95 → 검증 → lotto_cache.json 갱신
├── .github/workflows/
│   └── sync-lotto.yml              매주 일요일 자동 sync (검증·커밋·실패 알림)
└── docs/                           상세 문서
    ├── ARCHITECTURE.md             (이 문서)
    ├── WEB.md
    ├── CLI.md
    ├── STRATEGIES.md
    ├── DATA.md
    └── OPERATIONS.md               운영·복구 절차
```

## 배포

- **웹**: GitHub Pages 등 정적 호스팅에 `index.html` + `lotto_cache.json`을 함께 올리면 끝. 빌드 단계 없음. Actions가 `lotto_cache.json`을 주기적으로 갱신하므로 배포 후 사람 손이 닿지 않아도 자동으로 최신을 유지합니다.
- **CLI**: 별도 배포 불필요. Python 3 + (선택) `openpyxl`, `certifi`만 있으면 실행됨.
- **Actions**: `.github/workflows/sync-lotto.yml`이 `contents: write`, `issues: write` 권한으로 동작. 저장소 Settings → Actions → "Workflow permissions"에서 read/write 허용 필요.

## 의존성

### Python (선택 사항)
- `openpyxl` — Excel 백업 생성/읽기. 없으면 해당 기능만 건너뜀.
- `certifi` — Windows Python에서 SSL 인증서 검증용. 없으면 검증 비활성화 fallback.

### JavaScript
없음. 순수 vanilla JS + `fetch` + `localStorage`.
