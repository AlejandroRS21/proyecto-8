# /// script
# requires-python = ">=3.10"
# dependencies = ["networkx"]
# ///
"""Construye y renderiza el Context Graph usando Graphviz dot.
Produce un layout jerárquico limpio, ideal para A4."""

import json
import os
import subprocess
from collections import defaultdict

import networkx as nx

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
DOT_PATH = os.path.join(OUTPUT_DIR, "graph.dot")
PNG_PATH = os.path.join(OUTPUT_DIR, "graph.png")


def load_triplets(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"Error parseando JSON: {filepath}")
            return []


def source_label(filepath):
    if "XV_legislatura" in filepath:
        return "XV legislatura"
    if "Tercer_Gobierno" in filepath:
        return "3er Gob. Sánchez"
    return os.path.splitext(os.path.basename(filepath))[0]


def source_nodes():
    return ["XV legislatura", "3er Gob. Sánchez"]


def select_hubs(G, max_nodes=22):
    """Selecciona max_nodes nodos: fuentes + top hubs.
    Filtra ruido (nodos muy cortos, self-loops)."""
    sources = set(source_nodes())
    degrees = dict(G.degree())

    # Identificar nodos ruidosos: muy cortos o autoproblemáticos
    noisy = {"turias", "Ciudadanos"}
    
    selected = set(sources & set(G.nodes))
    candidates = [(n, d) for n, d in degrees.items()
                  if n not in selected and n in G.nodes
                  and n not in noisy
                  and len(n) > 2]  # filtrar nodos de 1-2 chars
    candidates.sort(key=lambda x: -x[1])

    remaining = max_nodes - len(selected)
    for node, _ in candidates[:remaining]:
        selected.add(node)
    return selected


def build_graph():
    G = nx.DiGraph()
    files = [
        os.path.join(BASE, "..", "data/XV_legislatura_de_España.json"),
        os.path.join(BASE, "..", "data/Tercer_Gobierno_Sánchez.json"),
    ]
    for f in files:
        src = source_label(f)
        G.add_node(src)
        for item in load_triplets(f):
            s = item.get("sujeto", "").strip()
            p = item.get("predicado", "").strip()
            o = item.get("objeto", "").strip()
            if not s or not p or not o:
                continue
            G.add_node(s)
            G.add_node(o)
            G.add_edge(src, s, predicado="menciona")
            G.add_edge(s, o, predicado=p)
    return G


def escape_dot(text):
    """Escapa texto para DOT."""
    return (text
            .replace('"', '\\"')
            .replace('\n', ' ')
            .replace('\r', ''))


def write_dot(G, selected, output_path):
    """Escribe archivo .dot con los nodos seleccionados."""
    H = G.subgraph(selected).copy()
    sources = set(source_nodes())

    lines = []
    lines.append("digraph ContextGraph {")
    lines.append("  rankdir=TB;")            # Top-to-bottom → ideal para A4 vertical
    lines.append("  splines=true;")           # Curvas suaves
    lines.append("  nodesep=0.35;")           # Separación entre nodos
    lines.append("  ranksep=0.50;")           # Separación entre niveles
    lines.append("  concentrate=true;")       # Mergea aristas paralelas
    lines.append("  fontname=\"Helvetica\";")
    lines.append("  label=\"Context Graph — Política española\";")
    lines.append("  labelloc=t;")
    lines.append("  labeljust=l;")
    lines.append("  fontsize=20;")
    lines.append("  bgcolor=\"#FAFAFA\";")
    lines.append("  pad=0.3;")
    lines.append("")

    # Nodos fuente: color dorado, forma de rectángulo redondeado
    for node in H.nodes:
        if node in sources:
            lines.append(
                f'  "{escape_dot(node)}" ['
                f'fillcolor="#FFD166", style=filled, '
                f'fontsize=14, shape=box, penwidth=2.5, '
                f'color="#D4A017", fontname="Helvetica-Bold", '
                f'margin="0.15,0.10"];'
            )
        else:
            # Entidad normal
            length = len(node)
            if length > 30:
                fs = 9
            elif length > 20:
                fs = 10
            elif length > 12:
                fs = 11
            else:
                fs = 12
            lines.append(
                f'  "{escape_dot(node)}" ['
                f'fillcolor="#8ECAE6", style=filled, '
                f'fontsize={fs}, shape=box, penwidth=1.2, '
                f'color="#457B9D", fontname="Helvetica", '
                f'margin="0.12,0.08"];'
            )
    lines.append("")

    # Aristas
    edge_colors = {
        "menciona": "#8D99AE",
    }
    default_colors = [
        "#264653", "#2A9D8F", "#E76F51", "#6D597A",
        "#E63946", "#2B9348", "#0077B6", "#F4A261",
    ]

    for src, dst, data in H.edges(data=True):
        # Saltar self-loops
        if src == dst:
            continue
        pred = data.get("predicado", "relacion")
        color = edge_colors.get(pred, default_colors[hash(pred) % len(default_colors)])

        if pred == "menciona":
            lines.append(
                f'  "{escape_dot(src)}" -> "{escape_dot(dst)}" ['
                f'color="{color}", style=dashed, penwidth=0.8, '
                f'arrowsize=0.5];'
            )
        else:
            # Acortar label del predicado si es muy largo
            plabel = pred if len(pred) <= 18 else pred[:16] + "…"
            lines.append(
                f'  "{escape_dot(src)}" -> "{escape_dot(dst)}" ['
                f'color="{color}", penwidth=1.0, '
                f'fontsize=6, fontcolor="#555555", '
                f'label=" {escape_dot(plabel)} ", '
                f'arrowsize=0.6];'
            )

    lines.append("}")
    text = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"DOT escrito: {output_path} ({H.number_of_nodes()} nodos, {H.number_of_edges()} aristas)")
    return H


def render_dot(dot_path, png_path):
    """Renderiza .dot con neato (spring model) a PNG."""
    # neato produce el layout más limpio para grafos pequeños
    # Sin size constraint: el layout ocupa su tamaño natural
    # Lo padding y centrado lo maneja LaTeX con keepaspectratio
    cmd = [
        "neato", "-Tpng",
        "-Gdpi=250",
        "-Goverlap=false",
        "-Gsplines=true",
        "-Gbgcolor=\"#FAFAFA\"",
        "-Gpad=0.3",
        dot_path, "-o", png_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback a dot si neato falla
        print(f"neato falló, probando dot: {result.stderr}")
        cmd[0] = "dot"
        cmd.insert(2, "-Grankdir=TB")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error dot: {result.stderr}")
            return False
    print(f"PNG renderizado: {png_path}")
    return True


def main():
    print("Construyendo grafo completo...")
    G = build_graph()
    print(f"Grafo completo: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

    selected = select_hubs(G, max_nodes=22)
    print(f"Nodos seleccionados (hubs): {len(selected)}")

    H = write_dot(G, selected, DOT_PATH)
    render_dot(DOT_PATH, PNG_PATH)

    # Stats finales
    print(f"\nResumen:")
    print(f"  Nodos en visualización: {H.number_of_nodes()}")
    print(f"  Aristas en visualización: {H.number_of_edges()}")
    print(f"  Archivos: {DOT_PATH}, {PNG_PATH}")


if __name__ == "__main__":
    main()
