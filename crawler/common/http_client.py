import requests
from bs4 import BeautifulSoup

class HttpClient:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    @staticmethod
    def get_soup(url: str, timeout: int = 15) -> BeautifulSoup | None:
        """Fuehrt eine GET-Anfrage aus und gibt bei Erfolg ein BeautifulSoup-Objekt zurueck."""
        print(f"[HttpClient] Rufe auf: {url}")
        try:
            response = requests.get(url, headers=HttpClient.HEADERS, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"[HttpClient] Fehler beim Abrufen von {url}: {e}")
            return None