# /// script
# requires-python = ">=3.10"
# dependencies = ["networkx"]
# ///

import json
import os
from collections import deque

import networkx as nx

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILES = [
    os.path.join(BASE, "..", "data/XV_legislatura_de_España.json"),
    os.path.join(BASE, "..", "data/Tercer_Gobierno_Sánchez.json"),
]


def source_label(filepath):
    if "XV_legislatura_de_España" in filepath:
        return "XV legislatura de España"
    if "Tercer_Gobierno_Sánchez" in filepath:
        return "Tercer Gobierno de Pedro Sánchez"
    return os.path.splitext(os.path.basename(filepath))[0]


def load_graph():
    graph = nx.DiGraph()
    for path in DATA_FILES:
        if not os.path.exists(path):
            continue
        source_node = source_label(path)
        graph.add_node(source_node)
        with open(path, "r", encoding="utf-8") as file:
            items = json.load(file)
        for item in items:
            sujeto = item.get("sujeto")
            predicado = item.get("predicado")
            objeto = item.get("objeto")
            if not sujeto or not predicado or not objeto:
                continue
            graph.add_edge(
                source_node,
                sujeto,
                predicado="menciona",
                fuente=item.get("fuente", ""),
                fecha_extraccion=item.get("fecha_extraccion", ""),
            )
            graph.add_edge(
                sujeto,
                objeto,
                predicado=predicado,
                fuente=item.get("fuente", ""),
                fecha_extraccion=item.get("fecha_extraccion", ""),
            )
    return graph


def find_path(graph, start, goal):
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path
        for neighbor in graph.successors(node):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append((neighbor, path + [neighbor]))
    return None


def format_path(graph, path):
    lines = []
    for source, target in zip(path, path[1:]):
        edge = graph[source][target]
        lines.append(
            f"- {source} --{edge['predicado']}--> {target} | fuente: {edge['fuente']} | fecha_extraccion: {edge['fecha_extraccion']}"
        )
    return "\n".join(lines)


def answer_direct(graph, subject, predicate=None):
    for _, target, edge in graph.out_edges(subject, data=True):
        if predicate is None or edge.get("predicado") == predicate:
            return target, edge
    return None, None


def format_answer(prefix, value):
    if value.startswith("el ") or value.startswith("la "):
        return f"{prefix} {value}"
    return f"{prefix} {value}"


def main():
    graph = load_graph()
    print(f"Grafo QA: {graph.number_of_nodes()} nodos, {graph.number_of_edges()} aristas\n")

    # Q1 directa
    target, edge = answer_direct(graph, "XV legislatura de España", "comenzó")
    print("Q1: ¿Cuándo comenzó la XV legislatura de España?")
    if target:
        print(f"A: {format_answer('Comenzó', target)}")
        print(f"Cita: {edge['fuente']} | fecha_extraccion: {edge['fecha_extraccion']}\n")

    # Q2 directa
    target, edge = answer_direct(graph, "Pedro Sánchez", "fue investido")
    print("Q2: ¿Quién fue investido presidente del Gobierno?")
    if target:
        print("A: Pedro Sánchez")
        print(f"Cita: {edge['fuente']} | fecha_extraccion: {edge['fecha_extraccion']}\n")

    # Q3 multi-hop
    print("Q3: ¿Qué cargo se atribuye a Pedro Sánchez en la página del Tercer Gobierno de Pedro Sánchez?")
    path = find_path(graph, "Tercer Gobierno de Pedro Sánchez", "investido presidente del Gobierno")
    if path:
        print("A: presidente del Gobierno")
        print("Ruta:")
        print(format_path(graph, path))
        print()


if __name__ == "__main__":
    main()