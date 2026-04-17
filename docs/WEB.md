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

1. **제목 / 서브타이틀** — "🎱 로또 6/45 예측기" + 분석 회차 범위
2. **🎯 다음 회차 추천 번호** (`#predictions`) — 5개 전략의 추천 결과
3. **버튼 영역** — "🔄 다시 생성" / "📡 최신 데이터 동기화"
4. **📊 통계 요약** (`#statistics`) — 평균합·홀수·핫·콜드
5. **🏆 최근 당첨번호** (`#recent-draws`) — 최근 10회 테이블
6. **✏️ 당첨번호 수동 등록** — 회차/날짜/번호 입력 폼 + 등록·다운로드·삭제

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
| `loadData()` | 진입점. localStorage → `lotto_cache.json` → GitHub 순서로 로드 시도 |
| `normalizeData(data)` | GitHub 형식(`draw_no`, `bonus_no`)과 내부 형식(`round`, `bonus`)을 모두 내부 형식으로 정규화 |
| `syncFromGithub()` | GitHub 원본 재다운로드. 수동 등록분은 보존 |
| `saveLocal()` | 현재 `lottoData`를 `localStorage["lotto_cache"]`에 저장 |

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
| `render()` | 로딩 끄고 메인 컨텐츠 표시. 하위 렌더 함수들 호출 |
| `renderPredictions(stats)` | `#predictions`에 5개 전략 결과 표시 |
| `renderStats(stats)` | `#statistics`에 통계 요약 표시 |
| `renderRecentDraws()` | `#recent-draws`에 최근 10회 테이블 표시 |
| `ballHTML(n, sm)` / `ballsHTML(nums, sm)` | 공 HTML 조각 생성 |
| `regenerate()` | "다시 생성" 버튼 핸들러. 예측만 다시 그림 |

### 이벤트 (수동 등록 폼)

| 함수 | 역할 |
|---|---|
| `addDraw()` | 입력 검증 후 `lottoData`에 새 회차 추가 → 저장 → 전체 재렌더 |
| `deleteLast()` | 마지막 회차 삭제 (confirm 후) |
| `downloadJSON()` | 현재 `lottoData`를 `lotto_cache.json`으로 다운로드 |
| `showMsg(text, ok)` | 폼 아래에 성공/실패 메시지 3초간 표시 |

## 상태 관리

전역 변수 두 개만 사용합니다.

```javascript
let lottoData = [];            // 전체 당첨번호 (내부 정규화 형식)
const RECENT_WINDOW = 50;      // 최근 N회 트렌드 분석 범위
const GITHUB_ALL_URL = "...";  // 데이터 소스 URL
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
- **localStorage 우선 순위**: 수동 등록이 있을 때, 저장소의 `lotto_cache.json`을 업데이트해도 사용자의 브라우저는 localStorage 데이터를 먼저 씁니다. "최신 데이터 동기화" 버튼을 눌러야 GitHub를 다시 받습니다.
- **브라우저 호환성**: `fetch`, `localStorage`, 화살표 함수, 템플릿 리터럴 사용. 구형 IE 미지원.
