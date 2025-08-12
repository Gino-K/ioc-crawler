from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database_models import Base


def _normalize_name(name: str) -> str:
    """Eine zentrale Funktion zur Normalisierung von Namen für Vergleiche."""
    if not name:
        return ""
    return name.lower().replace('-', '').replace(' ', '')


class DatabaseHandlerBase:
    """
    Die Basis-Klasse für Datenbank-Handler. Kümmert sich um die Verbindung
    und stellt generische Helfermethoden bereit.
    """

    def __init__(self, db_name="threat_intelligence.sqlite"):
        """
        Initialisiert die Datenbankverbindung. Findet den Projekt-Root dynamisch,
        um sicherzustellen, dass immer dieselbe Datenbankdatei verwendet wird.
        """

        def find_project_root(start_path):
            current_path = Path(start_path).resolve()
            while not (current_path / '.gitignore').exists():
                if current_path.parent == current_path: return None
                current_path = current_path.parent
            return current_path

        if db_name == ":memory:":
            db_connection_string = 'sqlite:///:memory:'
            print("[DB Handler] Erstelle eine In-Memory-Test-Datenbank.")
        else:
            project_root = find_project_root(__file__)
            if not project_root:
                print(
                    "[DB Handler] WARNUNG: .gitignore nicht gefunden. DB wird im aktuellen Arbeitsverzeichnis erstellt.")
                project_root = Path.cwd()

            db_path = project_root / db_name
            db_connection_string = f'sqlite:///{db_path}'
            print(f"[DB Handler] Verbinde zur zentralen Datenbank: {db_path}")

        self.engine = create_engine(db_connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_or_create(self, session, model, defaults=None, **kwargs):
        """
        Sucht ein Objekt. Wenn es nicht existiert, wird es mit den Suchkriterien
        und den optionalen 'defaults' erstellt.
        """
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            params = {**kwargs, **(defaults or {})}
            instance = model(**params)
            session.add(instance)
            session.flush()
            return instance

