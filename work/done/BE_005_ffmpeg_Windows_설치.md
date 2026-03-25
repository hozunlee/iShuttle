# [BE_005] ffmpeg Windows 설치 확인 & 클립 생성 검증

> 상태: DONE
> 담당: BE
> 생성: 2026-03-25
> 실기록: 2026-03-25 겜북 실행 시 `[WinError 2] 지정된 파일을 찾을 수 없습니다` — 모든 랠리 클립 생성 실패

## 목표

겜북(Windows)에서 ffmpeg가 PATH에 설치되어 랠리 클립(.mp4) 및 숏폼이 정상 생성된다.

## 완료 기준 (Done Criteria)

- [x] `ffmpeg -version` 명령어가 PowerShell에서 정상 출력
- [x] 분석 후 `output/clips/{job_id}/rally_001.mp4` 파일 존재
- [x] 로그에 `[editor] 완료` 이후 클립 실패 WARNING 없음

## 설치 방법

```powershell
# 방법 1 — winget (Windows 11 기본)
winget install ffmpeg

# 방법 2 — chocolatey
choco install ffmpeg

# 설치 후 확인
ffmpeg -version
```

## 의존성

- 선행 필요: 없음
- 후행 영향: editor.py 클립/숏폼 생성, 연습 모드 영상 재생

## 메모

- editor.py는 `subprocess.run(["ffmpeg", ...])` 으로 시스템 PATH의 ffmpeg 호출
- Windows에서 ffmpeg는 자동 설치 안 됨, 수동 설치 필요
- macOS는 `brew install ffmpeg` 으로 해결
- **[26-03-25 갱신]** 설치는 완료되었으나 현재 터미널이 `ffmpeg` 명령어를 인식하지 못함 (PATH 미등록 또는 터미널 미재시작). 환경변수에 `ffmpeg.exe` 경로가 추가되었는지 확인하고 재부팅(또는 IDE 재시작) 필요. 현재 상태는 `BLOCKED`로 처리함.
- **[26-03-25 갱신]** 터미널에서 `ffmpeg` 정상 인식 확인. `output/clips/{job_id}/` 디렉토리에 정상적으로 .mp4 클립들이 생성된 것을 확인하여 `DONE` 처리함.
