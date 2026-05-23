import yaml
from scripts.collector import collect_all
from scripts.classifier import analyze_projects
from scripts.reporter import save_daily_data

config = yaml.safe_load(open('config.yaml', encoding='utf-8'))
data = collect_all(config)
result = analyze_projects(data, config)
save_daily_data(result, config)