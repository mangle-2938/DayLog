import os
import google.generativeai as genai


def build_prompt(data, result=None):
    """수집 데이터를 AI 프롬프트로 변환"""
    
    # 앱 사용시간 텍스트
    app_text = ""
    for app, info in sorted(data["apps"].items(), 
                             key=lambda x: x[1]["minutes"], reverse=True):
        clean_name = app.replace(".exe", "")
        titles = ", ".join(info["titles"][:3])
        app_text += f"  - {clean_name}: {info['minutes']}분"
        if titles:
            app_text += f" (작업: {titles})"
        app_text += "\n"
    
    # 프로젝트 분류 텍스트
    project_text = ""
    if result and result.get("projects"):
        for project, minutes in sorted(result["projects"].items(),
                                        key=lambda x: x[1], reverse=True):
            hours = minutes // 60
            mins = minutes % 60
            goal = data.get("config", {}).get("projects", {}).get(project, {}).get("goal_hours_per_day", 0)
            if goal == 0:
                project_text += f"  - {project}: {hours}시간 {mins}분\n"
            else:
                achieved = "✅" if hours >= goal else "❌"
                project_text += f"  - {achieved} {project}: {hours}시간 {mins}분 (목표: {goal}시간)\n"
    
    # 브라우저 기록 텍스트
    browser_text = ""
    seen = set()
    for title, url, count in (data["chrome"] + data["whale"]):
        if title and title not in seen:
            browser_text += f"  - {title} ({count}회)\n"
            seen.add(title)
    
    prompt = f"""
오늘 {data['date']} 컴퓨터 사용 데이터를 한국어 일지로 정리해줘.

=== 프로젝트별 작업 시간 ===
{project_text if project_text else "  데이터 없음"}

=== 앱 사용 시간 ===
{app_text if app_text else "  데이터 없음"}

=== 브라우저 방문 기록 ===
{browser_text if browser_text else "  데이터 없음"}

아래 형식으로 Obsidian 마크다운 작성해줘:

## 오늘 한 일
(프로젝트별 핵심 작업, [[wikilink]] 포함)

## 프로젝트 달성률
(각 프로젝트 목표 대비 실제 시간)

## 완료
(완료된 것들)

## 내일 할 것
(미완료 또는 이어서 할 것)

## 인사이트
(시간 배분 패턴 분석, 한 줄)

## 연결 노트
(관련 [[wikilink]] 나열)
"""
    return prompt


def summarize(data, config, result=None):
    """Gemini AI로 일지 요약 생성"""
    print("🤖 AI 요약 생성 중...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 없어요.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config['ai']['model'])
        
        data["config"] = config
        prompt = build_prompt(data, result)
        response = model.generate_content(prompt)
        
        print("  ✅ AI 요약 완료")
        return response.text
    
    except Exception as e:
        print(f"AI 요약 오류: {e}")
        return None