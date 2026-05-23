import requests
import sqlite3
import shutil
import os
from datetime import datetime, date

def get_activitywatch_data(config):
    """ActivityWatch에서 오늘 앱 사용시간 수집"""
    host = config['activitywatch']['host']
    port = config['activitywatch']['port']
    min_minutes = config['activitywatch']['min_app_time_minutes']
    
    try:
        # 버킷 목록 가져오기
        response = requests.get(f"http://{host}:{port}/api/0/buckets")
        buckets = response.json()
        
        # window watcher 버킷 찾기
        window_bucket = None
        for bucket in buckets:
            if 'aw-watcher-window' in bucket:
                window_bucket = bucket
                break
        
        if not window_bucket:
            print("ActivityWatch window watcher를 찾을 수 없어요.")
            return {}
        
        # 오늘 데이터 가져오기
        today = date.today().isoformat()
        url = f"http://{host}:{port}/api/0/buckets/{window_bucket}/events"
        params = {
            "start": f"{today}T00:00:00+09:00",
            "end": f"{today}T23:59:59+09:00"
        }
        
        response = requests.get(url, params=params)
        events = response.json()
        
        # 앱별 사용시간 집계
        app_time = {}
        for event in events:
            app = event["data"].get("app", "Unknown")
            title = event["data"].get("title", "")
            duration = event.get("duration", 0)
            
            if app not in app_time:
                app_time[app] = {"seconds": 0, "titles": set()}
            app_time[app]["seconds"] += duration
            app_time[app]["titles"].add(title)
        
        # 최소 시간 필터링
        filtered = {}
        for app, info in app_time.items():
            if info["seconds"] / 60 >= min_minutes:
                filtered[app] = {
                    "minutes": round(info["seconds"] / 60),
                    "titles": list(info["titles"])[:5]
                }
        
        return filtered
    
    except Exception as e:
        print(f"ActivityWatch 수집 오류: {e}")
        return {}


def get_browser_history(browser="chrome"):
    """Chrome 또는 Whale 방문 기록 수집"""
    paths = {
        "chrome": os.path.expanduser(
    r"~\AppData\Local\Google\Chrome\User Data\Profile 1\History"
),
        "whale": os.path.expanduser(
    r"~\AppData\Local\Naver\Naver Whale\User Data\Profile 1\History"
),
    }
    
    path = paths.get(browser)
    if not path or not os.path.exists(path):
        return []
    
    tmp = f"temp_{browser}_history.db"
    try:
        shutil.copy2(path, tmp)
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        
        # 오늘 방문한 URL
        import time
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        chrome_epoch = datetime(1601, 1, 1)
        delta = today - chrome_epoch
        today_chrome = int(delta.total_seconds() * 1000000)
        
        cursor.execute("""
            SELECT title, url, visit_count 
            FROM urls 
            WHERE last_visit_time > ?
            AND url NOT LIKE 'chrome%'
            AND url NOT LIKE 'about%'
            ORDER BY visit_count DESC
            LIMIT 20
        """, (today_chrome,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    except Exception as e:
        print(f"{browser} 기록 수집 오류: {e}")
        return []
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def collect_all(config):
    """모든 데이터 수집"""
    print("📊 데이터 수집 중...")
    
    aw_data = get_activitywatch_data(config)
    print(f"  ✅ ActivityWatch: 앱 {len(aw_data)}개")
    
    chrome_data = get_browser_history("chrome")
    print(f"  ✅ Chrome: {len(chrome_data)}개 사이트")
    
    whale_data = get_browser_history("whale")
    print(f"  ✅ Whale: {len(whale_data)}개 사이트")
    
    return {
        "apps": aw_data,
        "chrome": chrome_data,
        "whale": whale_data,
        "date": date.today().isoformat()
    }