import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.pipeline import run_competitor_research
from core.reporting import build_markdown_report, build_pdf_report
from core.storage import list_saved_reports, save_research_report


def _format_feature_rows(rows):
    formatted = []
    for row in rows or []:
        current = dict(row)
        evidence = current.get("evidence", "")
        if evidence:
            current["evidence"] = evidence
        else:
            current["evidence"] = "unknown"
        formatted.append(current)
    return formatted

st.set_page_config(page_title="AI竞品调研助手", page_icon="🔎", layout="wide")

st.title("🔎 AI竞品调研助手")
st.caption("输入一个 AI 产品，我们会自动生成竞品名单、对比表和调研摘要。")

if "latest_saved_report" not in st.session_state:
    st.session_state.latest_saved_report = None

with st.sidebar:
    st.subheader("最近保存")
    saved_reports = list_saved_reports(limit=8)
    if saved_reports:
        for item in saved_reports:
            st.markdown(f"**{item['product_name']}**")
            if item.get("saved_at"):
                st.caption(item["saved_at"])
            if item.get("summary"):
                st.caption(item["summary"][:120])
            md_path = item.get("markdown_path", "")
            json_path = item.get("json_path", "")
            if md_path:
                st.markdown(
                    f"[Markdown]({Path(md_path).as_posix()})"
                )
            if json_path:
                st.markdown(
                    f"[JSON]({Path(json_path).as_posix()})"
                )
            st.divider()
    else:
        st.caption("还没有保存的调研记录。")

with st.form("research_form"):
    product_name = st.text_input("产品名", placeholder="例如：Perplexity")
    website = st.text_input("官网", placeholder="例如：https://www.perplexity.ai")
    description = st.text_area(
        "一句话描述",
        placeholder="例如：面向知识工作者的 AI 搜索与问答产品",
        height=100,
    )
    submitted = st.form_submit_button("开始调研")

if submitted:
    if not product_name.strip():
        st.error("请先输入产品名。")
    else:
        with st.spinner("正在识别赛道、寻找竞品并生成调研报告..."):
            report = run_competitor_research(
                product_name=product_name,
                website=website,
                description=description,
            )

        if report.get("error"):
            st.error(report["error"])
        else:
            overview = report.get("product_overview", {})
            competitors = report.get("competitors", [])
            feature_rows = _format_feature_rows(report.get("feature_comparison", []))
            pricing_rows = report.get("pricing_comparison", [])
            gaps = report.get("opportunity_gaps", [])
            risks = report.get("risks_and_unknowns", [])
            grouped_sources = report.get("grouped_sources", {})

            markdown_report = build_markdown_report(report)
            pdf_report = None
            pdf_error = ""
            try:
                pdf_report = build_pdf_report(report)
            except RuntimeError as exc:
                pdf_error = str(exc)

            st.subheader("产品画像")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**产品**：{overview.get('name', product_name)}")
                st.write(f"**赛道**：{overview.get('category', 'unknown')}")
                st.write(f"**定位**：{overview.get('positioning', 'unknown')}")
            with col2:
                target_users = overview.get("target_users", [])
                st.write(
                    f"**目标用户**：{', '.join(target_users) if target_users else 'unknown'}"
                )
                st.write(f"**官网**：{website or 'unknown'}")
            st.write(overview.get("summary", "暂无摘要。"))

            st.subheader("竞品推荐")
            if competitors:
                for index, competitor in enumerate(competitors, start=1):
                    st.markdown(
                        f"**{index}. {competitor.get('name', 'unknown')}**  "
                        f"{competitor.get('website', '')}\n\n"
                        f"{competitor.get('reason', '暂无说明')}"
                    )
            else:
                st.info("暂未识别到稳定的竞品结果。")

            st.subheader("高层结论")
            st.write(report.get("executive_summary", "暂无结论。"))
            st.caption("结论中的 `[S1]`、`[S2]` 等编号可在下方来源列表中追溯。")

            st.subheader("功能对比")
            if feature_rows:
                st.dataframe(pd.DataFrame(feature_rows), use_container_width=True)
                st.caption("功能对比表最后一列 `evidence` 对应支撑这行判断的来源编号。")
            else:
                st.info("暂无功能对比数据。")

            st.subheader("定价对比")
            if pricing_rows:
                st.dataframe(pd.DataFrame(pricing_rows), use_container_width=True)
            else:
                st.info("暂无定价对比数据。")

            st.subheader("机会点")
            if gaps:
                for item in gaps:
                    st.markdown(f"- {item}")
            else:
                st.info("暂无机会点分析。")

            st.subheader("风险与不确定项")
            if risks:
                for item in risks:
                    st.markdown(f"- {item}")
            else:
                st.info("暂无风险说明。")

            st.subheader("导出报告")
            export_col1, export_col2, export_col3 = st.columns(3)
            with export_col1:
                st.download_button(
                    label="下载 Markdown 报告",
                    data=markdown_report,
                    file_name=f"{product_name}_competitor_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with export_col2:
                if pdf_report:
                    st.download_button(
                        label="下载 PDF 报告",
                        data=pdf_report,
                        file_name=f"{product_name}_competitor_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        "下载 PDF 报告",
                        disabled=True,
                        use_container_width=True,
                    )
                    if pdf_error:
                        st.caption(pdf_error)
            with export_col3:
                if st.button("保存到本地", use_container_width=True):
                    saved_info = save_research_report(
                        product_name=product_name,
                        report=report,
                        markdown_report=markdown_report,
                    )
                    st.session_state.latest_saved_report = saved_info
                    st.rerun()

            latest_saved = st.session_state.latest_saved_report
            if latest_saved:
                st.success(
                    "已保存调研结果："
                    f" {latest_saved['base_name']}"
                )
                st.caption(f"JSON: {latest_saved['json_path']}")
                st.caption(f"Markdown: {latest_saved['markdown_path']}")

            st.subheader("来源")
            if grouped_sources:
                for group_name, items in grouped_sources.items():
                    with st.expander(f"{group_name}（{len(items)}）", expanded=group_name == "官网与官方页面"):
                        if items:
                            for source in items:
                                source_id = source.get("source_id", "?")
                                title = source.get("title", "未命名来源")
                                url = source.get("url", "")
                                snippet = source.get("snippet", "")
                                if url:
                                    st.markdown(f"- `[{source_id}]` [{title}]({url})")
                                else:
                                    st.markdown(f"- `[{source_id}]` {title}")
                                if snippet:
                                    st.caption(snippet[:220])
                        else:
                            st.caption("暂无来源。")
            else:
                st.info("暂无来源。")
