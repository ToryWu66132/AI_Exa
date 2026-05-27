import os

from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()

exa_api_key = os.getenv("EXA_API_KEY")
if not exa_api_key:
    raise ValueError("EXA_API_KEY 未配置，请检查 .env 文件")

exa = Exa(exa_api_key)


def _detect_source_type(url: str) -> str:
    lowered = url.lower()
    if "pricing" in lowered:
        return "pricing"
    if "review" in lowered or "g2.com" in lowered or "capterra" in lowered:
        return "review"
    if "docs" in lowered or "help" in lowered:
        return "documentation"
    return "web"


def search(query, num_results=5):
    response = exa.search(query, num_results=num_results)

    docs = []
    for result in response.results:
        url = getattr(result, "url", "") or ""
        docs.append(
            {
                "title": getattr(result, "title", "") or "",
                "url": url,
                "snippet": getattr(result, "snippet", "") or "",
                "text": getattr(result, "text", "") or getattr(result, "snippet", "") or "",
                "published_date": getattr(result, "published_date", "") or "",
                "source_type": _detect_source_type(url),
            }
        )

    return docs
