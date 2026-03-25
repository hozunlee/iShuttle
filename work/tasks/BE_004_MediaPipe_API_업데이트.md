# [BE_004] MediaPipe API 업데이트 — mp.solutions 제거 대응

> 상태: DONE
> 담당: BE
> 생성: 2026-03-23
> 완료: 2026-03-25

## 목표

MediaPipe 0.10+ 에서 제거된 `mp.solutions.pose` API를 새 Tasks API로 교체하여 자세 분석이 실제 동작하도록 한다.

## 문제 분석

수동 테스트 로그:
```
[pose] MediaPipe 실패, fallback 사용: module 'mediapipe' has no attribute 'solutions'
[pose] fallback mock 자세 데이터 사용
```

`pose.py` 현재 코드:
```python
import mediapipe as mp
mp_pose = mp.solutions.pose  # ← 0.10+에서 AttributeError
```

MediaPipe 0.10.0부터 `mp.solutions` 네임스페이스가 제거되고 Tasks API로 전환됨.

## 완료 기준 (Done Criteria)

- [ ] `mp.solutions.pose` 대신 `mediapipe.tasks` 또는 `mp.solutions` 래퍼 활용
- [ ] 로그에 `[pose] MediaPipe 실패` 없이 실제 분석 결과 출력
- [ ] `pose_summary.confidence`가 `"mock"` 아닌 `"high"` / `"medium"` / `"low"` 반환

## 구현 방향

옵션 A — Tasks API 전환 (권장):
```python
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

# PoseLandmarker 사용
base_options = mp_tasks.BaseOptions(model_asset_path="models/pose_landmarker.task")
options = vision.PoseLandmarkerOptions(base_options=base_options, ...)
```

옵션 B — 구버전 호환 패키지 고정:
```
# pyproject.toml
mediapipe>=0.10.0,<0.10.3  # solutions API 마지막 지원 버전
```

옵션 A 권장. 단, Tasks API용 모델 파일(`pose_landmarker.task`) 별도 다운로드 필요.

## 의존성

- 선행 필요: 없음
- 후행 영향: AI 리포트 자세 분석 정확도

## 메모 / 이슈

- 모델 파일: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- 현재 설치 버전 확인: `uv run python -c "import mediapipe; print(mediapipe.__version__)"`
