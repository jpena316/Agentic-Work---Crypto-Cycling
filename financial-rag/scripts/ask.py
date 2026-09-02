"""Interactive CLI for querying the financial RAG API's /ask endpoint."""

import argparse

import httpx

API_URL = "http://localhost:8002/ask"

TICKER_TO_COMPANY = {
    "VRT": "Vertiv Holdings Co",
    "SNOW": "Snowflake Inc.",
}


def ask(question: str, company: str | None) -> None:
    filters = {"company": company} if company else None
    payload: dict = {"question": question}
    if filters:
        payload["filters"] = filters

    response = httpx.post(API_URL, json=payload, timeout=60.0)
    response.raise_for_status()
    data = response.json()

    print()
    print(data["answer"])
    print()
    if data["citations"]:
        print("Sources:")
        for c in data["citations"]:
            print(f"  {c['marker']} {c['company']} | {c['doc_type']} | {c['fiscal_period']} | {c['section']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions against the financial RAG corpus.")
    parser.add_argument(
        "--company",
        default=None,
        help="Filter by company ticker, e.g. VRT or SNOW.",
    )
    args = parser.parse_args()

    company = None
    if args.company:
        company = TICKER_TO_COMPANY.get(args.company.upper(), args.company)

    print("Financial RAG CLI — type a question, Ctrl+C to exit.")
    if company:
        print(f"(filtering by company: {company})")

    try:
        while True:
            question = input("> ").strip()
            if not question:
                continue
            try:
                ask(question, company)
            except httpx.HTTPError as e:
                print(f"Error: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nBye.")


if __name__ == "__main__":
    main()
