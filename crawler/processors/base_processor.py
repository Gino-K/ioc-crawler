from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    """Abstrakte Basisklasse fuer einen Schritt in der Crawler-Pipeline."""
    @abstractmethod
    def process(self, data):
        """Verarbeitet die Eingabedaten und gibt das Ergebnis fuer den nächsten Schritt zurueck."""
        pass