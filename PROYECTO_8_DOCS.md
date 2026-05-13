# Proyecto 8: Sistema Experto a Context Graph

Evolución AI: Reglas manuales → Knowledge Graph (KG) + LLM. 
KG estructurable. LLM razona. Context Graph = KG + meta (procedencia, vigencia). Fix alucinaciones LLM.

## Arquitectura / Fases

1. **Dominio**: Política España.
   - **Por qué**: Red compleja (Político → Partido → Ley). Roles cambian rápido (`validez` temporal clave). LLMs alucinan pactos/fechas.
   - **Objetivo**: QA Auditable. Cero sesgo AI. 100% trazabilidad a fuente (Congreso/BOE). Demostrar supremacía Context Graph vs RAG en data temporal.
2. **Scrape**: Obtener datos estructurables. `r.jina.ai` → Markdown (fácil para LLM).
   - **URLs elegidas (Wikipedia - rico en fechas/relaciones):**
     - `https://es.wikipedia.org/wiki/XV_legislatura_de_Espa%C3%B1a` (Pactos, fechas, partidos).
     - `https://es.wikipedia.org/wiki/Tercer_Gobierno_S%C3%A1nchez` (Ministros, carteras, nombramientos).
3. **Extracción (LLM)**: Prompt LLM para extraer triplets.
   - Core: Sujeto → Predicado → Objeto.
   - Meta obligatorios: `fuente` (URL), `fecha_extraccion`, `valido_desde`/`hasta` (opc), `confianza` (0-1).
4. **Construcción Grafo**: Cargar triplets en `networkx` (Python obj). Aristas guardan meta.
5. **Inferencia (Motor Query)**: 3 queries (mínimo 1 *multi-hop* / saltar nodos). LLM responde + cita URL y fecha exactas del grafo.
6. **Visualización**: Render 50-100 nodos.
7. **Documentación (PDF)**: 
   - Objetivos + Dominio. 
   - Arq diagrama. 
   - Scripts comentados. 
   - IMG grafo. 
   - 3 Q&A + citas. 
   - Context Graph vs RAG vectorial (opinión).

## Estado actual

- Scraping listo en `data/*.md`.
- Extracción lista en `data/*.json` con Cerebras + `llama3.1-8b`.
- Grafo reconstruido con nodos de fuente: 25 nodos, 25 aristas.
- Visualización generada en `graph.png`.
- QA verificado en `qa_graph.py`.

## Q&A del grafo

1. **¿Cuándo comenzó la XV legislatura de España?**
   - Respuesta: Comenzó el 17 de agosto de 2023.
   - Fuente: `https://es.wikipedia.org/wiki/XV_legislatura_de_Espa%C3%B1a`
   - Fecha de extracción: `2026-05-13`

2. **¿Quién fue investido presidente del Gobierno?**
   - Respuesta: Pedro Sánchez.
   - Fuente: `https://es.wikipedia.org/wiki/Tercer_Gobierno_S%C3%A1nchez`
   - Fecha de extracción: `2026-05-13`

3. **¿Qué cargo se atribuye a Pedro Sánchez en la página del Tercer Gobierno de Pedro Sánchez?**
   - Respuesta: presidente del Gobierno.
   - Ruta multi-hop:
     - `Tercer Gobierno de Pedro Sánchez` --menciona--> `Pedro Sánchez`
     - `Pedro Sánchez` --fue--> `investido presidente del Gobierno`
   - Fuente: `https://es.wikipedia.org/wiki/Tercer_Gobierno_S%C3%A1nchez`
   - Fecha de extracción: `2026-05-13`

## TODO inicial
- [x] Definir Dominio (Política España).
- [x] Definir URLs base (Wikipedia Legislatura/Gobierno).
- [x] Hacer script `scrape.py` para bajar MD con `r.jina.ai`.
- [x] Extraer triplets LLM (script `extract_cerebras.py` vía API Cerebras + modelo configurable).
- [x] Construir Grafo en `networkx` (`build_graph.py`).