import yaml
import sys
from scripts.collector import collect_all
from scripts.summarizer import summarize
from scripts.writer import write_to_obsidian
from scripts.classifier import analyze_projects
from scripts.reporter import save_daily_data, run_weekly_if_friday, run_monthly_if_last


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    print("🚀 DayLog 시작\n")

    config = load_config()

    # 테스트 모드
    if "--test" in sys.argv:
        print("[ 테스트 모드 - AI 호출 없음 ]\n")
        data = collect_all(config)

        # 프로젝트 분류
        result = analyze_projects(data, config)
        save_daily_data(result, config)

        print("\n📊 프로젝트별 시간:")
        for project, minutes in sorted(result["projects"].items(),
                                        key=lambda x: x[1], reverse=True):
            hours = minutes // 60
            mins = minutes % 60
            goal = config["projects"].get(project, {}).get("goal_hours_per_day", 0)
            achieved = "✅" if hours >= goal else "❌"
            print(f"  {achieved} {project}: {hours}시간 {mins}분 (목표: {goal}시간)")

        print("\n🔍 앱별 분류 상세:")
        for app, info in data["apps"].items():
            for title in info["titles"]:
                from scripts.classifier import classify_project
                project = classify_project(app, title, "", config)
                print(f"  {app} ({title}) → {project}: {info['minutes']}분")

        total = sum(result["projects"].values())
        if total > 0:
            consumption_ratio = result["consumption"] / (total + result["consumption"]) * 100
            production_ratio = 100 - consumption_ratio
            print(f"\n⚖️  제작 {production_ratio:.0f}% vs 소비 {consumption_ratio:.0f}%")

        print("\n✅ 테스트 완료!")
        return

    # 정상 실행
    data = collect_all(config)
    result = analyze_projects(data, config)
    save_daily_data(result, config)
    summary = summarize(data, config, result)

    if summary:
        write_to_obsidian(summary, data, config, result)
        run_weekly_if_friday(config)    # 금요일에만 실행
        run_monthly_if_last(config)     # 월 마지막날에만 실행
        print("\n✅ DayLog 완료!")
    else:
        print("\n❌ 요약 생성 실패")


if __name__ == "__main__":
    main()