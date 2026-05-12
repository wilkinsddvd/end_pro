from pathlib import Path


def pytest_configure(config):
    report_dir = Path(__file__).resolve().parent / "test_report"
    report_dir.mkdir(parents=True, exist_ok=True)
