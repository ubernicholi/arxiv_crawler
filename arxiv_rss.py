import json
import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import requests
from bs4 import BeautifulSoup
import re
from process_papers import TextGenerationHandler

@dataclass
class ArxivCategory:
    short_name: str
    long_name: str
    description: str
    main_category: str

class SubjectManager:
    def __init__(self, subjects_file: str = "parsed_arxiv_subjects.json"):
        self.subjects: Dict[str, ArxivCategory] = {}
        self.load_subjects(subjects_file)
        
    def load_subjects(self, file_path: str) -> None:
        """Load and parse arXiv subject categories."""
        try:
            with open(file_path, 'r') as f:
                subjects_data = json.load(f)
                
            for subject in subjects_data:
                cat = ArxivCategory(
                    short_name=subject['short_name'],
                    long_name=subject['long_name'],
                    description=subject.get('description', ''),
                    main_category=subject.get('main_category', '')
                )
                self.subjects[subject['short_name']] = cat
        except Exception as e:
            logging.error(f"Error loading subjects: {e}")
            raise

    def get_category_info(self, short_name: str) -> Optional[ArxivCategory]:
        """Get category information by short name."""
        return self.subjects.get(short_name)

    def get_categories_by_main(self, main_category: str) -> List[ArxivCategory]:
        """Get all categories within a main category."""
        return [cat for cat in self.subjects.values() 
                if cat.main_category.lower() == main_category.lower()]

class EnhancedArxivScraper:
    def __init__(self, subject_manager: SubjectManager):
        self.subject_manager = subject_manager
        self.base_url = "https://arxiv.org/list/{}/recent"
        self.abs_base_url = "https://arxiv.org/abs/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def _get_soup(self, url: str) -> BeautifulSoup:
        """Make request and return BeautifulSoup object."""
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    def _extract_paper_id(self, text: str) -> str:
        """Extract paper ID from arXiv identifier."""
        match = re.search(r'arXiv:(\d+\.\d+)', text)
        return match.group(1) if match else None

    def _get_paper_details(self, paper_id: str) -> Dict:
        """Fetch detailed paper information."""
        abs_url = f"{self.abs_base_url}{paper_id}"
        soup = self._get_soup(abs_url)
        
        # Get abstract
        abstract_elem = soup.find('blockquote', class_='abstract')
        abstract = abstract_elem.text.replace('Abstract:', '').strip() if abstract_elem else None
        
        # Get submission date
## TODO this doesnt work right,
        date_elem = soup.find('div', class_='submission-history')
        date = None
        if date_elem:
            date_match = re.search(r'\[(v1)\] (.*?) \(', date_elem.text)
            if date_match:
                date = date_match.group(2).strip()

        # Get categories
##TODO getting sub catagories doesnt work right
        categories = []
        cats_elem = soup.find('div', class_='subjects')
        if cats_elem:
            cat_links = cats_elem.find_all('a')
            categories = [link.text.strip() for link in cat_links]
        
        return {
            'abstract': abstract,
            'date': date,
            'categories': categories
        }
##TODO ppaper count again, possibly batches
    def get_papers_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Fetch papers from a specific category."""
        if category not in self.subject_manager.subjects:
            raise ValueError(f"Invalid category: {category}")
            
        url = self.base_url.format(category)
        soup = self._get_soup(url)
        papers = []
        
        entries = list(zip(soup.find_all('dt'), soup.find_all('dd')))
        
        for dt, dd in entries[:limit]:
            try:
                arxiv_link = dt.find('a', text=re.compile(r'arXiv:\d+\.\d+'))
                if not arxiv_link:
                    continue
                    
                paper_id = self._extract_paper_id(arxiv_link.text)
                title = dd.find('div', class_='list-title').text.replace('Title:', '').strip()
                authors_div = dd.find('div', class_='list-authors')
                authors = [a.text.strip() for a in authors_div.find_all('a')] if authors_div else []
                
                # Get detailed information
                details = self._get_paper_details(paper_id)
                
                paper_info = {
                    'id': paper_id,
                    'title': title,
                    'authors': authors,
                    'abstract': details['abstract'],
                    'date': details['date'],
                    'url': f"{self.abs_base_url}{paper_id}",
                    'primary_category': category,
                    'all_categories': details['categories']
                }
                
                papers.append(paper_info)
                time.sleep(1)  # Be nice to arXiv servers
                
            except Exception as e:
                logging.error(f"Error processing paper {paper_id if paper_id else 'unknown'}: {e}")
                continue
                
        return papers

class PaperFeedGenerator:
    def __init__(self, scraper: EnhancedArxivScraper, analyzer: 'TextGenerationHandler'):
        self.scraper = scraper
        self.analyzer = analyzer
        self.processed_ids: Set[str] = set()

##TODO this loop is bad, it should scrap and save to the JSON before sending/processing with the LLM  

##TODO a better way to pass number of papers to process
    def generate_daily_feed(self, categories: List[str], papers_per_category: int = 5) -> List[Dict]:
        """Generate a daily feed of papers from specified categories."""
        all_papers = []
        
        for category in categories:
            try:
                papers = self.scraper.get_papers_by_category(category, papers_per_category)
                
                # Filter out already processed papers
                new_papers = [p for p in papers if p['id'] not in self.processed_ids]
                
                for paper in new_papers:
                    # Add analysis
                    # this needs to be edited based on what LLM back end is used
                    prompt = self._create_paper_prompt(paper)
                    analysis_result = self.analyzer.generate_text(prompt)
                    
                    if analysis_result['success']:
                        paper['analysis'] = analysis_result['messages'][0]
                        paper['analysis_success'] = True
                    else:
                        paper['analysis'] = None
                        paper['analysis_success'] = False
                        
                    self.processed_ids.add(paper['id'])
                    all_papers.append(paper)
                    
            except Exception as e:
                logging.error(f"Error processing category {category}: {e}")
                continue
                
        return all_papers

    def _create_paper_prompt(self, paper: Dict) -> str:
        """Create analysis prompt for a paper."""
        return f"""Please analyze this research paper:

Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Categories: {', '.join(paper['all_categories'])}
Abstract: {paper['abstract']}

Please provide a technical analysis and explanation of this paper's significance."""


## TODO more rubust saving is needed
    def save_feed(self, papers: List[Dict], output_file: str = 'daily_paper_feed.json'):
        """Save the daily feed to a JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize components
    subject_manager = SubjectManager('parsed_arxiv_subjects.json')
    scraper = EnhancedArxivScraper(subject_manager)
    analyzer = TextGenerationHandler()
    feed_generator = PaperFeedGenerator(scraper, analyzer)
    
    # Configure categories to monitor
##TODO this is a PITA to deal with, the subjects JSON needs to be parsed to a more readable format
    ## so that this is easier to configure
    categories = ['cs.AI', 'cs.LG', 'cs.CL']  # Add more as needed
    
    # Generate daily feed
    papers = feed_generator.generate_daily_feed(categories)
    feed_generator.save_feed(papers)
    
    logging.info(f"Successfully processed {len(papers)} papers from {len(categories)} categories")

if __name__ == "__main__":
    main()
