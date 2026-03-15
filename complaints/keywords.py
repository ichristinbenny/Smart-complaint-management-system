"""
Load keywords from complaint dataset CSV for department prediction.
Keywords are extracted from complaint_text for each department.
"""
import csv
import os
import re
from collections import Counter, defaultdict
from django.conf import settings

# Map CSV department names to DB search terms (for flexible matching)
CSV_TO_DB_TERMS = {
    'Road & Infrastructure': ['Road', 'Infrastructure'],
    'Water Supply': ['Water'],
    'Electricity & Streetlights': ['Electricity', 'Streetlight'],
    'Garbage & Sanitation': ['Garbage', 'Sanitation'],
    'Public Safety': ['Public Safety', 'Safety'],
}

# Common words to exclude (minimal stopwords)
_STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
    'not', 'only', 'own', 'same', 'than', 'too', 'very', 'this', 'that',
    'these', 'those', 'it', 'its', 'no', 'our', 'their', 'my', 'your',
}

_KEYWORDS_CACHE = None


def _tokenize(text):
    """Extract lowercased words of length >= 3 from text."""
    text = (text or '').lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    return [w for w in words if w not in _STOPWORDS]


def _load_keywords_from_csv():
    """Load complaint dataset CSV and build department -> keywords mapping."""
    csv_path = os.path.join(settings.BASE_DIR, 'complaint dataset.csv')
    if not os.path.exists(csv_path):
        return {}

    dept_words = defaultdict(list)  # department -> list of all words from its complaints

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'complaint_text' not in reader.fieldnames or 'department' not in reader.fieldnames:
            return {}

        for row in reader:
            dept = (row.get('department') or '').strip()
            text = row.get('complaint_text', '')
            if not dept or not text:
                continue
            words = _tokenize(text)
            dept_words[dept].extend(words)

    # For each department: keep words that appear at least 2 times
    dept_keywords = {}
    for dept, words in dept_words.items():
        counts = Counter(words)
        keywords = [w for w, c in counts.most_common(50) if c >= 2]
        if not keywords:
            # Fallback: take top 30 by frequency
            keywords = [w for w, _ in counts.most_common(30)]
        dept_keywords[dept] = set(keywords) if keywords else set()

    return dept_keywords


def get_keyword_map():
    """Return department -> set of keywords. Cached after first load."""
    global _KEYWORDS_CACHE
    if _KEYWORDS_CACHE is None:
        _KEYWORDS_CACHE = _load_keywords_from_csv()
    return _KEYWORDS_CACHE


def match_department_by_keywords(description):
    """
    Match description to a department using keywords from the dataset.
    Returns the first DB search term (str) that may match a Department, or None.
    """
    keywords_map = get_keyword_map()
    if not keywords_map:
        return None

    desc_words = set(_tokenize(description))
    if not desc_words:
        return None

    best_dept = None
    best_score = 0

    for dept, keywords in keywords_map.items():
        matches = len(desc_words & keywords)
        if matches > best_score:
            best_score = matches
            best_dept = dept

    if best_score == 0:
        return None

    # Map CSV department name to DB-friendly search terms
    terms = CSV_TO_DB_TERMS.get(best_dept, [best_dept])
    return terms[0] if terms else best_dept
