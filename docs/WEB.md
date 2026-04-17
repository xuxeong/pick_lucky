# 웹사이트 (index.html) 상세

정적 HTML 한 개 파일로 구성된 SPA입니다. 빌드 단계 없이 브라우저가 그대로 해석합니다.

## 파일 섹션 구조

`index.html`은 세 부분으로 나뉩니다.

| 라인 (대략) | 영역 | 내용 |
|---|---|---|
| 1 ~ 107 | `<style>` | 전체 CSS |
| 108 ~ 179 | `<body>` | 화면 레이아웃 (카드들) |
| 181 ~ 551 | `<script>` | 앱 로직 (데이터·통계·전략·렌더·이벤트) |

## UI 카드 구성

화면 위에서 아래로:

1. **제목 / 서브타이틀** — "🎱 로또 6/45 예측기" + 분석 회차 범위 + **최종 추첨일**
2. **⚠️ 데이터 노후/오류 배너** (`#stale-banner`, 조건부) — 최신 추첨일이 8일 이상 지났거나 공식 파일을 못 받았을 때만 표시
3. **🎯 다음 회차 추천 번호** (`#predictions`) — 5개 전략의 추천 결과
4. **버튼 영역** — "🔄 다시 생성" / "📡 최신 데이터 동기화"
5. **📊 통계 요약** (`#statistics`) — 평균합·홀수·핫·콜드
6. **🏆 최근 당첨번호** (`#recent-draws`) — 최근 10회 테이블
7. **✏️ 당첨번호 수동 등록** (비상용) — 회차/날짜/번호 입력 폼 + 등록·다운로드·삭제

## 주요 CSS 클래스

| 클래스 | 용도 |
|---|---|
| `.card` | 흰 박스 (둥근 모서리 + 그림자) |
| `.ball` / `.ball-sm` | 로또 공 (원형, 색상은 `ballColor()`에서 계산) |
| `.pred-row` | 예측 결과 한 줄 (이름 / 공들 / 합·홀수) |
| `.stat-row` | 통계 한 줄 |
| `.recent-table` | 최근 당첨번호 테이블 |
| `.btn` + `.green`/`.orange`/`.red`/`.sm` | 버튼 변종 |
| `.form-row` | 입력 폼 한 줄 |

반응형: 600px 이하에서 패딩·공 크기 등을 줄입니다 (`@media (max-width: 600px)`).

## 색상 규칙 (공)

`ballColor(n)` — 동행복권 공식 색상과 동일합니다.

| 번호 범위 | 색상 (hex) | 의미 |
|---|---|---|
| 1 ~ 10 | `#FFC000` | 노랑 |
| 11 ~ 20 | `#4472C4` | 파랑 |
| 21 ~ 30 | `#FF4444` | 빨강 |
| 31 ~ 40 | `#A5A5A5` | 회색 |
| 41 ~ 45 | `#70AD47` | 초록 |

## JavaScript 함수 명세

### 데이터 계층

| 함수 | 역할 |
|---|---|
| `loadData()` | 진입점. **저장소 `lotto_cache.json`을 항상 먼저 확인** (no-cache), localStorage와 머지. 둘 다 실패하면 `syncFromGithub()` |
| `mergeOfficialWithManual(official, local)` | 공식 데이터 기준으로 localStorage의 수동 등록분을 뒤에 붙임. 같은 회차 값이 다르면 공식이 이기고 콘솔 경고 |
| `normalizeData(data)` | GitHub 형식(`draw_no`, `bonus_no`)과 내부 형식(`round`, `bonus`)을 모두 내부 형식으로 정규화 |
| `syncFromGithub()` | **비상 수단**. smok95 원본 직접 요청. 수동 등록분은 보존 |
| `saveLocal()` | 현재 `lottoData`를 `localStorage["lotto_cache"]`에 저장 |

### 머지 정책

`mergeOfficialWithManual()`의 원칙:
- **공식이 이긴다.** 같은 회차 번호가 있으면 `lotto_cache.json`(또는 smok95) 값으로 덮어씀
- 값이 다른 경우 **조용히 덮지 않음** — `console.warn`으로 `{manual, official}` 양쪽을 로그
- localStorage에만 있는 회차(= 공식에 아직 없는 수동 등록분)는 살림
- 결과는 `round` 오름차순 정렬

### 통계·예측 계층

| 함수 | 역할 |
|---|---|
| `analyze(data)` | 전체/최근 빈도, 쌍 카운트, 갭(마지막 출현 이후 경과 회차), 평균합, 홀수 최빈값 계산 |
| `weightedSample(weights)` | 가중치 맵 `{번호: 가중치}`에서 중복 없이 6개 선택 |
| `isBalanced(nums, stats)` | 합계·홀짝·구간편중·연속번호 제약 검사 |
| `STRATEGIES` (배열) | 5개 전략. 각 원소는 `{name, fn(stats)}` |

수학적 설명은 [STRATEGIES.md](STRATEGIES.md) 참조.

### 렌더링 계층

| 함수 | 역할 |
|---|---|
| `render()` | 로딩 끄고 메인 컨텐츠 표시. 서브타이틀에 최종 추첨일 포함. 하위 렌더 함수 호출 |
| `renderStaleBanner(lastDateStr)` | 최신 추첨일이 8일 이상 지났으면 노란 경고 배너, `loadError`가 있으면 빨간 오류 배너 |
| `renderPredictions(stats)` | `#predictions`에 5개 전략 결과 표시 |
| `renderStats(stats)` | `#statistics`에 통계 요약 표시 |
| `renderRecentDraws()` | `#recent-draws`에 최근 10회 테이블 표시 |
| `ballHTML(n, sm)` / `ballsHTML(nums, sm)` | 공 HTML 조각 생성 |
| `regenerate()` | "다시 생성" 버튼 핸들러. 예측만 다시 그림 |

### 배너 트리거 조건

| 상태 | 배너 색 | 메시지 |
|---|---|---|
| `loadError` 있음 (공식 파일 fetch 실패 + GitHub도 실패) | 빨강 | "공식 데이터를 불러오지 못했습니다" + 수동 동기화 버튼 |
| 최신 추첨일 + 8일 < 오늘 | 노랑 | "N일째 갱신되지 않았습니다" + 수동 등록/동기화 안내 |
| 그 외 (정상) | 숨김 | — |

8일 기준: 로또는 매주 토요일 추첨이므로 정상 범위는 최대 7일. 8일이면 한 회차를 놓친 것.

### 이벤트 (수동 등록 폼)

| 함수 | 역할 |
|---|---|
| `addDraw()` | 입력 검증 후 `lottoData`에 새 회차 추가 → 저장 → 전체 재렌더 |
| `deleteLast()` | 마지막 회차 삭제 (confirm 후) |
| `downloadJSON()` | 현재 `lottoData`를 `lotto_cache.json`으로 다운로드 |
| `showMsg(text, ok)` | 폼 아래에 성공/실패 메시지 3초간 표시 |

## 상태 관리

전역 변수:

```javascript
let lottoData = [];            // 전체 당첨번호 (내부 정규화 형식)
let loadError = null;          // 공식 파일 로드 실패 시 에러 메시지 (배너 트리거)
const RECENT_WINDOW = 50;      // 최근 N회 트렌드 분석 범위
const GITHUB_ALL_URL = "...";  // 비상용 원본 소스 URL
```

영속화는 `localStorage["lotto_cache"]` 한 개 키로만 이루어집니다.

## 흔한 수정 사례

### "최근 트렌드" 분석 범위 바꾸기
- `RECENT_WINDOW` 상수 변경 (기본 50회)
- Python 쪽도 같은 이름의 상수를 동시에 바꾸세요.

### 전략 추가하기
1. `STRATEGIES` 배열에 `{name: "…", fn: stats => [...6개 번호...]}` 추가
2. Python `STRATEGIES`에도 대응 전략 추가
3. [STRATEGIES.md](STRATEGIES.md)에 설명 추가

### 색상 변경
- `ballColor(n)` 함수 (JS) + `BALL_COLORS` 리스트 (Python) 함께 수정

### 표시 회차 수 바꾸기 (최근 당첨번호 테이블)
- `renderRecentDraws()` 내부 `data.slice(-10)`의 `10`을 변경

### 균형형 제약 조정
- `isBalanced()` 함수 수정 (합계 범위, 홀짝, 구간 편중, 연속 번호). Python `is_balanced()`도 같이 수정.

## 주의점

- **파일 직접 열기 vs 로컬 서버**: `file://` 프로토콜로 `index.html`을 열면 `fetch("lotto_cache.json")`이 CORS로 실패할 수 있습니다. `python -m http.server`로 띄우는 것을 권장합니다.
- **공식 파일이 항상 이김**: 이제 매 방문마다 `lotto_cache.json`을 `no-cache`로 다시 받습니다. localStorage는 수동 등록분 보존 용도일 뿐, 새 회차 전파를 막지 않습니다.
- **수동 등록 후 공식 데이터 들어오면**: 같은 회차가 `lotto_cache.json`에 실리는 순간 localStorage의 수동 값은 공식 값으로 덮입니다. 값이 다르면 콘솔에 경고가 남습니다 (개발자 도구 F12에서 확인).
- **브라우저 호환성**: `fetch`, `localStorage`, 화살표 함수, 템플릿 리터럴 사용. 구형 IE 미지원.
