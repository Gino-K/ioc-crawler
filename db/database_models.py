import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Text,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# --- Verbindungstabellen fuer Viele-zu-Viele-Beziehungen ---

sighting_apt_association = Table('sighting_apt_association', Base.metadata,
    Column('sighting_id', Integer, ForeignKey('sightings.id'), primary_key=True),
    Column('apt_id', Integer, ForeignKey('apts.id'), primary_key=True)
)

sighting_country_association = Table('sighting_country_association', Base.metadata,
    Column('sighting_id', Integer, ForeignKey('sightings.id'), primary_key=True),
    Column('country_id', Integer, ForeignKey('countries.id'), primary_key=True)
)

sighting_cve_association = Table('sighting_cve_association', Base.metadata,
    Column('sighting_id', Integer, ForeignKey('sightings.id'), primary_key=True),
    Column('cve_id', Integer, ForeignKey('cves.id'), primary_key=True)
)

class IOC(Base):
    __tablename__ = 'iocs'
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    type = Column(String, nullable=False)
    first_seen_timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    sightings = relationship("Sighting", back_populates="ioc", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('value', 'type', name='_value_type_uc'),)

    def __repr__(self):
        return f"<IOC(value='{self.value}', type='{self.type}')>"


class Sighting(Base):
    __tablename__ = 'sightings'
    id = Column(Integer, primary_key=True)
    ioc_id = Column(Integer, ForeignKey('iocs.id'), nullable=False)
    source_article_url = Column(String, nullable=False)
    context_snippet = Column(Text)
    sighting_timestamp = Column(DateTime, nullable=False)
    saved_formats = Column(String)

    country_id = Column(Integer, ForeignKey('countries.id'))

    ioc = relationship("IOC", back_populates="sightings")
    apts = relationship("APT", secondary=sighting_apt_association, back_populates="sightings")
    countries = relationship("Country", secondary=sighting_country_association, back_populates="sightings")
    cves = relationship("CVE", secondary=sighting_cve_association, back_populates="sightings")


    def __repr__(self):
        return f"<Sighting(ioc_id={self.ioc_id}, url='{self.source_article_url}')>"


class APT(Base):
    __tablename__ = 'apts'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    mitre_id = Column(String, unique=True, nullable=True)
    aliases = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    sightings = relationship("Sighting", secondary=sighting_apt_association, back_populates="apts")

    def __repr__(self):
        return f"<APT(mitre_id='{self.mitre_id}', name='{self.name}')>"


class Country(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    continent_code = Column(String(2))
    iso2_code = Column(String(2), nullable=False, unique=True)
    iso3_code = Column(String(3))
    tld = Column(String)

    sightings = relationship("Sighting", secondary=sighting_country_association, back_populates="countries")


class CVE(Base):
    __tablename__ = 'cves'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    sightings = relationship("Sighting", secondary=sighting_cve_association, back_populates="cves")

    def __repr__(self):
        return f"<CVE(name='{self.name}')>"


class ArticleScanHistory(Base):
    __tablename__ = 'article_scan_history'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    last_scanned = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc),
                          onupdate=datetime.datetime.now(datetime.timezone.utc))

    def __repr__(self):
        return f"<ArticleScanHistory(url='{self.url}', last_scanned='{self.last_scanned}')>"


def setup_database(db_name="ioc_database.sqlite"):
    """Erstellt die SQLite-Datenbank und die Tabellen, falls sie nicht existieren."""
    engine = create_engine(f'sqlite:///{db_name}')
    Base.metadata.create_all(engine)
    print(f"Datenbank '{db_name}' und Tabellen erfolgreich initialisiert.")
    return engine