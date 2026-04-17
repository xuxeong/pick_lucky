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

**증상**: `https://smok95.github.io/...`이 404.

**대응** (우선순위 순):

**A. 대체 미러 탐색**
- GitHub 검색: `lotto 645 korea json` 유사 프로젝트 여러 개
- 찾으면 `scripts/sync_lotto.py`의 `GITHUB_ALL_URL`과 `normalize()`만 수정

**B. 동행복권 공식 API 직접 사용**
- `https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=N` (회차별 JSON)
- 장점: 공식 소스, 영구 가용 가능성 큼
- 단점: CORS 제한으로 브라우저 직접 요청 불가 (Actions에서는 문제없음), 회차별 N번 요청 필요
- 구현: `sync_lotto.py`에서 기존 최신 회차 다음부터 하나씩 순회

**C. 저장소 데이터로 당분간 버티기**
- 이미 `lotto_cache.json`에 1회~현재까지 데이터가 있음
- 자동 갱신만 멈췄을 뿐 서비스는 계속 동작
- 사용자는 수동 등록 폼으로 새 회차 직접 입력 (매주 1회 5분)

### 사례 ④: Actions 권한 문제로 push 실패

**증상**: 이슈에 `Permission denied` 또는 `403`.

**대응**:
1. 저장소 Settings → Actions → General → "Workflow permissions"
2. "Read and write permissions" 선택 + "Allow GitHub Actions to create and approve pull requests" 체크
3. 실패한 워크플로우 재실행

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
