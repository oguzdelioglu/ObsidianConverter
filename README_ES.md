<p align="center">
  <img src="logo.png" alt="ObsidianConverter Logo" width="200"/>
</p>

<h1 align="center">ObsidianConverter</h1>

<p align="center">
  Una poderosa utilidad para convertir archivos de texto plano en notas de Obsidian bien estructuradas con vinculación, etiquetado y organización inteligente.
</p>

<p align="center">
  <a href="README.md">🇬🇧 English</a> |
  <a href="README_TR.md">🇹🇷 Türkçe</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a> |
  <a href="README_ZH.md">🇨🇳 中文</a>
</p>

## Características

- **Análisis Inteligente de Contenido**: Utiliza LLMs para identificar divisiones naturales del contenido y organizar la información
- **Vinculación Automática de Notas**: Crea conexiones entre notas relacionadas utilizando similitud semántica
- **Procesamiento de Directorios Recursivo**: Procesa todos los archivos de texto en un directorio y sus subdirectorios
- **Salida Optimizada para Obsidian**: Crea archivos con el formato adecuado para Obsidian
- **Generación Inteligente de Etiquetas**: Sugiere etiquetas relevantes basadas en el contenido de la nota
- **Categorización de Contenido**: Organiza las notas en carpetas lógicas basadas en temas de contenido
- **Integración Mejorada con Obsidian**: Soporte para callouts, consultas dataview y tabla de contenidos
- **Procesamiento Paralelo**: Procesa múltiples archivos simultáneamente para una conversión más rápida
- **Sistema de Configuración**: Personaliza el comportamiento a través de archivos de configuración YAML
- **Seguimiento de Estadísticas**: Estadísticas detalladas sobre el proceso de conversión y creación de notas
- **Soporte para Múltiples LLM**: Funciona con modelos de Ollama, OpenAI o Anthropic
- **Modo Interactivo**: Revisa, edita y refina las notas antes de guardarlas
- **Soporte para Docker**: Ejecuta con Docker y Docker Compose para una configuración fácil

## Requisitos

- Python 3.8+
- Uno de los siguientes proveedores de LLM:
  - [Ollama](https://ollama.ai/) (predeterminado, servicio LLM local)
  - Clave API de OpenAI (para modelos GPT)
  - Clave API de Anthropic (para modelos Claude)
- Paquetes Python requeridos (ver `requirements.txt`)
- Docker (opcional, para uso en contenedores)

## Instalación

### Método 1: Configuración de Desarrollo
1. Clona este repositorio
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno:
   - En macOS/Linux: `source venv/bin/activate`
   - En Windows: `venv\Scripts\activate`
4. Instala en modo desarrollo: `pip install -e .`

### Método 2: Instalación Regular
1. Clona este repositorio
2. Ejecuta: `pip install .`

### Método 3: Instalación con Docker
1. Construye la imagen Docker: `docker build -t obsidian-converter .`
2. Ejecuta con Docker: `docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output obsidian-converter`
3. O usa Docker Compose: `docker-compose up`

Consulta [README_DOCKER.md](README_DOCKER.md) para instrucciones detalladas de Docker.

### Prerrequisitos
- Para Ollama: Asegúrate de que esté instalado y funcionando con el modelo requerido (predeterminado: "mistral")
  - Instala el modelo con: `ollama pull mistral`
- Para OpenAI: Configura tu clave API a través del argumento `--openai-key` o la variable de entorno `OPENAI_API_KEY`
- Para Anthropic: Configura tu clave API a través del argumento `--anthropic-key` o la variable de entorno `ANTHROPIC_API_KEY`

## Uso

```bash
# Mostrar mensaje de ayuda
obsidian-converter --help

# Uso básico (procesa todos los archivos .txt en el directorio txt/)
obsidian-converter

# Procesar archivos específicos
obsidian-converter files example.txt subdir/notes.txt

# Limpiar directorio de salida
obsidian-converter clean

# Listar todas las notas generadas
obsidian-converter list

# Listar notas de una categoría específica
obsidian-converter list --category technical

# Crear un archivo de configuración
obsidian-converter config --create --file my_config.yaml

# Ver configuración actual
obsidian-converter config --file my_config.yaml

# Usar un archivo de configuración
obsidian-converter --config my_config.yaml

# Directorios personalizados
obsidian-converter --input /path/to/input --output /path/to/output

# Habilitar procesamiento paralelo
obsidian-converter --parallel --workers 4

# Limpiar directorio de salida antes de la conversión
obsidian-converter --clean

# Usar un modelo específico
obsidian-converter --model llama2

# Registro detallado
obsidian-converter --verbose

# Modo de revisión interactiva
obsidian-converter --interactive

# Especificar editor para modo interactivo
obsidian-converter --interactive --editor vim

# Usar diferentes proveedores de LLM
obsidian-converter --provider ollama --model llama2
obsidian-converter --provider openai --model gpt-3.5-turbo --openai-key TU_CLAVE_API
obsidian-converter --provider anthropic --model claude-3-sonnet-20240229 --anthropic-key TU_CLAVE_API

# Todas las opciones combinadas
obsidian-converter --input /path/to/input --output /path/to/output --model llama2 \
  --similarity 0.4 --max-links 10 --clean --verbose --parallel --workers 8 --interactive
```

## Configuración

La herramienta se puede configurar a través de argumentos de línea de comando o con un archivo de configuración YAML:

```bash
# Crear un archivo de configuración predeterminado
obsidian-converter config --create --file my_config.yaml
```

Ejemplo de archivo de configuración:

```yaml
# Configuración básica
input_dir: txt
output_dir: vault
model: mistral

# Configuración del proveedor LLM
provider: ollama      # ollama, openai, o anthropic
openai_api_key: null  # Tu clave API de OpenAI (o usar variable de entorno)
anthropic_api_key: null  # Tu clave API de Anthropic (o usar variable de entorno)
llm_temperature: 0.7  # Temperatura para respuestas LLM

# Configuración de procesamiento
similarity_threshold: 0.3
max_links: 5
use_cache: true
cache_file: .llm_cache.json

# Configuración de rendimiento
parallel_processing: true
max_workers: 4
chunk_size: 1000000  # Fragmentos de 1MB para archivos grandes

# Configuración específica de Obsidian
obsidian_features:
  callouts: true
  dataview: true
  toc: true
  graph_metadata: true

# Patrones de archivos para incluir/excluir
include_patterns:
  - '*.txt'
  - '*.md'
exclude_patterns:
  - '*.tmp'
  - '~*'
```

Puedes usar este archivo de configuración con:

```bash
obsidian-converter --config my_config.yaml
```

## Características Avanzadas

### Estadísticas e Informes

La herramienta genera estadísticas sobre el proceso de conversión, incluyendo:

- Número de archivos procesados y notas creadas
- Distribución de categorías y etiquetas
- Recuentos de palabras y caracteres
- Métricas de rendimiento de LLM
- Tiempo de procesamiento

Un informe JSON se guarda automáticamente en el directorio `.stats` dentro de tu carpeta de salida.

### Procesamiento Paralelo

Para grandes conjuntos de documentos, habilita el procesamiento paralelo para acelerar la conversión:

```bash
obsidian-converter --parallel --workers 4
```

### Optimización de Memoria

Los archivos grandes se procesan automáticamente en fragmentos para reducir el uso de memoria. Puedes personalizar el tamaño de fragmento en el archivo de configuración.

### Patrones de Archivo Personalizados

Por defecto, la herramienta procesa archivos `.txt`, pero puedes personalizar los patrones en el archivo de configuración:

```yaml
include_patterns:
  - '*.txt'  # Archivos de texto
  - '*.md'   # Archivos Markdown
  - 'notes_*.log'  # Archivos de registro con nomenclatura específica
```

### Modo Interactivo

Revisa y edita cada nota antes de guardar con el modo interactivo:

```bash
obsidian-converter --interactive
```

En el modo interactivo, puedes:
- Editar notas en tu editor de texto preferido
- Descartar notas que no quieras conservar
- Cambiar categorías de notas
- Ver el contenido completo antes de decidir
- Revisar metadatos y enlaces sugeridos

Para especificar un editor personalizado (en lugar de usar el predeterminado del sistema):

```bash
obsidian-converter --interactive --editor vim
```

## Ejemplo de Salida

Para un archivo de texto que contiene notas mixtas, ObsidianConverter producirá múltiples archivos markdown bien estructurados:

```markdown
---
title: Planificación de Proyectos
date: 2023-06-15
tags: [planificación, gestión-de-proyectos, flujo-de-trabajo]
category: Trabajo
---

## Planificación de Proyectos

Aquí está el contenido sobre planificación de proyectos que fue extraído...

## Notas Relacionadas
- [[Notas de Reunión - Revisión Q2]]
- [[Métodos de Priorización de Tareas]]
```

## Cómo Funciona

1. Lee todos los archivos `.txt` del directorio de entrada y sus subdirectorios
2. Utiliza LLM para analizar y desglosar el contenido en secciones lógicas
3. Crea metadatos apropiados (frontmatter) para cada nota
4. Establece conexiones entre notas relacionadas
5. Organiza las notas en una estructura de carpetas limpia
6. Genera la bóveda completa de Obsidian

## Licencia

MIT