# Context Graph sobre política española

**Del sistema experto al Context Graph: extracción semántica, grafos de conocimiento y consultas trazables sobre la XV legislatura de España.**

---

## Resumen

Este proyecto implementa un pipeline completo que transforma páginas web no estructuradas (Wikipedia) en un **grafo de conocimiento** enriquecido con metadatos de procedencia, fecha de vigencia y nivel de confianza. El sistema permite responder preguntas directas y multi-hop con trazabilidad total a la fuente original.

**Dominio**: política española — XV legislatura de España y Tercer Gobierno de Pedro Sánchez.

---

## Estructura del repositorio

```
├── src/
│   ├── scrape.py            # Fase 1: obtención de datos (Jina Reader API)
│   ├── extract_cerebras.py  # Fase 2: extracción de tripletes semánticos (LLM)
│   ├── build_graph.py       # Fase 3a: construcción del grafo (NetworkX)
│   ├── build_graph_dot.py   # Fase 3b: visualización con Graphviz (neato)
│   └── qa_graph.py          # Fase 4: motor de consultas QA
│
├── data/                    # Datos extraídos (Markdown + JSON)
│
├── output/                  # Artefactos generados
│   ├── graph.png            # Visualización del grafo (22 hubs)
│   ├── graph.dot            # Archivo DOT intermedio
│   └── qa_output.txt        # Resultados de las consultas QA
│
├── informe/                 # Memoria académica
│   ├── informe_academico.tex
│   └── informe_academico.pdf
│
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

---

## Pipeline

| Fase | Script | Descripción |
|------|--------|-------------|
| 1 | `scrape.py` | Convierte páginas de Wikipedia a Markdown mediante la API de Jina Reader |
| 2 | `extract_cerebras.py` | Divide el texto en fragmentos con solapamiento y extrae tripletes (sujeto, predicado, objeto) usando Llama 3.1 8B en Cerebras |
| 3a | `build_graph.py` | Construye un grafo dirigido con NetworkX; cada arista conserva fuente, fecha y confianza |
| 3b | `build_graph_dot.py` | Selecciona los 22 hubs por grado de centralidad y renderiza con Graphviz neato |
| 4 | `qa_graph.py` | Ejecuta consultas directas y multi-hop sobre el grafo con trazabilidad paso a paso |

### Resultados numéricos

- **715 nodos**, **812 aristas** en el grafo completo
- **22 hubs** seleccionados para visualización (28 aristas)
- **3 consultas QA** verificadas (2 directas + 1 multi-hop)

---

## Consultas QA

| # | Pregunta | Tipo | Respuesta |
|---|----------|------|-----------|
| Q1 | ¿Cuándo comenzó la XV legislatura de España? | Directa | 17 de agosto de 2023 |
| Q2 | ¿Quién fue investido presidente del Gobierno? | Directa | Pedro Sánchez |
| Q3 | ¿Qué cargo se atribuye a Pedro Sánchez en la página del Tercer Gobierno? | Multi-hop | presidente del Gobierno |

Todas las respuestas incluyen cita de fuente y fecha de extracción.

---

## Reproducción

### Requisitos

```bash
# Dependencias Python
pip install -r requirements.txt

# Graphviz (para build_graph_dot.py)
sudo apt install graphviz   # Debian/Ubuntu
brew install graphviz       # macOS
```

### Ejecución (desde la raíz del proyecto)

```bash
# 1. Scraping
python3 src/scrape.py

# 2. Extracción de tripletes (requiere API key en .env)
python3 src/extract_cerebras.py

# 3. Construcción del grafo
python3 src/build_graph.py

# 4. Visualización
python3 src/build_graph_dot.py

# 5. Consultas QA
python3 src/qa_graph.py
```

> **Nota**: La extracción con LLM requiere una API key de [Cerebras](https://cloud.cerebras.ai/) almacenada en un archivo `.env` con el formato `CEREBRAS_API_KEY=sk-...`.

---

## Memoria académica

El documento `informe/informe_academico.pdf` (13 páginas) incluye:

1. Introducción con objetivos y descripción del dominio
2. Diagrama de arquitectura del pipeline
3. Código comentado de todos los scripts
4. Visualización del grafo
5. Resultados de las tres consultas QA
6. Discusión: Context Graph vs. RAG vectorial
7. Conclusiones y trabajo futuro
8. Referencias bibliográficas verificadas

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Ver el archivo `LICENSE`.
