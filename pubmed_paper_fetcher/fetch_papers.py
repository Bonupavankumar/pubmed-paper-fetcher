import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
from typing import List, Dict

# Define API URLs
SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Keywords to identify non-academic authors
COMPANY_KEYWORDS = [
    "pharma", "biotech", "inc", "ltd", "corporation", "gmbh", "s.a.", "pvt", 
    "therapeutics", "biopharma", "research lab", "biosciences", "biosystems", 
    "lifesciences", "genomics"
]

def fetch_pubmed_ids(query: str, max_results=10) -> List[str]:
    """Fetch PubMed IDs based on a search query."""
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results}
    response = requests.get(SEARCH_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])

def fetch_paper_details(pubmed_ids: List[str]) -> List[Dict]:
    """Fetch full details for given PubMed IDs using XML format."""
    if not pubmed_ids:
        return []
    
    params = {"db": "pubmed", "id": ",".join(pubmed_ids), "retmode": "xml"}
    response = requests.get(FETCH_URL, params=params)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    
    papers = []
    for article in root.findall(".//PubmedArticle"):
        pub_date = article.findtext(".//PubDate") or article.findtext(".//DateCompleted/Year", "Unknown")
        
        paper_data = {
            "uid": article.findtext(".//PMID"),
            "title": article.findtext(".//ArticleTitle"),
            "pubdate": pub_date,
            "authors": []
        }

        for author in article.findall(".//Author"):
            name = author.findtext("LastName", "") + " " + author.findtext("ForeName", "")
            affiliation = author.findtext(".//Affiliation", "Unknown")
            email = extract_email(affiliation)  # Extract email if present
            paper_data["authors"].append({"name": name, "affiliation": affiliation, "email": email})
        
        papers.append(paper_data)
    
    return papers

def extract_email(text: str) -> str:
    """Extracts email address from text if present."""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else "N/A"

def extract_indian_non_academic_authors(authors: List[Dict]) -> List[Dict]:
    """Filter authors affiliated with pharmaceutical or biotech companies in India."""
    if not isinstance(authors, list):
        return []  # Ensure authors list is valid

    non_academic_authors = []
    for author in authors:
        affiliation = author.get("affiliation", "").lower()
        if "india" in affiliation and any(keyword in affiliation for keyword in COMPANY_KEYWORDS):
            non_academic_authors.append({
                "name": author.get("name", "Unknown"),
                "company": affiliation,
                "email": author.get("email", "N/A"),
            })
    
    return non_academic_authors

def save_to_csv(papers: List[Dict], filename: str):
    """Save research paper data to a CSV file and verify output."""
    if not papers:
        print("⚠️ No valid papers found. Check API response or filtering.")
        return
    
    df = pd.DataFrame(papers)
    print(f"✅ Saving {len(df)} records to {filename}")
    print(df.head())  # Print first few rows before writing
    df.to_csv(filename, index=False)
