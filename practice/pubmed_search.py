import requests

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def search_pubmed(query, days=365, max_results=5):
    # مرحله ۱: جستجو - شماره‌ی مقاله‌ها رو می‌گیره
    search = requests.get(
        BASE + "esearch.fcgi",
        params={
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "pub_date",
            "datetype": "pdat",
            "reldate": days,
        },
        timeout=30,
    )
    ids = search.json()["esearchresult"]["idlist"]

    if not ids:
        return []

    # مرحله ۲: خلاصه - اطلاعات هر مقاله رو می‌گیره
    summary = requests.get(
        BASE + "esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
        timeout=30,
    )
    data = summary.json()["result"]

    papers = []
    for pid in ids:
        item = data[pid]
        papers.append({
            "title": item["title"],
            "journal": item["fulljournalname"],
            "date": item["pubdate"],
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
        })
    return papers


if __name__ == "__main__":
    results = search_pubmed("social anxiety")
    for p in results:
        print(p["date"], "|", p["journal"])
        print("   ", p["title"])
        print("   ", p["link"])
        print()