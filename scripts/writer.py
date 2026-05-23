import os
from datetime import date, timedelta


def write_to_obsidian(summary, data, config, result=None):
    """Obsidian Daily Notes 폴더에 마크다운 저장"""
    print("📝 Obsidian에 저장 중...")
    
    today = data["date"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    # 앱 목록 추출
    apps = [app.replace(".exe", "") for app in data["apps"].keys()]
    apps_str = ", ".join(apps[:5])
    
    # 노트 내용 구성
    content = f"""---
date: {today}
tags: [daily-log]
apps: [{apps_str}]
---

# {today}
[[{yesterday}]] ← 오늘 → [[{tomorrow}]]

{summary}

#daily-log
"""
    
    # 저장 경로 설정
    vault_path = config['obsidian']['vault_path']
    folder = config['obsidian']['daily_notes_folder']
    save_dir = os.path.join(vault_path, folder)
    
    # 폴더 없으면 생성
    os.makedirs(save_dir, exist_ok=True)
    
    # 파일 저장
    file_path = os.path.join(save_dir, f"{today}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"  ✅ 저장 완료: {file_path}")
    return file_path