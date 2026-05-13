# /// script
# requires-python = ">=3.10"
# dependencies = ["cerebras-cloud-sdk", "python-dotenv"]
# ///

import os
import json
import time
from datetime import datetime
import dotenv
from cerebras.cloud.sdk import Cerebras

# Cargar .env
dotenv.load_dotenv()

api_key = os.environ.get("CEREBRAS_API_KEY")
base_url = os.environ.get("CEREBRAS_BASE_URL")
MODEL = os.environ.get("CEREBRAS_MODEL", "llama3.1-8b")

if not api_key:
    raise RuntimeError("Falta CEREBRAS_API_KEY en .env")

client_kwargs = {"api_key": api_key}
if base_url:
    client_kwargs["base_url"] = base_url

client = Cerebras(**client_kwargs)


def chunk_text(text, chunk_size=5200, overlap=450):
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        if end >= text_length:
            break
        start = max(0, end - overlap)
    return chunks


def normalize_item(item, url, today):
    if not isinstance(item, dict):
        return None
    sujeto = item.get("sujeto")
    predicado = item.get("predicado")
    objeto = item.get("objeto")
    if not sujeto or not predicado or not objeto:
        return None
    return {
        "sujeto": str(sujeto).strip(),
        "predicado": str(predicado).strip(),
        "objeto": str(objeto).strip(),
        "fuente": url,
        "fecha_extraccion": today,
        "valido_desde": item.get("valido_desde"),
        "valido_hasta": item.get("valido_hasta"),
        "confianza": item.get("confianza", 0.0),
    }


def extract_triplets(text, url):
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""Extraer relaciones politicas como array JSON. 
Reglas:
- Cada item debe tener "sujeto", "predicado", "objeto" no nulos.
- Si el texto es definicional o copulativo, usa "es" como predicado y pon la definición en "objeto".
- Si no hay fecha clara, usa null en valido_desde/valido_hasta.
- Devolver SOLO JSON. Cero markdown.

Mapeo exacto de keys: "sujeto", "predicado", "objeto", "fuente" ("{url}"), "fecha_extraccion" ("{today}"), "valido_desde" (YYYY-MM-DD o null), "valido_hasta" (YYYY-MM-DD o null), "confianza" (0.0 a 1.0).

TEXTO:
{text[:8000]}
"""
    
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Eres extractor experto de Knowledge Graph. Responde SOLO con array JSON válido."},
            {"role": "user", "content": prompt}
        ],
        model=MODEL,
        max_completion_tokens=4096,
        temperature=0.0,
        top_p=1,
        stream=False
    )
    
    res = completion.choices[0].message.content.strip()
    
    # Limpiar markdown si Llama lo agrega
    if res.startswith("```json"):
        res = res[7:]
    elif res.startswith("```"):
        res = res[3:]
    if res.endswith("```"):
        res = res[:-3]
        
    return res.strip()


def extract_triplets_with_retry(text, url, max_attempts=4):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return extract_triplets(text, url)
        except Exception as exc:
            last_error = exc
            wait_seconds = min(20, 2 ** attempt)
            print(f"  Reintento {attempt}/{max_attempts} tras error: {exc}")
            if attempt < max_attempts:
                time.sleep(wait_seconds)
    raise last_error


def extract_triplets_from_chunks(text, url):
    today = datetime.now().strftime("%Y-%m-%d")
    aggregated = []
    seen = set()

    chunks = chunk_text(text)
    print(f"Chunks a procesar: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {index}/{len(chunks)}")
        raw = extract_triplets_with_retry(chunk, url)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"  Skip chunk {index}: JSON inválido ({exc})")
            continue

        if isinstance(parsed, dict):
            parsed = [parsed]

        for item in parsed:
            normalized = normalize_item(item, url, today)
            if not normalized:
                continue
            key = (
                normalized["sujeto"],
                normalized["predicado"],
                normalized["objeto"],
                normalized["fuente"],
            )
            if key in seen:
                continue
            seen.add(key)
            aggregated.append(normalized)

    return aggregated

def main():
    print(f"Usando modelo: {MODEL}")
    files = [
        ("data/XV_legislatura_de_España.md", "https://es.wikipedia.org/wiki/XV_legislatura_de_Espa%C3%B1a"),
        ("data/Tercer_Gobierno_Sánchez.md", "https://es.wikipedia.org/wiki/Tercer_Gobierno_S%C3%A1nchez")
    ]
    
    for relative_path, url in files:
        if not os.path.exists(relative_path):
            print(f"Skip → falta {relative_path}")
            continue
            
        with open(relative_path, "r", encoding="utf-8") as f:
            text = f.read()

        print(f"Extract (Cerebras Llama3.1) → {relative_path}...")
        try:
            triplets = extract_triplets_from_chunks(text, url)
        except Exception as exc:
            print(f"Error extrayendo {relative_path}: {exc}")
            continue
        
        out_path = relative_path.replace(".md", ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(triplets, f, ensure_ascii=False, indent=2)
            
        print(f"OK → {out_path} ({len(triplets)} triplets)")

if __name__ == "__main__":
    main()
