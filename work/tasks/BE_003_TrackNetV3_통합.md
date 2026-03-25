# [BE_003] TrackNetV3 통합 — 셔틀콕 추적 1차 모델 구현

> 상태: TODO
> 담당: BE
> 생성: 2026-03-23
> 실기록: 2026-03-25 실제 영상 테스트 — TrackNetV3 없이 광학 플로우 fallback 진입, 0개 감지 → mock 사용 확인

## 목표

CONTEXT.md F1의 1차 모델인 TrackNetV3를 실제로 동작시켜 셔틀콕 추적 및 랠리 자동 분리를 수행한다.

## 현재 상태

`models/TrackNetV3/` 디렉토리 자체가 없어서 즉시 FileNotFoundError → 광학 플로우 fallback → 0개 랠리.
광학 플로우는 셔틀콕이 아닌 임의의 빠른 점을 추적하므로 랠리 감지 신뢰도가 낮다.

## 완료 기준 (Done Criteria)

- [ ] `backend/models/TrackNetV3/predict.py` 실행 가능
- [ ] 체크포인트 파일 `ckpts/TrackNet_best.pt`, `ckpts/InpaintNet_best.pt` 존재
- [ ] 20분 영상 분석 시 랠리 1개 이상 감지
- [ ] 로그에 `[rally] TrackNetV3 완료: N개 랠리` 출력

## 설치 방법

### 1단계 — 레포 클론

```bash
cd backend/models
git clone https://github.com/alenzenx/TrackNetV3.git
```

### 2단계 — 체크포인트 다운로드

TrackNetV3 GitHub Releases 또는 논문 공식 링크에서:
- `TrackNet_best.pt` → `backend/models/TrackNetV3/ckpts/`
- `InpaintNet_best.pt` → `backend/models/TrackNetV3/ckpts/`

### 3단계 — 의존성 확인

TrackNetV3의 `requirements.txt` 확인 후 `pyproject.toml`에 추가.
주요 의존: `torch`, `torchvision` (이미 포함)

### 4단계 — 동작 테스트

```bash
cd backend
uv run python models/TrackNetV3/predict.py \
  --video_file uploads/sample.mp4 \
  --tracknet_file models/TrackNetV3/ckpts/TrackNet_best.pt \
  --inpaintnet_file models/TrackNetV3/ckpts/InpaintNet_best.pt \
  --save_dir output/tracknet_tmp
```

## 임시 조치 (TrackNetV3 설치 전 테스트용)

광학 플로우가 0개 반환 시 mock으로 자동 fallback 추가 (`rally.py`):

```python
if len(rallies) == 0:
    logger.warning("[rally] 광학 플로우 0개 → mock으로 대체")
    return _mock_rallies(video_path)
```

→ 이 임시 조치로 결과 화면까지 end-to-end 테스트 가능.

## 의존성

- 선행 필요: 없음
- 후행 영향: 랠리 품질에 의존하는 모든 기능 (editor, formation, reporter)

## 메모 / 이슈

- TrackNetV3는 pip 패키지가 아닌 연구 레포. subprocess로 실행하는 현재 구조 유지.
- CPU only 환경에서 TrackNetV3 추론 속도 확인 필요 (20분 영상 기준 예상 5~15분)
- 체크포인트 파일은 gitignore 대상 (`models/**/*.pt`)
