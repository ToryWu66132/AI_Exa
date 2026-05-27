from pprint import pprint

from core.pipeline import run_competitor_research


if __name__ == "__main__":
    while True:
        product_name = input("\n请输入产品名（q退出）： ").strip()
        if product_name.lower() == "q":
            break

        website = input("请输入官网（可留空）： ").strip()
        description = input("请输入一句话描述（可留空）： ").strip()

        report = run_competitor_research(
            product_name=product_name,
            website=website,
            description=description,
        )
        pprint(report)
