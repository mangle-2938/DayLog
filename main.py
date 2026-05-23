import yaml
import sys
from scripts.collector import collect_all
from scripts.summarizer import summarize
from scripts.writer import write_to_obsidian


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    print("🚀 DayLog 시작\n")
    
    config = load_config()
    
    # 테스트 모드 (AI 호출 없이 데이터 수집만)
    if "--test" in sys.argv:
        print("[ 테스트 모드 - AI 호출 없음 ]\n")
        data = collect_all(config)
        print("\n수집된 앱 목록:")
        for app, info in data["apps"].items():
            print(f"  {app}: {info['minutes']}분")
        print("\n✅ 테스트 완료!")
        return
    
    # 정상 실행
    data = collect_all(config)
    summary = summarize(data, config)
    
    if summary:
        write_to_obsidian(summary, data, config)
        print("\n✅ DayLog 완료!")
    else:
        print("\n❌ 요약 생성 실패")


if __name__ == "__main__":
    main()