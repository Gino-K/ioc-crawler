import random
import time
import re
from concurrent.futures import ThreadPoolExecutor

from .base_processor import BaseProcessor
from ..common.http_client import HttpClient


class ContentExtractor(BaseProcessor):
    """
    Extrahiert parallel den sauberen Textinhalt von einer Liste von Artikel-URLs.
    Ersetzt die Logik aus module2.
    """

    def __init__(self):
        self.http_client = HttpClient()

    def _extract_worker(self, url: str, retries: int = 3, backoff_factor: int = 3) -> tuple[str, str | None]:
        """
        Worker-Funktion, die den Inhalt einer URL extrahiert und bereinigt.
        """
        time.sleep(random.uniform(0.5, 2.0))

        soup = None
        for attempt in range(retries):
            soup = self.http_client.get_soup(url)
            if soup:
                break

            if attempt < retries - 1:
                wait_time = backoff_factor * (2 ** attempt)
                print(
                    f"[{self.__class__.__name__}] Netzwerkfehler bei {url}. Warte {wait_time}s vor Versuch {attempt + 2}...")
                time.sleep(wait_time)

        if not soup:
            print(
                f"[{self.__class__.__name__}] FEHLER: Konnte Inhalt fuer {url} nach {retries} Netzwerk-Versuchen nicht abrufen.")
            return url, None

        main_content_element = None

        known_selectors = [
            'div.articlebody',
            'div.article-body',
            'div.story-content',
            'div.post-body',
            'div#article-content',
            'div.td-post-content'
        ]
        for selector in known_selectors:
            main_content_element = soup.select_one(selector)
            if main_content_element:
                print(f"[{self.__class__.__name__}] Spezifischen Container '{selector}' für {url} gefunden.")
                break

        if not main_content_element:
            main_content_element = soup.find('article') or soup.find('main')
            if main_content_element:
                print(
                    f"[{self.__class__.__name__}] Semantischen Container '{main_content_element.name}' für {url} gefunden.")

        if not main_content_element:
            keywords = ['article', 'content', 'post', 'news', 'story', 'main', 'body']
            candidate_containers = []
            for tag in soup.find_all(['div', 'section']):
                attributes_string = f"{tag.get('id', '')} {' '.join(tag.get('class', []))}".lower()
                if any(keyword in attributes_string for keyword in keywords):
                    candidate_containers.append(tag)
            if candidate_containers:
                main_content_element = max(candidate_containers, key=lambda t: len(t.get_text(strip=True)))
                if main_content_element:
                    print(f"[{self.__class__.__name__}] Fallback-Container per Keyword für {url} gefunden.")

        if main_content_element:
            for unwanted_tag in main_content_element.select(
                    'script, style, form, nav, footer, header, .ad, .advertisement, .author-box, .related-posts, .share, .tags, .cf.note-b'):
                unwanted_tag.decompose()

            text_blocks = [tag.get_text(separator=' ', strip=True) for tag in
                           main_content_element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'pre', 'code', 'table'])]
            clean_text = "\n".join(filter(None, text_blocks))
        else:
            print(
                f"[{self.__class__.__name__}] Kein spezifisches Hauptinhaltselement gefunden fuer {url}. Extrahiere Text aus dem gesamten Body.")
            clean_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

        if clean_text:
            final_text = re.sub(r'\s{2,}', ' ', clean_text).strip()
            if len(final_text) > 50:
                print(f"[{self.__class__.__name__}] Inhalt fuer {url} erfolgreich extrahiert.")
                return url, final_text
            else:
                print(
                    f"[{self.__class__.__name__}] Logik-Fehler: Inhalt fuer {url} abgerufen, aber Text ist zu kurz (<50 Zeichen).")
                return url, None
        else:
            print(f"[{self.__class__.__name__}] Logik-Fehler: Inhalt fuer {url} abgerufen, aber kein Text gefunden.")
            return url, None

    def process(self, urls: list[str]) -> dict:
        """Verarbeitet eine Liste von Artikel-URLs parallel."""
        print(f"\n[Prozessor 2] Starte Inhalts-Extraktion fuer {len(urls)} Artikel parallel...")

        article_data_map = {'urls': urls, 'texts': {}}
        successful_count = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_results = executor.map(self._extract_worker, urls)

            url_to_index = {url: i for i, url in enumerate(urls)}

            for url, content in future_results:
                if content:
                    idx = url_to_index[url]
                    article_data_map['texts'][idx] = content
                    successful_count += 1

        print(f"[Prozessor 2] Inhalts-Extraktion abgeschlossen. {successful_count} von {len(urls)} Texten extrahiert.")
        return article_data_map


