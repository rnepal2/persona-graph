import re
from typing import List, Optional, Set
from bs4 import BeautifulSoup, NavigableString

# --- Helper Function for Keyword Processing ---

def _get_keyword_parts(keyword: str) -> List[str]:
    """
    Splits a multi-word keyword into parts and escapes them for regex.
    Example: "Rabindra Nepal" -> ['Rabindra', 'Nepal']
    """
    # Split by whitespace and filter out any empty strings
    return [re.escape(part) for part in keyword.split() if part]

# --- Approach 1: Structure-Aware Extraction (html content) ---

def _extract_by_structure(
    html_content: str,
    keyword_parts: List[str],
    container_tags: Optional[List[str]] = None
) -> List[str]:
    """
    Extracts text from semantic containers (p, li, tr, etc.) that contain ALL
    of the specified keyword parts.
    """
    if not keyword_parts:
        return []
    if container_tags is None:
        container_tags = ['p', 'li', 'tr', 'div', 'article', 'section', 'h1', 'h2', 'h3', 'h4']
    soup = BeautifulSoup(html_content, 'html.parser')

    def contains_all_keywords(text_node: NavigableString) -> bool:
        if not isinstance(text_node, NavigableString):
            return False
        text_lower = text_node.lower()
        return all(re.search(r'\b' + part + r'\b', text_lower, re.IGNORECASE) for part in keyword_parts)
    text_nodes = soup.find_all(string=contains_all_keywords)

    relevant_chunks: Set[str] = set()
    for node in text_nodes:
        container = node.find_parent(container_tags)
        if container:
            chunk_text = container.get_text(separator=' ', strip=True)
            relevant_chunks.add(chunk_text)
    return list(relevant_chunks)


# --- Approach 2: Paragraph-Based Context Extraction (The "Good" Fallback) ---

def _extract_by_paragraphs(full_text: str, keyword_parts: List[str]) -> List[str]:
    """
    Extracts paragraphs from plain text that contain ALL of the keyword parts.
    This is a more robust fallback than word counting.
    """
    if not keyword_parts:
        return []

    # Split the text into paragraphs
    paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
    
    relevant_chunks = []
    for para in paragraphs:
        if all(re.search(r'\b' + part + r'\b', para, re.IGNORECASE) for part in keyword_parts):
            relevant_chunks.append(para)
    return relevant_chunks

# --- The Main Orchestrator Function ---

def extract_relevant_context(
    content: str,
    search_phrase: str,
    prefer_structure: bool = True
) -> str:
    """
    Extracts relevant text chunks containing a keyword from web content, formats
    them into a single string for an LLM, and handles multi-word keywords
    in any order.
    """
    keyword_parts = _get_keyword_parts(search_phrase)
    if not keyword_parts:
        print("Warning: Keyword is empty. Returning no context.")
        return ""
    
    is_html = content.strip().startswith('<') and content.strip().endswith('>')
    
    chunks: List[str] = []
    if prefer_structure and is_html:
        chunks = _extract_by_structure(content, keyword_parts)
        if not chunks:
            plain_text = BeautifulSoup(content, 'html.parser').get_text(separator='\n\n')
            chunks = _extract_by_paragraphs(plain_text, keyword_parts)
    else:
        if is_html:
            plain_text = BeautifulSoup(content, 'html.parser').get_text(separator='\n\n')
            chunks = _extract_by_paragraphs(plain_text, keyword_parts)
        else:
            chunks = _extract_by_paragraphs(content, keyword_parts)

    if not chunks:
        return ""

    formatted_chunks = [f"  <Chunk>{chunk}</Chunk>" for chunk in chunks]
    return "<SearchContext>\n" + "\n".join(formatted_chunks) + "\n</SearchContext>"