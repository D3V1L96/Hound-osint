import json
from datetime import datetime
from pathlib import Path
class ReportGenerator:
    def __init__(self, display):
        self.display = display
        self.reports_dir = Path('hound_reports')
        self.reports_dir.mkdir(exist_ok=True)
    def save_report(self, target, data, report_type='general'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hound_report_{target}_{timestamp}.json"
        filepath = self.reports_dir / filename
        report = {'target': target, 'timestamp': datetime.now().isoformat(), 'data': data}
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        self.display.print_success(f"Report saved to: {filepath}")
        return filepath
