import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}


def _extract_links_from_html(soup, source_url):
    """
    Extrahiert Artikel-Links aus einem BeautifulSoup-Objekt mit einer flexiblen,
    Score-basierten Funktion.
    """
    article_links = set()
    source_domain = urlparse(source_url).netloc

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
            print(f"[Module 1] Hauptinhaltsbereich mit Selektor '{selector}' gefunden.")
            for area in content_areas:
                if area.name == 'a':
                    potential_links.append(area)
                else:
                    potential_links.extend(area.find_all('a', href=True))
            found_main_content = True

    if not found_main_content:
        print(
            "[Module 1] Konnte keinen spezifischen Inhaltsbereich finden. Durchsuche den gesamten 'body' als Fallback.")
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

        blacklist = [
            '/search', '/tag/', '/author/', '/login', '/signup', '/forums', '/forum/',
            '/legal/', '/glossary/', '/news-tip/', 'mailto:', 'tel:', '/about',
            '/offer/', '/deals/'
        ]
        if any(re.search(keyword, path, re.IGNORECASE) for keyword in blacklist):
            continue

        # *** FLEXIBLE SCORE-BASIERTE Funktion ***
        score = 0

        # Kriterium 1: Link-Text sieht aus wie eine Überschrift (gibt 2 Punkte)
        if len(link_text.split()) >= 4:
            score += 2
        elif len(link_text.split()) >= 3:
            score += 1

        # Kriterium 2: URL-Struktur sieht wie ein Artikel aus (gibt je 1 Punkt)
        if path.count('/') >= 3:
            score += 1
        if re.search(r'/\d{4}/\d{2}/', path) or path.endswith(('.html', '.htm')):
            score += 1
        if not path.endswith('/'):
            score += 1

        # Ein Link wird akzeptiert, wenn er eine Mindestpunktzahl erreicht
        # Das erlaubt z.B. einen Link mit kurzer URL aber langem Text, oder umgekehrt.
        if score >= 2:
            article_links.add(absolute_url)

    return sorted(list(article_links))


def get_article_links_from_source(source_url):
    """
    Sammelt Links zu einzelnen Artikeln von einer gegebenen Quell-URL.
    Die Quelle kann eine HTML-Webseite oder ein RSS-Feed sein.
    """
    print(f"[Module 1] Verarbeite Quelle: {source_url}")

    try:
        feed = feedparser.parse(source_url, agent=HEADERS['User-Agent'])
        if feed.entries:
            print(f"[Module 1] Quelle als RSS-Feed erkannt.")
            article_links = [entry.link for entry in feed.entries if hasattr(entry, 'link') and entry.link]
            if article_links:
                print(f"[Module 1] {len(article_links)} Links aus RSS-Feed extrahiert.")
                return sorted(list(set(article_links)))
            else:
                print(
                    f"[Module 1] RSS-Feed wurde geparst, aber es wurden keine gültigen Links in den Einträgen gefunden.")
    except Exception as e:
        print(f"[Module 1] Fehler beim Parsen von {source_url} als RSS-Feed: {e}")

    print(f"[Module 1] Versuche, {source_url} als HTML-Seite zu verarbeiten.")
    try:
        response = requests.get(source_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        article_links = _extract_links_from_html(soup, source_url)
        print(f"[Module 1] {len(article_links)} Links nach HTML-Verarbeitung von {source_url} extrahiert.")
        return article_links
    except requests.exceptions.RequestException as e:
        print(f"[Module 1] Fehler beim Abrufen der HTML-Seite {source_url}: {e}")
    except Exception as e:
        print(f"[Module 1] Unbekannter Fehler bei der HTML-Verarbeitung von {source_url}: {e}")

    return []