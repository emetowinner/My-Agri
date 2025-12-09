"""
Web scraping utilities for news aggregation
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
import time
import logging

logger = logging.getLogger(__name__)


class NewsScraper:
    """Scraper for finding and extracting news articles"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_google_news(self, keywords, country='', max_results=10):
        """
        Search Google News for articles matching keywords and country

        Args:
            keywords (str): Search keywords
            country (str): Country filter
            max_results (int): Maximum number of results to return

        Returns:
            list: List of dictionaries with 'title', 'url', 'source' keys
        """
        results = []

        try:
            # Build search query
            query = keywords
            if country:
                query += f" {country}"

            # Google News search URL
            search_url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Find article elements (Google News structure)
            articles = soup.find_all('article', limit=max_results)

            for article in articles:
                try:
                    # Extract title
                    title_elem = article.find('a', class_='gPFEn')
                    if not title_elem:
                        title_elem = article.find('h3') or article.find('h4')

                    title = title_elem.get_text(strip=True) if title_elem else ''

                    # Extract URL
                    link = title_elem.get('href', '') if title_elem else ''
                    if link.startswith('./'):
                        link = 'https://news.google.com' + link[1:]

                    # Extract source
                    source_elem = article.find('a', class_='wEwyrc')
                    source = source_elem.get_text(strip=True) if source_elem else 'Unknown'

                    if title and link:
                        # Try to get the actual article URL (not Google redirect)
                        actual_url = self._resolve_google_news_url(link)

                        results.append({
                            'title': title,
                            'url': actual_url or link,
                            'source': source
                        })

                except Exception as e:
                    logger.warning(f"Error extracting article: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching Google News: {e}")

        return results

    def _resolve_google_news_url(self, google_url):
        """Try to resolve the actual article URL from Google News redirect"""
        try:
            response = self.session.get(google_url, timeout=5, allow_redirects=True)
            return response.url
        except:
            return google_url

    def extract_article_content(self, url):
        """
        Extract main content from an article URL

        Args:
            url (str): Article URL

        Returns:
            dict: Dictionary with 'title', 'text', 'summary' keys
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                script.decompose()

            # Extract title
            title = ''
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract main content
            # Try common article containers
            article_selectors = [
                'article',
                '[class*="article"]',
                '[class*="content"]',
                '[class*="post"]',
                'main',
            ]

            content = None
            for selector in article_selectors:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                content = soup.find('body')

            # Extract paragraphs
            paragraphs = []
            if content:
                for p in content.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > 50:  # Only meaningful paragraphs
                        paragraphs.append(text)

            # Create 3-paragraph summary
            summary = self._create_summary(paragraphs)

            full_text = '\n\n'.join(paragraphs)

            return {
                'title': title,
                'text': full_text,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Error extracting article content from {url}: {e}")
            return {
                'title': '',
                'text': '',
                'summary': ''
            }

    def _create_summary(self, paragraphs, num_paragraphs=3):
        """Create a summary from paragraphs"""
        if not paragraphs:
            return "No content available."

        # Take first few meaningful paragraphs
        summary_paragraphs = []
        for p in paragraphs:
            if len(p) > 100:  # Only substantial paragraphs
                summary_paragraphs.append(p)
                if len(summary_paragraphs) >= num_paragraphs:
                    break

        # If we don't have enough, just take what we have
        if len(summary_paragraphs) < num_paragraphs:
            summary_paragraphs = paragraphs[:num_paragraphs]

        return '\n\n'.join(summary_paragraphs)

    def scrape_news_for_job(self, keywords, country, max_articles=20):
        """
        Complete scraping workflow for a crawl job

        Args:
            keywords (str): Keywords to search
            country (str): Country filter
            max_articles (int): Maximum articles to scrape

        Returns:
            list: List of article data dictionaries
        """
        articles_data = []

        # Search for news
        search_results = self.search_google_news(keywords, country, max_articles)

        logger.info(f"Found {len(search_results)} search results")

        # Extract content from each article
        for idx, result in enumerate(search_results):
            try:
                logger.info(f"Extracting article {idx + 1}/{len(search_results)}: {result['url']}")

                content = self.extract_article_content(result['url'])

                if content['summary']:
                    articles_data.append({
                        'title': content['title'] or result['title'],
                        'url': result['url'],
                        'summary': content['summary'],
                        'source_name': result['source'],
                        'keywords_matched': keywords,
                        'country': country,
                    })

                # Be polite - add delay between requests
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing article {result['url']}: {e}")
                continue

        return articles_data


def run_crawl_job(crawl_job):
    """
    Execute a crawl job and save articles

    Args:
        crawl_job: CrawlJob instance

    Returns:
        int: Number of articles found
    """
    from news.models import NewsArticle

    try:
        crawl_job.status = 'running'
        crawl_job.save()

        scraper = NewsScraper()
        articles_data = scraper.scrape_news_for_job(
            crawl_job.keywords,
            crawl_job.country,
            max_articles=20
        )

        # Save articles to database
        created_count = 0
        for article_data in articles_data:
            # Check if article already exists (by URL)
            if not NewsArticle.objects.filter(url=article_data['url']).exists():
                NewsArticle.objects.create(
                    **article_data,
                    crawl_job=crawl_job,
                    is_manual=False
                )
                created_count += 1

        crawl_job.articles_found = created_count
        crawl_job.mark_completed()

        logger.info(f"Crawl job {crawl_job.id} completed. Found {created_count} new articles.")

        return created_count

    except Exception as e:
        error_msg = f"Error running crawl job: {str(e)}"
        logger.error(error_msg)
        crawl_job.mark_failed(error_msg)
        return 0
