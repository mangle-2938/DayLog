import yaml
from scripts.reporter import generate_weekly_report

config = yaml.safe_load(open('config.yaml', encoding='utf-8'))
generate_weekly_report(config)