# 로또 6/45 예측기

과거 당첨번호의 통계적 특성을 분석하여 번호를 추천하는 웹사이트 + CLI 도구입니다.

> ⚠️ 로또는 독립 시행이므로 실제 당첨 확률을 높이지 못합니다. 재미로만 활용하세요.

---

## 구성

이 저장소는 **동일한 예측 로직**을 두 가지 방식으로 제공합니다.

| 구성요소 | 파일 | 설명 |
|---|---|---|
| 정적 웹사이트 | `index.html` | 브라우저에서 바로 실행. GitHub Pages 배포 가능. |
| CLI 도구 | `lotto_predictor.py` | 터미널에서 실행하는 Python 스크립트. Excel 백업 포함. |
| 데이터 캐시 | `lotto_cache.json` | 1회 ~ 최신 회차 당첨번호. 웹/CLI 공용. |

## 기능

- 5가지 전략 기반 번호 추천 (전체빈도, 최근트렌드, 콜드넘버, 동반출현, 균형형)
- 핫넘버 / 콜드넘버 / 최근 트렌드 통계
- 최근 당첨번호 조회
- 당첨번호 수동 등록 / 삭제 / JSON 다운로드 (웹)
- GitHub에서 최신 회차 자동 동기화

## 빠른 시작

### 웹사이트로 쓰기
```bash
# 로컬에서 바로 열기
# index.html을 브라우저로 열면 끝. lotto_cache.json을 같이 배포해야 합니다.

# 또는 간단한 로컬 서버
python -m http.server 8000
# http://localhost:8000 접속
```

### CLI로 쓰기
```bash
# 1. (선택) 의존성 설치 (Excel 백업용, 없어도 예측은 동작)
pip install openpyxl certifi

# 2. 최초 실행 - 최신 데이터 받기
python lotto_predictor.py --sync

# 3. 이후 예측만 (캐시 사용, 오프라인 가능)
python lotto_predictor.py
```

## 데이터 출처

당첨번호 데이터는 [smok95/lotto](https://github.com/smok95/lotto) 저장소에서 수집된 데이터를 기반으로 합니다. 원본은 [동행복권](https://www.dhlottery.co.kr/) 공식 추첨 결과입니다.

## 상세 문서

서비스를 수정·확장하기 위한 문서는 `docs/` 폴더에 있습니다.

| 문서 | 내용 |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 전체 구조 · 데이터 흐름 · 저장소 구성 |
| [docs/WEB.md](docs/WEB.md) | `index.html` (프론트엔드) 상세 구조와 함수 명세 |
| [docs/CLI.md](docs/CLI.md) | `lotto_predictor.py` CLI 모드 · 함수 명세 |
| [docs/STRATEGIES.md](docs/STRATEGIES.md) | 5가지 예측 전략의 수학·알고리즘 설명 |
| [docs/DATA.md](docs/DATA.md) | `lotto_cache.json` 스키마와 데이터 수집 흐름 |

처음 읽는다면 → **ARCHITECTURE → WEB / CLI → STRATEGIES → DATA** 순서를 권장합니다.
