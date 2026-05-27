import json
import re
from typing import Any
from urllib.parse import urlparse

from llm.deepseek import DeepSeekLLM
from prompt.template import (
    build_competitor_discovery_prompt,
    build_product_profile_prompt,
    build_report_prompt,
)
from retrieval.web_search import search

llm = DeepSeekLLM()


def _extract_json(text: str, fallback: Any) -> Any:
    if not text:
        return fallback

    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    candidate = match.group(1) if match else text

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end < start:
        return fallback

    try:
        return json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return fallback


def _dedupe_sources(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = []
    seen = set()

    for item in items:
        url = item.get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(item)

    return deduped


def _assign_source_ids(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numbered = []
    for index, item in enumerate(items, start=1):
        current = dict(item)
        current["source_id"] = f"S{index}"
        numbered.append(current)
    return numbered


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _group_label(source_type: str) -> str:
    mapping = {
        "official": "官网与官方页面",
        "pricing": "定价与套餐",
        "review": "第三方评测",
        "documentation": "文档与帮助中心",
        "web": "其他网页来源",
    }
    return mapping.get(source_type, "其他网页来源")


def _group_sources(
    items: list[dict[str, Any]],
    official_domains: set[str],
) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "官网与官方页面": [],
        "定价与套餐": [],
        "第三方评测": [],
        "文档与帮助中心": [],
        "其他网页来源": [],
    }

    for item in items:
        current = dict(item)
        domain = _normalize_url(current.get("url", ""))
        if domain and domain in official_domains:
            current["source_type"] = "official"
        label = _group_label(current.get("source_type", "web"))
        groups[label].append(current)

    return groups


def _build_source_lookup(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        item.get("source_id", ""): item
        for item in items
        if item.get("source_id")
    }


def _attach_source_ids_to_evidence(
    evidence_map: list[dict[str, Any]],
    source_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    updated = []
    url_to_id = {
        source.get("url", ""): source_id
        for source_id, source in source_lookup.items()
        if source.get("url", "")
    }

    for item in evidence_map:
        current = dict(item)
        new_sources = []
        for source in current.get("sources", []):
            source_copy = dict(source)
            source_copy["source_id"] = url_to_id.get(source_copy.get("url", ""), "")
            new_sources.append(source_copy)
        current["sources"] = new_sources
        updated.append(current)

    return updated


def _normalize_citation_text(text: str) -> str:
    if not text:
        return text
    normalized = re.sub(r"\[(s\d+)\]", lambda m: f"[{m.group(1).upper()}]", text)
    normalized = re.sub(r"\((s\d+)\)", lambda m: f"[{m.group(1).upper()}]", normalized)
    return normalized


def _normalize_report_citations(report: dict[str, Any]) -> dict[str, Any]:
    report["executive_summary"] = _normalize_citation_text(
        report.get("executive_summary", "")
    )

    competitors = []
    for competitor in report.get("competitors", []):
        current = dict(competitor)
        current["reason"] = _normalize_citation_text(current.get("reason", ""))
        competitors.append(current)
    report["competitors"] = competitors

    report["opportunity_gaps"] = [
        _normalize_citation_text(item)
        for item in report.get("opportunity_gaps", [])
    ]
    report["risks_and_unknowns"] = [
        _normalize_citation_text(item)
        for item in report.get("risks_and_unknowns", [])
    ]

    feature_rows = []
    for row in report.get("feature_comparison", []):
        current = dict(row)
        current["evidence"] = _normalize_citation_text(current.get("evidence", ""))
        feature_rows.append(current)
    report["feature_comparison"] = feature_rows

    pricing_rows = []
    for row in report.get("pricing_comparison", []):
        current = dict(row)
        current["notes"] = _normalize_citation_text(current.get("notes", ""))
        pricing_rows.append(current)
    report["pricing_comparison"] = pricing_rows
    return report


def _normalize_feature_comparison(
    feature_rows: list[dict[str, Any]],
    target_name: str,
    competitors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    competitor_names = [
        competitor.get("name", f"竞品{i + 1}")
        for i, competitor in enumerate(competitors[:3])
    ]
    while len(competitor_names) < 3:
        competitor_names.append(f"竞品{len(competitor_names) + 1}")

    normalized = []
    aliases = {
        "feature": ["feature", "功能", "能力"],
        "target": ["target_product", "target", "我方产品", target_name],
        "comp1": ["competitor_1", competitor_names[0]],
        "comp2": ["competitor_2", competitor_names[1]],
        "comp3": ["competitor_3", competitor_names[2]],
        "evidence": ["evidence", "evidences", "sources", "source_ids", "citation"],
    }

    for row in feature_rows or []:
        normalized_row = {
            "feature": "unknown",
            target_name: "unknown",
            competitor_names[0]: "unknown",
            competitor_names[1]: "unknown",
            competitor_names[2]: "unknown",
            "evidence": "",
        }
        for key, value in row.items():
            key_text = str(key).strip()
            if key_text in aliases["feature"]:
                normalized_row["feature"] = value
            elif key_text in aliases["target"]:
                normalized_row[target_name] = value
            elif key_text in aliases["comp1"]:
                normalized_row[competitor_names[0]] = value
            elif key_text in aliases["comp2"]:
                normalized_row[competitor_names[1]] = value
            elif key_text in aliases["comp3"]:
                normalized_row[competitor_names[2]] = value
            elif key_text in aliases["evidence"]:
                normalized_row["evidence"] = value
        normalized.append(normalized_row)

    return normalized


def _normalize_pricing_comparison(
    pricing_rows: list[dict[str, Any]],
    target_name: str,
    competitors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_order = [target_name] + [
        competitor.get("name", "").strip()
        for competitor in competitors
        if competitor.get("name", "").strip()
    ]

    normalized_rows = []
    for row in pricing_rows or []:
        normalized_rows.append(
            {
                "product": row.get("product", "unknown"),
                "pricing": row.get("pricing", row.get("plan", "unknown")),
                "notes": row.get("notes", row.get("comment", "")),
            }
        )

    ranked = []
    for name in target_order:
        matched = next(
            (row for row in normalized_rows if row["product"].strip().lower() == name.lower()),
            None,
        )
        if matched:
            ranked.append(matched)

    for row in normalized_rows:
        if row not in ranked:
            ranked.append(row)

    return ranked


def _collect_competitor_sources(
    product_name: str,
    product_website: str,
    product_description: str,
    category: str,
) -> list[dict[str, Any]]:
    queries = [
        f"{product_name} alternatives",
        f"{product_name} competitors",
        f"best {category} tools" if category and category != "unknown" else "",
        (
            f"{product_description} software comparison"
            if product_description
            else ""
        ),
    ]

    raw_results = []
    for query in queries:
        if not query:
            continue
        raw_results.extend(search(query, num_results=5))

    if product_website:
        raw_results.insert(
            0,
            {
                "title": f"{product_name} official website",
                "url": product_website,
                "snippet": product_description,
                "text": product_description,
                "published_date": "",
                "source_type": "official",
            },
        )

    return _dedupe_sources(raw_results)[:12]


def _collect_product_sources(
    product_name: str,
    product_website: str,
    category: str,
) -> list[dict[str, Any]]:
    queries = [
        f"{product_name} official site",
        f"{product_name} pricing",
        f"{product_name} features",
        f"{product_name} review",
        f"{product_name} {category}" if category and category != "unknown" else "",
    ]

    results = []
    for query in queries:
        if not query:
            continue
        results.extend(search(query, num_results=4))

    if product_website:
        results.insert(
            0,
            {
                "title": f"{product_name} official website",
                "url": product_website,
                "snippet": "",
                "text": "",
                "published_date": "",
                "source_type": "official",
            },
        )

    return _dedupe_sources(results)[:10]


def _fallback_profile(
    product_name: str,
    product_website: str,
    product_description: str,
) -> dict[str, Any]:
    return {
        "product_name": product_name,
        "website": product_website or "unknown",
        "category": "unknown",
        "target_users": ["unknown"],
        "core_use_cases": [product_description or "unknown"],
        "search_keywords": [product_name, product_description or ""],
    }


def run_competitor_research(
    product_name: str,
    website: str = "",
    description: str = "",
) -> dict[str, Any]:
    if not product_name.strip():
        return {"error": "请输入产品名。"}

    profile_prompt = build_product_profile_prompt(
        product_name=product_name,
        website=website,
        description=description,
    )
    profile = _extract_json(
        llm.generate(profile_prompt),
        _fallback_profile(product_name, website, description),
    )

    category = profile.get("category", "unknown")

    competitor_sources = _collect_competitor_sources(
        product_name=product_name,
        product_website=website,
        product_description=description,
        category=category,
    )

    discovery_prompt = build_competitor_discovery_prompt(
        product_name=product_name,
        category=category,
        product_description=description,
        sources=competitor_sources,
    )
    discovery = _extract_json(
        llm.generate(discovery_prompt),
        {
            "competitors": [],
            "analysis_notes": "未能稳定识别竞品，请检查检索结果。",
        },
    )

    competitors = discovery.get("competitors", [])[:5]

    research_targets = [
        {"name": product_name, "website": website, "role": "target_product"}
    ]
    for competitor in competitors:
        research_targets.append(
            {
                "name": competitor.get("name", ""),
                "website": competitor.get("website", ""),
                "role": "competitor",
            }
        )

    evidence_map = []
    all_sources = []
    for target in research_targets:
        target_name = target.get("name", "").strip()
        if not target_name:
            continue
        sources = _collect_product_sources(
            product_name=target_name,
            product_website=target.get("website", ""),
            category=category,
        )
        evidence_map.append(
            {
                "name": target_name,
                "role": target.get("role", "competitor"),
                "website": target.get("website", ""),
                "sources": sources,
            }
        )
        all_sources.extend(sources)

    all_numbered_sources = _assign_source_ids(
        _dedupe_sources(all_sources + competitor_sources)
    )
    source_lookup = _build_source_lookup(all_numbered_sources)
    evidence_map = _attach_source_ids_to_evidence(evidence_map, source_lookup)

    report_prompt = build_report_prompt(
        product_name=product_name,
        website=website,
        description=description,
        profile=profile,
        competitor_discovery=discovery,
        evidence_map=evidence_map,
        source_catalog=all_numbered_sources,
    )
    report = _extract_json(
        llm.generate(report_prompt),
        {
            "product_overview": {
                "name": product_name,
                "category": category,
                "target_users": [],
                "positioning": "unknown",
                "summary": description or "unknown",
            },
            "competitors": competitors,
            "feature_comparison": [],
            "pricing_comparison": [],
            "opportunity_gaps": [],
            "risks_and_unknowns": ["模型未能输出完整报告，请查看原始来源。"],
            "executive_summary": "未能生成结构化报告。",
        },
    )

    official_domains = {
        _normalize_url(website),
        *{
            _normalize_url(item.get("website", ""))
            for item in competitors
        },
    }
    official_domains.discard("")

    report = _normalize_report_citations(report)
    report["feature_comparison"] = _normalize_feature_comparison(
        report.get("feature_comparison", []),
        product_name,
        competitors,
    )
    report["pricing_comparison"] = _normalize_pricing_comparison(
        report.get("pricing_comparison", []),
        product_name,
        competitors,
    )

    report["sources"] = all_numbered_sources
    report["grouped_sources"] = _group_sources(
        report["sources"],
        official_domains=official_domains,
    )
    report["evidence_map"] = evidence_map
    return report
