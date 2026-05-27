import json
import re
from datetime import datetime
from pathlib import Path


REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "saved_reports"


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", text.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "report"


def ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def save_research_report(
    product_name: str,
    report: dict,
    markdown_report: str,
) -> dict:
    reports_dir = ensure_reports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = _slugify(product_name)
    base_name = f"{timestamp}_{safe_name}"

    json_path = reports_dir / f"{base_name}.json"
    md_path = reports_dir / f"{base_name}.md"

    payload = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "product_name": product_name,
        "report": report,
    }

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(markdown_report, encoding="utf-8")

    return {
        "base_name": base_name,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "saved_at": payload["saved_at"],
    }


def list_saved_reports(limit: int = 10) -> list[dict]:
    reports_dir = ensure_reports_dir()
    items = []

    for json_path in sorted(reports_dir.glob("*.json"), reverse=True):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        product_name = payload.get("product_name", json_path.stem)
        report = payload.get("report", {})
        md_path = json_path.with_suffix(".md")
        items.append(
            {
                "product_name": product_name,
                "saved_at": payload.get("saved_at", ""),
                "json_path": str(json_path),
                "markdown_path": str(md_path) if md_path.exists() else "",
                "summary": report.get("executive_summary", ""),
            }
        )

        if len(items) >= limit:
            break

    return items
