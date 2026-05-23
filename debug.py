import yaml
from scripts.collector import collect_all
from scripts.classifier import classify_project

with open('config.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)

data = collect_all(config)
print("\n앱 분류:")
for app, info in data['apps'].items():
    title = info['titles'][0] if info['titles'] else ''
    project = classify_project(app, title, '', config)
    print(f"  {app} ({info['minutes']}분) → {project}")

print("\n브라우저 분류:")
for title, url, count in (data['chrome'] + data['whale'])[:10]:
    from scripts.classifier import classify_project, classify_consumption
    is_consumption = classify_consumption("", url, config)
    project = classify_project("", title, url, config)
    print(f"  {'🔴소비' if is_consumption else '🟢'+project}: {title[:30]}")
