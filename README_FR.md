<p align="center">
  <img src="logo.png" alt="ObsidianConverter Logo" width="200"/>
</p>

<h1 align="center">ObsidianConverter</h1>

<p align="center">
  Un puissant utilitaire pour convertir des fichiers texte brut en notes Obsidian bien structurées avec liens intelligents, étiquetage et organisation.
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_TR.md">Türkçe</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_ZH.md">中文</a>
</p>

## Fonctionnalités

- **Analyse Intelligente du Contenu**: Utilise des LLM pour identifier les ruptures naturelles de contenu et organiser l'information
- **Liaison Automatique des Notes**: Crée des connexions entre les notes liées en utilisant la similarité sémantique
- **Traitement Récursif des Répertoires**: Traite tous les fichiers texte dans un répertoire et ses sous-répertoires
- **Sortie Optimisée pour Obsidian**: Crée des fichiers avec le frontmatter et le formatage appropriés pour Obsidian
- **Génération Intelligente d'Étiquettes**: Suggère des étiquettes pertinentes basées sur le contenu de la note
- **Catégorisation du Contenu**: Organise les notes dans des dossiers logiques basés sur les thèmes de contenu
- **Intégration Avancée avec Obsidian**: Prise en charge des callouts, des requêtes dataview et des tables des matières
- **Traitement Parallèle**: Traite plusieurs fichiers simultanément pour une conversion plus rapide
- **Système de Configuration**: Personnaliser le comportement via des fichiers de configuration YAML
- **Suivi des Statistiques**: Statistiques détaillées sur le processus de conversion et la création de notes
- **Support Multi-LLM**: Fonctionne avec les modèles Ollama, OpenAI ou Anthropic
- **Mode Interactif**: Réviser, éditer et affiner les notes avant de les sauvegarder
- **Support Docker**: Exécution avec Docker et Docker Compose pour une configuration facile

## Prérequis

- Python 3.8+
- L'un des fournisseurs LLM suivants :
  - [Ollama](https://ollama.ai/) (par défaut, service LLM local)
  - Clé API OpenAI (pour les modèles GPT)
  - Clé API Anthropic (pour les modèles Claude)
- Packages Python requis (voir `requirements.txt`)
- Docker (facultatif, pour utilisation conteneurisée)

## Installation

### Méthode 1: Installation pour le Développement
1. Cloner ce dépôt
2. Créer un environnement virtuel: `python -m venv venv`
3. Activer l'environnement:
   - Sur macOS/Linux: `source venv/bin/activate`
   - Sur Windows: `venv\Scripts\activate`
4. Installer en mode développement: `pip install -e .`

### Méthode 2: Installation Standard
1. Cloner ce dépôt
2. Exécuter: `pip install .`

### Méthode 3: Installation Docker
1. Construire l'image Docker: `docker build -t obsidian-converter .`
2. Exécuter avec Docker: `docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output obsidian-converter`
3. Ou utiliser Docker Compose: `docker-compose up`

Voir [README_DOCKER.md](README_DOCKER.md) pour des instructions Docker détaillées.

### Prérequis
- Pour Ollama : S'assurer qu'il est installé et fonctionne avec le modèle requis (par défaut : "mistral")
  - Installer le modèle avec : `ollama pull mistral`
- Pour OpenAI : Définir votre clé API via l'argument `--openai-key` ou la variable d'environnement `OPENAI_API_KEY`
- Pour Anthropic : Définir votre clé API via l'argument `--anthropic-key` ou la variable d'environnement `ANTHROPIC_API_KEY`

## Utilisation

```bash
# Afficher le message d'aide
obsidian-converter --help

# Utilisation basique (traite tous les fichiers .txt dans le répertoire txt/)
obsidian-converter

# Traiter des fichiers spécifiques
obsidian-converter files example.txt subdir/notes.txt

# Nettoyer le répertoire de sortie
obsidian-converter clean

# Lister toutes les notes générées
obsidian-converter list

# Lister les notes d'une catégorie spécifique
obsidian-converter list --category technical

# Créer un fichier de configuration
obsidian-converter config --create --file my_config.yaml

# Voir la configuration actuelle
obsidian-converter config --file my_config.yaml

# Utiliser un fichier de configuration
obsidian-converter --config my_config.yaml

# Répertoires personnalisés
obsidian-converter --input /path/to/input --output /path/to/output

# Activer le traitement parallèle
obsidian-converter --parallel --workers 4

# Nettoyer le répertoire de sortie avant la conversion
obsidian-converter --clean

# Utiliser un modèle spécifique
obsidian-converter --model llama2

# Journalisation détaillée
obsidian-converter --verbose

# Mode de révision interactive
obsidian-converter --interactive

# Spécifier l'éditeur pour le mode interactif
obsidian-converter --interactive --editor vim

# Utiliser différents fournisseurs LLM
obsidian-converter --provider ollama --model llama2
obsidian-converter --provider openai --model gpt-3.5-turbo --openai-key VOTRE_CLE_API
obsidian-converter --provider anthropic --model claude-3-sonnet-20240229 --anthropic-key VOTRE_CLE_API

# Toutes les options combinées
obsidian-converter --input /path/to/input --output /path/to/output --model llama2 \
  --similarity 0.4 --max-links 10 --clean --verbose --parallel --workers 8 --interactive
```

## Configuration

L'outil peut être configuré via des arguments de ligne de commande ou avec un fichier de configuration YAML :

```bash
# Créer un fichier de configuration par défaut
obsidian-converter config --create --file my_config.yaml
```

Exemple de fichier de configuration :

```yaml
# Paramètres de base
input_dir: txt
output_dir: vault
model: mistral

# Paramètres du fournisseur LLM
provider: ollama      # ollama, openai, ou anthropic
openai_api_key: null  # Votre clé API OpenAI (ou utilisez la variable d'environnement)
anthropic_api_key: null  # Votre clé API Anthropic (ou utilisez la variable d'environnement)
llm_temperature: 0.7  # Température pour les réponses LLM

# Paramètres de traitement
similarity_threshold: 0.3
max_links: 5
use_cache: true
cache_file: .llm_cache.json

# Paramètres de performance
parallel_processing: true
max_workers: 4
chunk_size: 1000000  # Fragments de 1MB pour les gros fichiers

# Paramètres spécifiques à Obsidian
obsidian_features:
  callouts: true
  dataview: true
  toc: true
  graph_metadata: true

# Modèles de fichiers à inclure/exclure
include_patterns:
  - '*.txt'
  - '*.md'
exclude_patterns:
  - '*.tmp'
  - '~*'
```

Vous pouvez utiliser ce fichier de configuration avec :

```bash
obsidian-converter --config my_config.yaml
```

## Fonctionnalités Avancées

### Statistiques et Rapports

L'outil génère des statistiques sur le processus de conversion, notamment :

- Nombre de fichiers traités et de notes créées
- Distribution des catégories et des étiquettes
- Nombre de mots et de caractères
- Métriques de performance LLM
- Temps de traitement

Un rapport JSON est automatiquement enregistré dans le répertoire `.stats` de votre dossier de sortie.

### Traitement Parallèle

Pour les grands ensembles de documents, activez le traitement parallèle pour accélérer la conversion :

```bash
obsidian-converter --parallel --workers 4
```

### Optimisation de la Mémoire

Les gros fichiers sont automatiquement traités par fragments pour réduire l'utilisation de la mémoire. Vous pouvez personnaliser la taille des fragments dans le fichier de configuration.

### Modèles de Fichiers Personnalisés

Par défaut, l'outil traite les fichiers `.txt`, mais vous pouvez personnaliser les modèles dans le fichier de configuration :

```yaml
include_patterns:
  - '*.txt'  # Fichiers texte
  - '*.md'   # Fichiers Markdown
  - 'notes_*.log'  # Fichiers journaux avec une nomenclature spécifique
```

### Mode Interactif

Révisez et modifiez chaque note avant de l'enregistrer avec le mode interactif :

```bash
obsidian-converter --interactive
```

En mode interactif, vous pouvez :
- Modifier les notes dans votre éditeur de texte préféré
- Supprimer les notes que vous ne souhaitez pas conserver
- Changer les catégories de notes
- Voir le contenu complet avant de décider
- Examiner les métadonnées et les liens suggérés

Pour spécifier un éditeur personnalisé (au lieu de celui par défaut du système) :

```bash
obsidian-converter --interactive --editor vim
```

## Exemple de Sortie

Pour un fichier texte contenant des notes mixtes, ObsidianConverter produira plusieurs fichiers markdown bien structurés :

```markdown
---
title: Planification de Projet
date: 2023-06-15
tags: [planification, gestion-projet, flux-travail]
category: Travail
---

## Planification de Projet

Voici le contenu sur la planification de projet qui a été extrait...

## Notes Connexes
- [[Notes de Réunion - Revue T2]]
- [[Méthodes de Priorisation des Tâches]]
```

## Comment Ça Fonctionne

1. Lit tous les fichiers `.txt` du répertoire d'entrée et de ses sous-répertoires
2. Utilise le LLM pour analyser et décomposer le contenu en sections logiques
3. Crée des métadonnées appropriées (frontmatter) pour chaque note
4. Établit des connexions entre les notes liées
5. Organise les notes dans une structure de dossiers propre
6. Génère le coffre Obsidian complet

## Licence

MIT