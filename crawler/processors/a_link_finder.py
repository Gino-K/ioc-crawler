import feedparser
import re
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor

from .base_processor import BaseProcessor
from ..common.http_client import HttpClient
from db.crawler_db_handler import CrawlerDBHandler
from settings.user_settings import UserSettings
import datetime


def filter_links_by_timestamp(all_links_from_source, scan_history_map, days_to_rescan=5):
    links_to_process = []
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    rescan_threshold = now_utc - datetime.timedelta(days=days_to_rescan)
    for link in all_links_from_source:
        if link not in scan_history_map:
            links_to_process.append(link)
        else:
            timestamp_from_db = scan_history_map[link]
            if timestamp_from_db:
                aware_last_seen = timestamp_from_db.replace(tzinfo=datetime.timezone.utc)
                if aware_last_seen < rescan_threshold:
                    links_to_process.append(link)
    return links_to_process


class LinkFinder(BaseProcessor):
    INTERNAL_BLACKLIST = [
        '/search', '/tag/', '/author/', '/login', '/signup', '/forums', '/forum/',
        '/legal/', '/glossary/', '/news-tip/', 'mailto:', 'tel:', '/about',
        '/offer/', '/deals/', '/deals', '/categories'
    ]

    def __init__(self, settings: UserSettings, db_handler: CrawlerDBHandler):
        self.settings = settings
        self.db_handler = db_handler
        self.http_client = HttpClient()

    def _extract_links_from_html(self, soup, source_url: str) -> list[str]:
        """
        Extrahiert Artikel-Links aus einem BeautifulSoup-Objekt mit einer flexiblen,
        Score-basierten Funktion.
        """
        article_links = set()
        source_domain = urlparse(source_url).netloc

        full_blacklist = self.INTERNAL_BLACKLIST + self.settings.blacklist_keywords

        content_selectors = [
            'article', 'main', 'div#main-col', 'div.bc_latest_news', 'div#content',
            'div.content', 'div#main', 'div.main-content', 'div.posts',
            'div.body-post', 'section.post-content', 'a.story-link'
        ]

        potential_links = []
        found_main_content = False
        for selector in content_selectors:
            content_areas = soup.select(selector)
            if content_areas:
                for area in content_areas:
                    potential_links.extend(area.find_all('a', href=True))
                found_main_content = True

        if not found_main_content:
            potential_links = soup.find_all('a', href=True)

        for link_tag in potential_links:
            href = link_tag.get('href')
            if not href or href.strip() in ['#', '/']:
                continue

            absolute_url = urljoin(source_url, href)
            parsed_url = urlparse(absolute_url)

            if parsed_url.netloc != source_domain or parsed_url.fragment:
                continue

            path = parsed_url.path
            link_text = link_tag.get_text(strip=True)

            if not path or not link_text:
                continue

            if any(re.search(keyword, path, re.IGNORECASE) for keyword in full_blacklist):
                continue

            score = 0
            if len(link_text.split()) >= 4:
                score += 2
            elif len(link_text.split()) >= 3:
                score += 1
            if path.count('/') >= 3: score += 1
            if re.search(r'/\d{4}/\d{2}/', path) or path.endswith(('.html', '.htm')): score += 1
            if not path.endswith('/'): score += 1

            if score >= 3:
                article_links.add(absolute_url)

        return sorted(list(article_links))

    def _process_source(self, source_url: str) -> list:
        """Verarbeitet eine einzelne Quell-URL (RSS oder HTML)."""
        feed = feedparser.parse(source_url, agent=self.http_client.HEADERS['User-Agent'])
        if feed.entries:
            links = [entry.link for entry in feed.entries if hasattr(entry, 'link') and entry.link]
            if links:
                print(f"[LinkFinder] {len(links)} Links aus RSS-Feed ({source_url}) extrahiert.")
                return links

        soup = self.http_client.get_soup(source_url)
        if soup:
            links = self._extract_links_from_html(soup, source_url)
            print(f"[LinkFinder] {len(links)} Links aus HTML ({source_url}) extrahiert.")
            return links

        return []

    def process(self, source_urls: list[str]) -> list[str]:
        print(f"\n[Prozessor 1] Starte Link-Suche fuer {len(source_urls)} Quellen parallel...")
        all_found_links = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_results = executor.map(self._process_source, source_urls)
            for result_list in future_results:
                all_found_links.extend(result_list)

        unique_links = sorted(list(set(all_found_links)))
        print(f"[Prozessor 1] {len(unique_links)} einzigartige Links gefunden. Filtere gegen DB-Historie...")

        scan_history = self.db_handler.get_article_scan_history("")  # Holt die komplette Historie
        links_to_process = filter_links_by_timestamp(unique_links, scan_history)

        print(f"[Prozessor 1] Link-Suche abgeschlossen. {len(links_to_process)} Links zur Verarbeitung ausgewaehlt.")
        return links_to_process