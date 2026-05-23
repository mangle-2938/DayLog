"""
scripts/reporter.py
주간/월간 리포트 생성 모듈

역할:
  1. save_daily_data()       → 매일 실행 후 classified 결과를 data/YYYY-MM-DD.json 으로 누적 저장
  2. generate_weekly_report()  → 매주 금요일 20:30 → Obsidian/Weekly Notes 저장
  3. generate_monthly_report() → 매월 마지막날 20:30 → Obsidian/Monthly Notes 저장
"""

import json
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from calendar import monthrange


# ── 1. 일별 데이터 저장 ──────────────────────────────────────────────────────

def save_daily_data(classified_data: dict, config: dict) -> Path:
    """
    analyze_projects() 결과를 data/YYYY-MM-DD.json 으로 저장.
    main.py 에서 writer.py 호출 직전에 실행.
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    today = date.today().isoformat()
    filepath = data_dir / f"{today}.json"

    payload = {
        "date": today,
        "projects": classified_data.get("projects", {}),
        "consumption": classified_data.get("consumption", 0),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 일별 데이터 저장: {filepath}")
    return filepath


# ── 2. 데이터 로드 헬퍼 ─────────────────────────────────────────────────────

def _load_range(start: date, end: date) -> dict[str, dict]:
    """start ~ end(포함) 범위의 JSON 파일 로드. 없는 날은 건너뜀."""
    data_dir = Path("data")
    result = {}

    current = start
    while current <= end:
        filepath = data_dir / f"{current.isoformat()}.json"
        if filepath.exists():
            with open(filepath, encoding="utf-8") as f:
                result[current.isoformat()] = json.load(f)
        current += timedelta(days=1)

    return result


# ── 3. 집계 공통 로직 ────────────────────────────────────────────────────────

def _aggregate(data: dict[str, dict], config: dict) -> dict:
    projects_config = config.get("projects", {})

    project_totals: dict[str, int] = {}
    project_daily: dict[str, dict[str, int]] = {}
    daily_consumption: dict[str, int] = {}

    for day, payload in sorted(data.items()):
        consumption = payload.get("consumption", 0)
        daily_consumption[day] = consumption

        for project, minutes in payload.get("projects", {}).items():
            project_totals[project] = project_totals.get(project, 0) + minutes
            project_daily.setdefault(project, {})[day] = minutes

    project_goals = {}
    for name, settings in projects_config.items():
        goal_h = settings.get("goal_hours_per_day", 0)
        if goal_h:
            project_goals[name] = goal_h * 60

    return {
        "days_count": len(data),
        "dates": sorted(data.keys()),
        "project_totals": project_totals,
        "project_daily": project_daily,
        "total_consumption": sum(daily_consumption.values()),
        "daily_consumption": daily_consumption,
        "project_goals": project_goals,
    }


def _fmt_minutes(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    return f"{h}시간 {m}분"


def _achievement_bar(ratio: float, width: int = 10) -> str:
    filled = round(ratio * width)
    filled = max(0, min(width, filled))
    bar = "▓" * filled + "░" * (width - filled)
    return f"{bar} {ratio * 100:.0f}%"


# ── 4. 주간 리포트 ───────────────────────────────────────────────────────────

def generate_weekly_report(config: dict, target_date: date | None = None) -> str:
    """
    target_date 기준 직전 7일 리포트 생성.
    저장 위치: Obsidian/Weekly Notes/
    """
    if target_date is None:
        target_date = date.today()

    end   = target_date
    start = target_date - timedelta(days=6)

    data = _load_range(start, end)
    if not data:
        print("⚠️  주간 데이터 없음")
        return ""

    agg = _aggregate(data, config)
    md  = _build_weekly_md(agg, start, end, config)

    obsidian_root = Path(config["obsidian"]["vault_path"])
    weekly_dir = obsidian_root / "Weekly Notes"
    weekly_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{start.isoformat()}~{end.isoformat()}.md"
    filepath = weekly_dir / filename
    filepath.write_text(md, encoding="utf-8")

    print(f"  ✅ 주간 리포트 저장: {filepath}")
    return str(filepath)


def _build_weekly_md(agg: dict, start: date, end: date, config: dict) -> str:
    lines = []

    lines += [
        f"# 📊 주간 리포트  {start.strftime('%m/%d')} – {end.strftime('%m/%d')}",
        f"> 데이터 {agg['days_count']}일 기록 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    lines += ["## 프로젝트별 달성 현황", ""]

    for project, total in sorted(agg["project_totals"].items(), key=lambda x: -x[1]):
        goal_mpd = agg["project_goals"].get(project, 0)
        avg_mpd  = total / agg["days_count"]

        lines.append(f"### {project}")
        lines.append(f"- **총 시간**: {_fmt_minutes(total)}")
        lines.append(f"- **일 평균**: {_fmt_minutes(avg_mpd)}")

        if goal_mpd:
            ratio = avg_mpd / goal_mpd
            lines.append(f"- **목표 달성률**: {_achievement_bar(ratio)}")
            goal_days = sum(
                1 for d, m in agg["project_daily"].get(project, {}).items()
                if m >= goal_mpd
            )
            lines.append(f"- **목표 달성일**: {goal_days}/{agg['days_count']}일")

        lines.append("- **일별 기록**:")
        for d in agg["dates"]:
            minutes = agg["project_daily"].get(project, {}).get(d, 0)
            bar = "█" * min(int(minutes / 30), 12)
            lines.append(f"  - {d[5:]}  {bar} {_fmt_minutes(minutes)}")

        lines.append("")

    total_creation    = sum(agg["project_totals"].values())
    total_consumption = agg["total_consumption"]
    total_all         = total_creation + total_consumption

    lines += ["## ⚖️ 제작 vs 소비", ""]
    if total_all > 0:
        c_ratio = total_creation   / total_all
        s_ratio = total_consumption / total_all
        lines.append(f"- **제작**: {_fmt_minutes(total_creation)} ({c_ratio*100:.0f}%)")
        lines.append(f"- **소비**: {_fmt_minutes(total_consumption)} ({s_ratio*100:.0f}%)")
        lines.append(f"- **비율 바**: {'🟩' * round(c_ratio*10)}{'🟥' * round(s_ratio*10)}")
    lines.append("")

    return "\n".join(lines)


# ── 5. 월간 리포트 ───────────────────────────────────────────────────────────

def generate_monthly_report(config: dict, year: int | None = None, month: int | None = None) -> str:
    """
    해당 월 전체 리포트 생성.
    저장 위치: Obsidian/Monthly Notes/
    """
    if year  is None: year  = date.today().year
    if month is None: month = date.today().month

    _, last_day = monthrange(year, month)
    start = date(year, month, 1)
    end   = date(year, month, last_day)

    data = _load_range(start, end)
    if not data:
        print("⚠️  월간 데이터 없음")
        return ""

    agg = _aggregate(data, config)
    md  = _build_monthly_md(agg, year, month, config)

    obsidian_root = Path(config["obsidian"]["vault_path"])
    monthly_dir = obsidian_root / "Monthly Notes"
    monthly_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{year}-{month:02d}.md"
    filepath = monthly_dir / filename
    filepath.write_text(md, encoding="utf-8")

    print(f"  ✅ 월간 리포트 저장: {filepath}")
    return str(filepath)


def _build_monthly_md(agg: dict, year: int, month: int, config: dict) -> str:
    lines = []

    lines += [
        f"# 📅 월간 리포트  {year}년 {month}월",
        f"> 데이터 {agg['days_count']}일 기록 | 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    lines += ["## 프로젝트별 월간 달성률", ""]

    for project, total in sorted(agg["project_totals"].items(), key=lambda x: -x[1]):
        goal_mpd = agg["project_goals"].get(project, 0)
        avg_mpd  = total / agg["days_count"]

        lines.append(f"### {project}")
        lines.append(f"- **총 시간**: {_fmt_minutes(total)}")
        lines.append(f"- **일 평균**: {_fmt_minutes(avg_mpd)}")

        if goal_mpd:
            ratio = avg_mpd / goal_mpd
            lines.append(f"- **월 평균 달성률**: {_achievement_bar(ratio)}")
            goal_days = sum(
                1 for d, m in agg["project_daily"].get(project, {}).items()
                if m >= goal_mpd
            )
            lines.append(f"- **목표 달성일**: {goal_days}/{agg['days_count']}일")

        lines.append("")

    lines += ["## 📈 주차별 제작 vs 소비 트렌드", ""]
    lines += _weekly_trend_rows(agg, year, month)
    lines.append("")

    total_creation    = sum(agg["project_totals"].values())
    total_consumption = agg["total_consumption"]
    total_all         = total_creation + total_consumption

    lines += ["## ⚖️ 월간 제작 vs 소비 총계", ""]
    if total_all > 0:
        c_ratio = total_creation   / total_all
        s_ratio = total_consumption / total_all
        lines.append(f"- **제작**: {_fmt_minutes(total_creation)} ({c_ratio*100:.0f}%)")
        lines.append(f"- **소비**: {_fmt_minutes(total_consumption)} ({s_ratio*100:.0f}%)")
        lines.append(f"- **비율 바**: {'🟩' * round(c_ratio*10)}{'🟥' * round(s_ratio*10)}")
    lines.append("")

    return "\n".join(lines)


def _weekly_trend_rows(agg: dict, year: int, month: int) -> list[str]:
    from collections import defaultdict

    weekly: dict[int, dict] = defaultdict(lambda: {"creation": 0, "consumption": 0})

    for day_str, consumption in agg["daily_consumption"].items():
        d = date.fromisoformat(day_str)
        if d.month != month:
            continue
        week_num = (d.day - 1) // 7 + 1

        creation = sum(
            agg["project_daily"].get(p, {}).get(day_str, 0)
            for p in agg["project_totals"]
        )
        weekly[week_num]["creation"]    += creation
        weekly[week_num]["consumption"] += consumption

    rows = ["| 주차 | 제작 | 소비 | 제작 비율 |", "|------|------|------|-----------|"]
    for wk in sorted(weekly):
        c = weekly[wk]["creation"]
        s = weekly[wk]["consumption"]
        total = c + s
        ratio = f"{c/total*100:.0f}%" if total else "-"
        rows.append(f"| {wk}주차 | {_fmt_minutes(c)} | {_fmt_minutes(s)} | {ratio} |")

    return rows


# ── 6. main.py 연동 편의 함수 ────────────────────────────────────────────────

def run_weekly_if_friday(config: dict) -> None:
    """매주 금요일 20:30 자동 실행. Weekly Notes 저장."""
    if date.today().weekday() == 4:  # 4 = 금요일
        print("📋 주간 리포트 생성 중...")
        generate_weekly_report(config, target_date=date.today())


def run_monthly_if_last(config: dict) -> None:
    """매월 마지막날 20:30 자동 실행. Monthly Notes 저장."""
    today = date.today()
    last_day = monthrange(today.year, today.month)[1]
    if today.day == last_day:
        print("📋 월간 리포트 생성 중...")
        generate_monthly_report(config, year=today.year, month=today.month)