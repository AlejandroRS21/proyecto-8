# /// script
# requires-python = ">=3.10"
# dependencies = ["networkx", "matplotlib"]
# ///

import json
import os
from collections import defaultdict
import textwrap
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def load_triplets(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            print(f"Error parseando JSON: {filepath}")
            return []


def source_label(filepath):
    if "XV_legislatura_de_España" in filepath:
        return "XV legislatura de España"
    if "Tercer_Gobierno_Sánchez" in filepath:
        return "Tercer Gobierno de Pedro Sánchez"
    return os.path.splitext(os.path.basename(filepath))[0]


def source_nodes():
    return [
        "XV legislatura de España",
        "Tercer Gobierno de Pedro Sánchez",
    ]


def hierarchical_layout(graph, roots):
    levels = {}
    for root in roots:
        if root not in graph:
            continue
        lengths = nx.single_source_shortest_path_length(graph, root)
        for node, depth in lengths.items():
            if node not in levels or depth < levels[node]:
                levels[node] = depth

    fallback_level = (max(levels.values()) + 1) if levels else 0
    for node in graph.nodes:
        levels.setdefault(node, fallback_level)

    grouped = defaultdict(list)
    for node, level in levels.items():
        grouped[level].append(node)

    positions = {}
    for level, nodes in grouped.items():
        nodes = sorted(nodes)
        # Ancho visual estimado por nodo. Más largo el texto, más espacio horizontal.
        weights = []
        for node in nodes:
            label = display_label(node)
            plain_label = label.replace("\n", "")
            weights.append(max(7.0, len(plain_label) * 0.9))

        gap = 18.0
        total_width = sum(weights) + gap * max(len(nodes) - 1, 0)
        cursor = -total_width / 2
        for node, weight in zip(nodes, weights):
            cursor += weight / 2
            positions[node] = (cursor, -level * 3.8)
            cursor += weight / 2 + gap
    return positions


def display_label(text, width=18):
    if len(text) <= width:
        return text
    return textwrap.fill(text, width=width, break_long_words=False, break_on_hyphens=False)


def label_font_size(label):
    length = len(label.replace("\n", ""))
    if length <= 10:
        return 11
    if length <= 18:
        return 10
    if length <= 28:
        return 8
    return 7


def node_size(label):
    length = len(label.replace("\n", ""))
    return min(6200, 2800 + length * 115)


def edge_style(predicado):
    if predicado == "menciona":
        return {
            "color": "#8d99ae",
            "style": "dashed",
            "width": 0.9,
            "alpha": 0.45,
        }
    palette = ["#264653", "#2a9d8f", "#e76f51", "#6d597a", "#457b9d"]
    palette_index = sum(ord(char) for char in predicado) % len(palette)
    return {
        "color": palette[palette_index],
        "style": "solid",
        "width": 1.4,
        "alpha": 0.72,
    }


def draw_relationship_threads(graph, positions):
    source_counts = defaultdict(int)
    for source, target, data in graph.edges(data=True):
        if source not in positions or target not in positions:
            continue

        predicado = data.get("predicado", "")
        style = edge_style(predicado)
        source_counts[source] += 1
        slot = source_counts[source]
        slot_magnitude = ((slot + 1) // 2) * 0.18
        rad = slot_magnitude if slot % 2 else -slot_magnitude

        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=[(source, target)],
            edge_color=style["color"],
            style=style["style"],
            arrows=True,
            arrowsize=14,
            width=style["width"],
            alpha=style["alpha"],
            connectionstyle=f"arc3,rad={rad}",
        )

def build_graph():
    G = nx.DiGraph()
    files = ["../data/XV_legislatura_de_España.json", "../data/Tercer_Gobierno_Sánchez.json"]
    for f in files:
        source_node = source_label(f)
        G.add_node(source_node)
        for item in load_triplets(f):
            sujeto = item.get("sujeto")
            predicado = item.get("predicado")
            objeto = item.get("objeto")
            
            if not sujeto or not predicado or not objeto:
                continue
                
            G.add_node(sujeto)
            G.add_node(objeto)
            
            G.add_edge(source_node, sujeto, predicado="menciona", fuente=item.get("fuente", ""), fecha=item.get("fecha_extraccion", ""), validez=f'{item.get("valido_desde","")}-{item.get("valido_hasta","")}')
            G.add_edge(sujeto, objeto, 
                       predicado=predicado,
                       fuente=item.get("fuente", ""),
                       fecha=item.get("fecha_extraccion", ""),
                       validez=f'{item.get("valido_desde","")}-{item.get("valido_hasta","")}')
                   
    print(f"Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas.")
    return G

def select_hub_nodes(G, max_nodes=50):
    """Selecciona los max_nodes nodos más centrales (hub nodes) preservando fuentes."""
    sources = set(source_nodes())
    degrees = dict(G.degree())
    
    # Las fuentes siempre se incluyen
    selected = set(sources & set(G.nodes))
    
    # Los nodos fuente no fuente ordenados por grado descendente
    candidates = [(n, d) for n, d in degrees.items()
                  if n not in selected and n in G.nodes]
    candidates.sort(key=lambda x: -x[1])
    
    remaining = max_nodes - len(selected)
    for node, _ in candidates[:remaining]:
        selected.add(node)
    
    return selected


def vertical_a4_layout(G, selected_nodes, roots):
    """Layout vertical con proporción A4 exacta.
    
    Las coordenadas se normalizan a un espacio [0,1]×[0,1] que luego se
    mapea a las dimensiones exactas de la figura A4.
    """
    H = G.subgraph(selected_nodes).copy()
    
    # Calcular niveles desde fuentes
    levels = {}
    for root in roots:
        if root not in H:
            continue
        lengths = nx.single_source_shortest_path_length(H, root)
        for node, depth in lengths.items():
            if node not in levels or depth < levels[node]:
                levels[node] = depth

    max_level = max(levels.values()) if levels else 0
    for node in H.nodes:
        levels.setdefault(node, max_level + 1)

    n_levels = max(levels.values()) + 1
    
    # Espacio normalizado [0,1]×[0,1]
    # Dejamos 5% margen en cada borde
    margin = 0.06
    x0, x1 = margin, 1 - margin
    y0, y1 = margin, 1 - margin
    
    pos = {}
    for level in sorted(set(levels.values())):
        nodes_at_level = [n for n in H.nodes if levels[n] == level]
        if not nodes_at_level:
            continue
        nodes_at_level.sort(key=lambda n: -H.degree(n))
        
        n_nodes = len(nodes_at_level)
        if n_nodes <= 3:
            # Nodos muy centrales: más separados
            centro = node_width = 0.0
            for i, node in enumerate(nodes_at_level):
                x = x0 + (x1 - x0) * (i + 1) / (n_nodes + 1)
                pos[node] = (x, y1 - (level + 0.5) * (y1 - y0) / n_levels)
        else:
            # Nodos normales con espaciado justo
            # Comprimimos si hay muchos
            for i, node in enumerate(nodes_at_level):
                x = x0 + (x1 - x0) * (i + 1) / (n_nodes + 1)
                pos[node] = (x, y1 - (level + 0.5) * (y1 - y0) / n_levels)
    
    return pos, H, n_levels


def visualize_graph(G, max_nodes=35):
    if G.number_of_nodes() > max_nodes:
        selected = select_hub_nodes(G, max_nodes)
        pos, H, n_levels = vertical_a4_layout(G, selected, source_nodes())
    else:
        H = G
        n_levels = 0
        # fallback
        from itertools import cycle
        colors = cycle(["#ffd166", "#8ecae6"])
        pos = {n: (i % 5 * 0.2, -(i // 5) * 0.15) for i, n in enumerate(H.nodes)}
    
    # Dimensiones A4 exactas: 210×297mm → a 200dpi en pulgadas
    # Usamos pulgadas a 200dpi target: 8.27×11.69 in
    fig_width = 8.27
    fig_height = 11.69
    dpi = 200
    
    plt.figure(figsize=(fig_width, fig_height))
    
    # Tamaño de nodo en puntos de la figura, escalado para que se vean bien
    base_node_size = 2800
    node_sizes = []
    node_colors = []
    for node in H.nodes:
        is_source = node in source_nodes()
        node_colors.append("#ffd166" if is_source else "#8ecae6")
        label = display_label(node)
        length = len(label.replace("\n", ""))
        # Entre 2400 y 4000 pts² escalado por texto
        size = max(2400, min(4800, 2000 + length * 80))
        node_sizes.append(size)

    nx.draw_networkx_nodes(H, pos, node_color=node_colors, node_size=node_sizes,
                           alpha=0.92, linewidths=1.8, edgecolors="#2b2d42")
    draw_relationship_threads(H, pos)

    for node, (x, y) in pos.items():
        label = display_label(node)
        plt.text(
            x, y, label,
            fontsize=label_font_size(label) + 1,
            ha='center', va='center',
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=0.30,
                      boxstyle="round,pad=0.2"),
        )
    
    # Fijar límites exactos [0,1] para que las coordenadas normalizadas funcionen
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    legend_items = [
        Line2D([0], [0], color="#8d99ae", lw=1.6, linestyle="--", label="menciona"),
        Line2D([0], [0], color="#264653", lw=2.0, linestyle="-", label="relación semántica"),
    ]
    plt.legend(handles=legend_items, loc="upper left", frameon=False, fontsize=10)
    
    plt.title("Context Graph — Política española", fontsize=16, pad=15)
    plt.axis('off')
    # Ajuste exacto: ni un píxel de padding
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    os.makedirs("../output", exist_ok=True)
    plt.savefig("../output/graph_matplotlib.png", dpi=dpi, bbox_inches=None, pad_inches=0)
    print(f"Grafo guardado en ../output/graph_matplotlib.png ({fig_width}×{fig_height} in @ {dpi}dpi — A4 exacto)")

if __name__ == "__main__":
    G = build_graph()
    visualize_graph(G)
