from io import BytesIO

def _clean_list(items):
    cleaned = []
    for item in items or []:
        value = str(item).strip()
        if value:
            cleaned.append(value)
    return cleaned


def build_markdown_report(report: dict) -> str:
    overview = report.get("product_overview", {})
    competitors = report.get("competitors", [])
    feature_rows = report.get("feature_comparison", [])
    pricing_rows = report.get("pricing_comparison", [])
    gaps = _clean_list(report.get("opportunity_gaps", []))
    risks = _clean_list(report.get("risks_and_unknowns", []))
    grouped_sources = report.get("grouped_sources", {})

    lines = [
        f"# {overview.get('name', 'AI竞品调研报告')}",
        "",
        "## 执行摘要",
        report.get("executive_summary", "暂无结论。"),
        "",
        "## 产品画像",
        f"- 产品：{overview.get('name', 'unknown')}",
        f"- 赛道：{overview.get('category', 'unknown')}",
        f"- 定位：{overview.get('positioning', 'unknown')}",
        f"- 目标用户：{', '.join(overview.get('target_users', []) or ['unknown'])}",
        "",
        overview.get("summary", "暂无摘要。"),
        "",
        "## 竞品推荐",
    ]

    if competitors:
        for competitor in competitors:
            lines.append(
                f"- {competitor.get('name', 'unknown')} | "
                f"{competitor.get('website', 'unknown')} | "
                f"{competitor.get('reason', '暂无说明')}"
            )
    else:
        lines.append("- 暂无稳定竞品结果")

    lines.extend(["", "## 功能对比"])
    if feature_rows:
        headers = list(feature_rows[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in feature_rows:
            lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
        lines.append("")
        lines.append("功能对比中的 `evidence` 列用于标记支撑该行判断的来源编号。")
    else:
        lines.append("暂无功能对比数据。")

    lines.extend(["", "## 定价对比"])
    if pricing_rows:
        headers = list(pricing_rows[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in pricing_rows:
            lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    else:
        lines.append("暂无定价对比数据。")

    lines.extend(["", "## 机会点"])
    if gaps:
        for item in gaps:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无机会点分析")

    lines.extend(["", "## 风险与不确定项"])
    if risks:
        for item in risks:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无风险说明")

    lines.extend(["", "## 来源"])
    if grouped_sources:
        for group_name, items in grouped_sources.items():
            lines.append(f"### {group_name}")
            if items:
                for source in items:
                    lines.append(
                        f"- [{source.get('source_id', '?')}] {source.get('title', '未命名来源')} | "
                        f"{source.get('url', 'unknown')}"
                    )
            else:
                lines.append("- 暂无来源")
            lines.append("")
    else:
        lines.append("- 暂无来源")

    return "\n".join(lines).strip() + "\n"


def build_pdf_report(report: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "缺少 reportlab 依赖，暂时无法导出 PDF。请先运行 pip install reportlab。"
        ) from exc

    markdown_text = build_markdown_report(report)

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    normal.fontName = "STSong-Light"
    normal.leading = 16

    title = styles["Title"]
    title.fontName = "STSong-Light"

    story = []
    for index, block in enumerate(markdown_text.split("\n\n")):
        text = block.strip()
        if not text:
            continue

        style = normal
        if index == 0:
            style = title

        formatted = text.replace("\n", "<br/>")
        story.append(Paragraph(formatted, style))
        story.append(Spacer(1, 12))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(story)
    return buffer.getvalue()
