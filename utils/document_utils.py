#!/usr/bin/env python3
"""
Document extraction utilities for processing PDFs and web pages.
"""

import re
import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import pdfplumber
from datetime import datetime

from utils.logging_utils import setup_logging

# Initialize logger
logger = setup_logging(__name__)

class StudyMetadata:
    """Metadata about a scientific study."""
    def __init__(
        self,
        title: str,
        authors: List[str],
        publication: str,
        year: int,
        doi: Optional[str] = None,
        pmid: Optional[str] = None,
        study_type: Optional[str] = None,
        sample_size: Optional[int] = None
    ):
        self.title = title
        self.authors = authors
        self.publication = publication
        self.year = year
        self.doi = doi
        self.pmid = pmid
        self.study_type = study_type
        self.sample_size = sample_size
    
    def to_citation(self) -> str:
        """Format as a citation string."""
        authors_str = ", ".join(self.authors)
        return f"{authors_str} ({self.year}). {self.title}. {self.publication}."
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "authors": self.authors,
            "publication": self.publication,
            "year": self.year,
            "doi": self.doi,
            "pmid": self.pmid,
            "study_type": self.study_type,
            "sample_size": self.sample_size
        }


class PDFExtractor:
    """Extracts text from PDF files."""
    
    def extract_text(self, pdf_path: str) -> Tuple[str, Optional[StudyMetadata]]:
        """
        Extract text and metadata from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        text = ""
        metadata = None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata from first page
                first_page = pdf.pages[0]
                first_page_text = first_page.extract_text()
                
                # Try to extract metadata
                metadata = self._extract_metadata(first_page_text, pdf.metadata)
                
                # Extract text from all pages
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return "", None
    
    def _extract_metadata(self, first_page_text: str, pdf_metadata: Dict) -> Optional[StudyMetadata]:
        """Extract study metadata from PDF first page and metadata."""
        # Default values
        title = ""
        authors = []
        publication = ""
        year = 2000
        doi = None
        
        # Try to extract title (usually first line or pdf title)
        if pdf_metadata and "title" in pdf_metadata and pdf_metadata["title"]:
            title = pdf_metadata["title"]
        else:
            # Try first line of first page
            lines = first_page_text.split('\n')
            if lines:
                title = lines[0]
        
        # Try to extract authors
        author_line = ""
        for line in first_page_text.split('\n')[:10]:  # Check first 10 lines
            if "," in line and not line.startswith("Abstract") and not line.startswith("Keywords"):
                author_line = line
                break
        
        if author_line:
            # Simple heuristic: split by commas and "and"
            author_parts = re.split(r',|\sand\s', author_line)
            authors = [part.strip() for part in author_parts if part.strip()]
        
        # Try to extract year
        year_match = re.search(r'(19|20)\d{2}', first_page_text[:1000])
        if year_match:
            try:
                year = int(year_match.group(0))
            except ValueError:
                pass
        
        # Try to extract DOI
        doi_match = re.search(r'doi:?\s*([^\s]+)', first_page_text, re.IGNORECASE)
        if doi_match:
            doi = doi_match.group(1)
        
        # Try to extract publication
        publication_indicators = ["journal", "proceedings", "conference", "volume", "issue"]
        for line in first_page_text.split('\n')[:20]:  # Check first 20 lines
            if any(indicator in line.lower() for indicator in publication_indicators):
                publication = line.strip()
                break
        
        if title and year:
            return StudyMetadata(
                title=title,
                authors=authors,
                publication=publication,
                year=year,
                doi=doi
            )
        
        return None


class WebPageExtractor:
    """Extracts text from web pages."""
    
    def extract_text(self, url: str) -> Tuple[str, Optional[StudyMetadata]]:
        """
        Extract text and metadata from a web page.
        
        Args:
            url: URL of web page
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            headers = {
                "User-Agent": "NutritionalPsychiatryDatabase/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Extract text
            text = soup.get_text()
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Try to extract metadata
            metadata = self._extract_metadata(soup, url)
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from web page {url}: {e}")
            return "", None
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Optional[StudyMetadata]:
        """Extract study metadata from web page."""
        # Try to extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text
        
        # Try meta tags
        meta_title = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'title'})
        if meta_title and 'content' in meta_title.attrs:
            title = meta_title['content']
        
        # Try to extract authors
        authors = []
        author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
        if author_meta and 'content' in author_meta.attrs:
            authors = [author.strip() for author in author_meta['content'].split(',')]
        
        # Try to extract publication
        publication = ""
        site_name = soup.find('meta', {'property': 'og:site_name'})
        if site_name and 'content' in site_name.attrs:
            publication = site_name['content']
        
        # Try to extract year
        year = datetime.now().year
        pub_date = soup.find('meta', {'property': 'article:published_time'}) or soup.find('meta', {'name': 'date'})
        if pub_date and 'content' in pub_date.attrs:
            try:
                year_match = re.search(r'(19|20)\d{2}', pub_date['content'])
                if year_match:
                    year = int(year_match.group(0))
            except (ValueError, TypeError):
                pass
        
        # Try to extract DOI
        doi = None
        doi_link = soup.find('a', href=re.compile(r'doi.org'))
        if doi_link:
            doi_match = re.search(r'doi.org/([^/\s]+/[^/\s]+)', doi_link['href'])
            if doi_match:
                doi = doi_match.group(1)
        
        if title:
            return StudyMetadata(
                title=title,
                authors=authors,
                publication=publication or url,
                year=year,
                doi=doi
            )
        
        return None