# ArXiv Paper Analyzer

A Python-based tool for scraping and analyzing recent papers from arXiv.org using local LLM-powered analysis. The system fetches papers from specified categories, generates summaries and technical analysis, and saves the results.

## Features

- Scrapes recent papers from specified arXiv categories
- Local LLM-powered paper analysis (using KoboldCPP backend)
- Configurable paper processing pipeline
- JSON-based output for easy integration
- Support for multiple arXiv categories and subjects
- Rate-limiting to respect arXiv's servers

## Requirements

- Python 3.7+
- BeautifulSoup4 for web scraping
- Requests library
- Local KoboldCPP instance running (default: http://192.168.0.6:8051)
- Access to arXiv.org

## Configuration

### ArXiv Categories
Categories are loaded from `parsed_arxiv_subjects.json`. Default monitoring includes:
- cs.AI (Artificial Intelligence)
- cs.LG (Machine Learning)
- cs.CL (Computation and Language)

### LLM Configuration
The system uses KoboldCPP with Gemma-2 type models. Configuration is stored in `kobold_config.json` with parameters for:
- Context length
- Temperature
- Top-p sampling
- Response length
- Other generation parameters

## Usage

```python
# Initialize components
subject_manager = SubjectManager('parsed_arxiv_subjects.json')
scraper = EnhancedArxivScraper(subject_manager)
analyzer = TextGenerationHandler()
feed_generator = PaperFeedGenerator(scraper, analyzer)

# Generate daily feed
papers = feed_generator.generate_daily_feed(['cs.AI', 'cs.LG', 'cs.CL'])
feed_generator.save_feed(papers)
```

## Output Format

Papers are saved in JSON format with the following structure:
```json
{
    "id": "paper_id",
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "abstract": "Paper abstract...",
    "date": "Submission date",
    "url": "arXiv URL",
    "primary_category": "Main category",
    "all_categories": ["cat1", "cat2"],
    "analysis": "LLM-generated analysis"
}
```

# TODO List

## High Priority Fixes
1. Paper Count and Batching
   - [ ] Implement proper paper count tracking
   - [ ] Add batch processing capability
   - [ ] Add configurable batch size

2. Data Processing Flow
   - [ ] Separate scraping and LLM processing steps
   - [ ] Save raw scraped data before LLM processing
   - [ ] Implement retry mechanism for failed LLM analyses

3. Date Extraction Issues
   - [ ] Fix submission date extraction from arXiv pages
   - [ ] Add proper date parsing and formatting
   - [ ] Handle multiple versions of papers

4. Category Management
   - [ ] Fix sub-categories extraction
   - [ ] Improve category parsing from paper pages
   - [ ] Create readable format for category configuration

## General Improvements

5. Error Handling and Logging
   - [ ] Add comprehensive error handling
   - [ ] Implement proper logging system
   - [ ] Add error recovery mechanisms

6. Data Storage
   - [ ] Implement more robust saving mechanism
   - [ ] Add database support (optional)
   - [ ] Add incremental save capability

7. Configuration
   - [ ] Move hardcoded values to config file
   - [ ] Add CLI arguments for common parameters
   - [ ] Create example configuration files

8. Documentation
   - [ ] Add docstrings to all classes and methods
   - [ ] Create API documentation
   - [ ] Add usage examples

## Optional Enhancements

9. Features
   - [ ] Add support for different LLM backends
   - [ ] Implement paper similarity analysis
   - [ ] Add export formats (PDF, HTML)
   - [ ] Create web interface

10. Performance
    - [ ] Optimize scraping with async requests
    - [ ] Add caching mechanism
    - [ ] Implement parallel processing

## Notes
- The TODO items are based on the comments in the source code and apparent needs
- Priority should be given to fixing core functionality before adding new features
- Testing should be added throughout the improvement process