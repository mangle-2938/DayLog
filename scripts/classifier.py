def classify_project(app, title, url, config):
    """앱/창제목/URL로 프로젝트 자동 분류"""
    
    projects = config.get("projects", {})
    text = f"{app} {title} {url}".lower()
    
    for project_name, settings in projects.items():
        # 키워드 매칭
        for keyword in settings.get("keywords", []):
            if keyword.lower() in text:
                return project_name
        
        # URL 매칭
        for url_pattern in settings.get("urls", []):
            if url_pattern.lower() in text:
                return project_name
    
    return "기타"


def classify_consumption(app, url, config):
    """소비 활동인지 판단"""
    
    consumption = config.get("consumption", {})
    
    # 소비 앱 체크
    if app in consumption.get("apps", []):
        return True
    
    # 소비 URL 체크
    for url_pattern in consumption.get("urls", []):
        if url_pattern.lower() in url.lower():
            return True
    
    return False


def analyze_projects(data, config):
    """수집된 데이터를 프로젝트별로 분류"""
    
    project_time = {}
    consumption_time = 0
    
    # 앱 사용시간 분류 (앱당 1회만 계산)
    for app, info in data["apps"].items():
        minutes = info["minutes"]
        best_title = info["titles"][0] if info["titles"] else ""
        project = classify_project(app, best_title, "", config)
        
        if app in config.get("consumption", {}).get("apps", []):
            consumption_time += minutes
        else:
            if project not in project_time:
                project_time[project] = 0
            project_time[project] += minutes
    
   # 브라우저 기록 분류 (방문횟수 무관, 사이트당 5분 고정)
    seen_urls = set()
    for title, url, count in (data["chrome"] + data["whale"]):
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        if classify_consumption("", url, config):
            consumption_time += 5
        else:
            project = classify_project("", title, url, config)
            if project not in project_time:
                project_time[project] = 0
            project_time[project] += 5
    
    return {
        "projects": project_time,
        "consumption": consumption_time
    }