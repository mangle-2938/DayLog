# DayLog 🗓️

> 매일 저녁 컴퓨터 작업을 자동으로 AI가 요약해서 Obsidian에 저장해주는 도구

## 기능
- ActivityWatch로 앱 사용시간 자동 수집
- Chrome / Whale 브라우저 방문기록 수집
- Gemini AI로 한국어 일지 자동 작성
- Obsidian Daily Notes에 자동 저장
- 매일 지정 시간 자동 실행

## 설치

### 1. 필수 도구
- Python 3.10+
- ActivityWatch
- Obsidian

### 2. 패키지 설치
pip install -r requirements.txt

### 3. 설정
config.example.yaml 을 config.yaml 로 복사 후 본인 경로로 수정

### 4. Gemini API 키 등록
setx GEMINI_API_KEY "여기에_API_키_입력"

### 5. 실행
python main.py --test   # 테스트
python main.py          # 즉시 실행

### 6. 자동실행 등록 (Windows)
schtasks /create /tn "DayLog" /tr "python C:\Projects\DayLog\main.py" /sc daily /st 20:30 /ru "%USERNAME%"

## 라이선스
MIT