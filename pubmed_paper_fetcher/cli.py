import argparse
from fetch_papers import fetch_pubmed_ids, fetch_paper_details, extract_indian_non_academic_authors, save_to_csv

def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed research papers and filter them.")
    parser.add_argument("query", type=str, help="Search query for PubMed")
    parser.add_argument("-f", "--file", type=str, help="Filename to save the results", default="output.csv")
    parser.add_argument("-m", "--max", type=int, help="Max number of results to fetch", default=20)
    args = parser.parse_args()

    print(f"🔍 Searching for papers related to: {args.query}")

    # Fetch paper IDs
    pmids = fetch_pubmed_ids(args.query, args.max)
    if not pmids:
        print("⚠️ No papers found for the given query.")
        return
    
    print(f"📄 Found PubMed IDs: {pmids}")

    # Fetch paper details
    papers = fetch_paper_details(pmids)

    # Process and filter papers
    results = []
    for paper in papers:
        authors = paper.get("authors", [])  # Ensure authors is a list
        indian_non_academic_authors = extract_indian_non_academic_authors(authors)

        if indian_non_academic_authors:
            results.append({
                "PubmedID": paper.get("uid", ""),
                "Title": paper.get("title", ""),
                "Publication Date": paper.get("pubdate", ""),
                "Non-academic Author(s)": ", ".join([auth["name"] for auth in indian_non_academic_authors]),
                "Company Affiliation(s)": ", ".join([auth["company"] for auth in indian_non_academic_authors]),
                "Corresponding Author Email": indian_non_academic_authors[0].get("email", "N/A"),
            })

    # Save results to CSV
    save_to_csv(results, args.file)

if __name__ == "__main__":
    main()
