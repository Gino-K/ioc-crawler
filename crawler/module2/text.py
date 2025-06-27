import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def _clean_text(text):
    """
    Bereinigt den extrahierten Text.
    - Entfernt überflüssige Leerzeilen.
    - Normalisiert Whitespace (mehrere Leerzeichen/Tabs zu einem Leerzeichen).
    """
    if not text:
        return ""

    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned_text = "\n".join(line for line in lines if line)
    return cleaned_text.strip()


def extract_and_clean_content(url: str) -> str | None:
    """
    Ruft den Inhalt einer Artikel-URL ab, extrahiert den Haupttext und bereinigt ihn
    mithilfe einer dynamischen, keyword-basierten Heuristik.
    """
    print(f"[Module 2] Verarbeite Artikel-URL: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Priorität: Suche nach semantischen Tags
        main_content_element = soup.find('article') or soup.find('main')
        if main_content_element:
            print("[Module 2] Hauptinhalt über semantisches Tag (<article> oder <main>) gefunden.")

        # 2. Priorität: Wenn nicht erfolgreich, suche dynamisch nach Schlüsselwörtern in IDs und Klassen
        if not main_content_element:
            print("[Module 2] Keine semantischen Tags gefunden. Starte dynamische Suche nach Keywords in class/id...")
            keywords = ['article', 'content', 'post', 'news', 'story', 'main', 'body']

            candidate_containers = []
            for tag in soup.find_all(['div', 'section']):
                attributes_string = f"{tag.get('id', '')} {' '.join(tag.get('class', []))}".lower()

                if any(keyword in attributes_string for keyword in keywords):
                    candidate_containers.append(tag)

            if candidate_containers:
                main_content_element = max(candidate_containers, key=lambda t: len(t.get_text(strip=True)))
                print(
                    f"[Module 2] Besten Content-Kandidaten basierend auf Textlänge gefunden: <{main_content_element.name} id='{main_content_element.get('id', '')}' class='{' '.join(main_content_element.get('class', []))}'>")

        # 3. Extrahiere den Text aus dem gefundenen Element
        if main_content_element:
            for unwanted_tag in main_content_element.select(
                    'script, style, form, nav, footer, header, .ad, .advertisement'):
                unwanted_tag.decompose()

            text_blocks = []
            for element in main_content_element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'pre', 'code', 'table']):
                text = element.get_text(separator=' ', strip=True)
                if text:
                    normalized_text = re.sub(r'\s+', ' ', text).strip()
                    text_blocks.append(normalized_text)

            clean_text = "\n".join(text_blocks)
        else:
            # Fallback, falls absolut nichts gefunden wurde
            print("[Module 2] Kein spezifisches Hauptinhaltselement gefunden. Extrahiere Text aus dem gesamten Body.")
            body_text = soup.body.get_text(separator='\n', strip=True)
            clean_text = body_text if body_text else ""

        if not clean_text:
            print(f"[Module 2] Kein Textinhalt extrahiert für {url} nach Bereinigung.")
            return None

        clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()

        print(f"[Module 2] Erfolgreich Text extrahiert und bereinigt für {url} (Länge: {len(clean_text)} Zeichen).")
        return clean_text

    except requests.exceptions.RequestException as e:
        print(f"[Module 2] Fehler beim Abrufen von {url}: {e}")
        return None
    except Exception as e:
        print(f"[Module 2] Unbekannter Fehler bei der Text-Extraktion von {url}: {e}")
        return None


def process_article_links(article_urls_list):
    """
    Verarbeitet eine Liste von Artikel-URLs und extrahiert für jede den Textinhalt.

    Args:
        article_urls_list (list): Eine Liste von Artikel-URLs.

    Returns:
        list: Eine Liste mit den extrahierten und bereinigten Textinhalten.
              Für URLs, bei denen die Extraktion fehlschlägt, enthält die Liste None.
    """
    all_extracted_texts = []
    if not article_urls_list:
        print("[Module 2] Keine Artikel-URLs zur Verarbeitung erhalten.")
        return all_extracted_texts

    print(f"\n[Module 2] Starte Inhalts-Extraktion für {len(article_urls_list)} Artikel-Links...")
    for i, url in enumerate(article_urls_list):
        print(f"[Module 2] --- Artikel {i + 1}/{len(article_urls_list)} ---")
        content = extract_and_clean_content(url)
        all_extracted_texts.append(content)  # content ist entweder der Text oder None

    print(
        f"[Module 2] Inhalts-Extraktion abgeschlossen. {sum(1 for t in all_extracted_texts if t is not None)} Texte erfolgreich extrahiert.")
    return all_extracted_texts