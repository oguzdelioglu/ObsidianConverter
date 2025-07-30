<p align="center">
  <img src="logo.png" alt="ObsidianConverter Logo" width="200"/>
</p>

<h1 align="center">ObsidianConverter</h1>

<p align="center">
  Ein leistungsstarkes Tool zur Umwandlung von Textdateien in gut strukturierte Obsidian-Notizen mit intelligenter Verlinkung, Tagging und Organisation.
</p>

<p align="center">
  <a href="README.md">🇬🇧 English</a> |
  <a href="README_TR.md">🇹🇷 Türkçe</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a> |
  <a href="README_ZH.md">🇨🇳 中文</a>
</p>

## Funktionen

- **Intelligente Inhaltsanalyse**: Nutzt LLMs, um natürliche Inhaltsabschnitte zu identifizieren und Informationen zu organisieren
- **Automatische Notizverknüpfung**: Erstellt Verbindungen zwischen verwandten Notizen mithilfe semantischer Ähnlichkeit
- **Rekursive Verzeichnisverarbeitung**: Verarbeitet alle Textdateien in einem Verzeichnis und seinen Unterverzeichnissen
- **Obsidian-optimierte Ausgabe**: Erstellt Dateien mit korrektem Frontmatter und Formatierung für Obsidian
- **Intelligente Tag-Generierung**: Schlägt relevante Tags basierend auf dem Notizinhalt vor
- **Inhaltliche Kategorisierung**: Organisiert Notizen in logischen Ordnern basierend auf Inhaltsthemen
- **Erweiterte Obsidian-Integration**: Unterstützung für Callouts, Dataview-Abfragen und Inhaltsverzeichnisse
- **Parallelverarbeitung**: Verarbeitet mehrere Dateien gleichzeitig für schnellere Konvertierung
- **Konfigurationssystem**: Anpassung des Verhaltens über YAML-Konfigurationsdateien
- **Statistik-Tracking**: Detaillierte Statistiken zum Konvertierungsprozess und zur Notizerstellung
- **Mehrere LLM-Unterstützung**: Funktioniert mit Ollama-, OpenAI- oder Anthropic-Modellen
- **Interaktiver Modus**: Überprüfen, bearbeiten und verfeinern von Notizen vor dem Speichern
- **Docker-Unterstützung**: Ausführung mit Docker und Docker Compose für einfaches Setup

## Anforderungen

- Python 3.8+
- Einer der folgenden LLM-Anbieter:
  - [Ollama](https://ollama.ai/) (Standard, lokaler LLM-Dienst)
  - OpenAI API-Schlüssel (für GPT-Modelle)
  - Anthropic API-Schlüssel (für Claude-Modelle)
- Erforderliche Python-Pakete (siehe `requirements.txt`)
- Docker (optional, für Container-Nutzung)

## Installation

### Methode 1: Entwickler-Setup
1. Klone dieses Repository
2. Erstelle eine virtuelle Umgebung: `python -m venv venv`
3. Aktiviere die Umgebung:
   - Unter macOS/Linux: `source venv/bin/activate`
   - Unter Windows: `venv\Scripts\activate`
4. Installiere im Entwicklungsmodus: `pip install -e .`

### Methode 2: Reguläre Installation
1. Klone dieses Repository
2. Führe aus: `pip install .`

### Methode 3: Docker-Installation
1. Baue das Docker-Image: `docker build -t obsidian-converter .`
2. Führe mit Docker aus: `docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output obsidian-converter`
3. Oder nutze Docker Compose: `docker-compose up`

Siehe [README_DOCKER.md](README_DOCKER.md) für detaillierte Docker-Anweisungen.

### Voraussetzungen
- Für Ollama: Stelle sicher, dass es installiert und mit dem erforderlichen Modell läuft (Standard: "mistral")
  - Installiere das Modell mit: `ollama pull mistral`
- Für OpenAI: Setze deinen API-Schlüssel über das Argument `--openai-key` oder die Umgebungsvariable `OPENAI_API_KEY`
- Für Anthropic: Setze deinen API-Schlüssel über das Argument `--anthropic-key` oder die Umgebungsvariable `ANTHROPIC_API_KEY`

## Verwendung

```bash
# Hilfe anzeigen
obsidian-converter --help

# Grundlegende Verwendung (verarbeitet alle .txt Dateien im txt/ Verzeichnis)
obsidian-converter

# Bestimmte Dateien verarbeiten
obsidian-converter files example.txt subdir/notes.txt

# Ausgabeverzeichnis bereinigen
obsidian-converter clean

# Alle generierten Notizen auflisten
obsidian-converter list

# Notizen einer bestimmten Kategorie auflisten
obsidian-converter list --category technical

# Konfigurationsdatei erstellen
obsidian-converter config --create --file my_config.yaml

# Aktuelle Konfiguration anzeigen
obsidian-converter config --file my_config.yaml

# Konfigurationsdatei verwenden
obsidian-converter --config my_config.yaml

# Benutzerdefinierte Verzeichnisse
obsidian-converter --input /path/to/input --output /path/to/output

# Parallelverarbeitung aktivieren
obsidian-converter --parallel --workers 4

# Ausgabeverzeichnis vor der Konvertierung bereinigen
obsidian-converter --clean

# Bestimmtes Modell verwenden
obsidian-converter --model llama2

# Ausführliche Protokollierung
obsidian-converter --verbose

# Interaktiver Überprüfungsmodus
obsidian-converter --interactive

# Editor für den interaktiven Modus angeben
obsidian-converter --interactive --editor vim

# Verschiedene LLM-Anbieter verwenden
obsidian-converter --provider ollama --model llama2
obsidian-converter --provider openai --model gpt-3.5-turbo --openai-key DEIN_API_SCHLÜSSEL
obsidian-converter --provider anthropic --model claude-3-sonnet-20240229 --anthropic-key DEIN_API_SCHLÜSSEL

# Alle Optionen kombiniert
obsidian-converter --input /path/to/input --output /path/to/output --model llama2 \
  --similarity 0.4 --max-links 10 --clean --verbose --parallel --workers 8 --interactive
```

## Konfiguration

Das Tool kann über Befehlszeilenargumente oder mit einer YAML-Konfigurationsdatei konfiguriert werden:

```bash
# Standardkonfigurationsdatei erstellen
obsidian-converter config --create --file my_config.yaml
```

Beispiel einer Konfigurationsdatei:

```yaml
# Kerneinstellungen
input_dir: txt
output_dir: vault
model: mistral

# LLM-Provider Einstellungen
provider: ollama      # ollama, openai oder anthropic
openai_api_key: null  # Dein OpenAI API-Schlüssel (oder Umgebungsvariable)
anthropic_api_key: null  # Dein Anthropic API-Schlüssel (oder Umgebungsvariable)
llm_temperature: 0.7  # Temperatur für LLM-Antworten

# Verarbeitungseinstellungen
similarity_threshold: 0.3
max_links: 5
use_cache: true
cache_file: .llm_cache.json

# Leistungseinstellungen
parallel_processing: true
max_workers: 4
chunk_size: 1000000  # 1MB-Chunks für große Dateien

# Obsidian-spezifische Einstellungen
obsidian_features:
  callouts: true
  dataview: true
  toc: true
  graph_metadata: true

# Dateimuster zum Ein-/Ausschließen
include_patterns:
  - '*.txt'
  - '*.md'
exclude_patterns:
  - '*.tmp'
  - '~*'
```

Du kannst diese Konfigurationsdatei verwenden mit:

```bash
obsidian-converter --config my_config.yaml
```

## Erweiterte Funktionen

### Statistiken und Berichte

Das Tool generiert Statistiken über den Konvertierungsprozess, einschließlich:

- Anzahl der verarbeiteten Dateien und erstellten Notizen
- Kategorien- und Tag-Verteilung
- Wort- und Zeichenanzahl
- LLM-Leistungsmetriken
- Verarbeitungszeit

Ein JSON-Bericht wird automatisch im `.stats`-Verzeichnis innerhalb deines Ausgabeordners gespeichert.

### Parallelverarbeitung

Für große Dokumentensammlungen kannst du die Parallelverarbeitung aktivieren, um die Konvertierung zu beschleunigen:

```bash
obsidian-converter --parallel --workers 4
```

### Speicheroptimierung

Große Dateien werden automatisch in Chunks verarbeitet, um den Speicherverbrauch zu reduzieren. Du kannst die Chunk-Größe in der Konfigurationsdatei anpassen.

### Benutzerdefinierte Dateimuster

Standardmäßig verarbeitet das Tool `.txt`-Dateien, aber du kannst die Muster in der Konfigurationsdatei anpassen:

```yaml
include_patterns:
  - '*.txt'  # Textdateien
  - '*.md'   # Markdown-Dateien
  - 'notes_*.log'  # Log-Dateien mit spezifischer Benennung
```

### Interaktiver Modus

Überprüfe und bearbeite jede Notiz vor dem Speichern mit dem interaktiven Modus:

```bash
obsidian-converter --interactive
```

Im interaktiven Modus kannst du:
- Notizen in deinem bevorzugten Texteditor bearbeiten
- Notizen verwerfen, die du nicht behalten möchtest
- Notizkategorien ändern
- Vollständigen Inhalt vor der Entscheidung anzeigen
- Metadaten und vorgeschlagene Links überprüfen

Um einen benutzerdefinierten Editor anzugeben (anstelle des Systemstandards):

```bash
obsidian-converter --interactive --editor vim
```

## Beispielausgabe

Für eine Textdatei mit gemischten Notizen wird ObsidianConverter mehrere gut strukturierte Markdown-Dateien erstellen:

```markdown
---
title: Projektplanung
date: 2023-06-15
tags: [planung, projektmanagement, workflow]
category: Arbeit
---

## Projektplanung

Hier ist der Inhalt zur Projektplanung, der extrahiert wurde...

## Verwandte Notizen
- [[Besprechungsnotizen - Q2 Review]]
- [[Methoden zur Aufgabenpriorisierung]]
```

## Funktionsweise

1. Liest alle `.txt`-Dateien aus dem Eingabeverzeichnis und seinen Unterverzeichnissen
2. Verwendet LLM, um Inhalte zu analysieren und in logische Abschnitte zu unterteilen
3. Erstellt geeignete Metadaten (Frontmatter) für jede Notiz
4. Stellt Verbindungen zwischen verwandten Notizen her
5. Organisiert Notizen in einer sauberen Ordnerstruktur
6. Generiert den vollständigen Obsidian-Vault

## Lizenz

MIT