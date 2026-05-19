# algoritmos de grafos usados en el proyecto
# se trabaja con dijkstra para encontrar rutas mas cortas

import time


try:
    import networkx as nx

    NETWORKX_DISPONIBLE = True
except ImportError:
    NETWORKX_DISPONIBLE = False


def dijkstra(grafo, origen, destino):
    # esta funcion calcula la ruta mas corta entre dos nodos del grafo
    if grafo is None:
        print("no hay grafo cargado.")
        return [], float("inf"), 0

    if not NETWORKX_DISPONIBLE:
        print("networkx no esta instalado.")
        return [], float("inf"), 0

    inicio = time.perf_counter()

    try:
        ruta = nx.shortest_path(grafo, origen, destino, weight="length")
        distancia = nx.shortest_path_length(grafo, origen, destino, weight="length")
    except nx.NetworkXNoPath:
        ruta, distancia = dijkstra_no_dirigido(grafo, origen, destino)
    except nx.NodeNotFound:
        ruta = []
        distancia = float("inf")

    fin = time.perf_counter()
    tiempo_ms = (fin - inicio) * 1000
    return ruta, distancia, tiempo_ms


def dijkstra_no_dirigido(grafo, origen, destino):
    # algunos puntos quedan en vias de un solo sentido; este respaldo evita descartarlos
    try:
        if "grafo_no_dirigido" not in grafo.graph:
            grafo.graph["grafo_no_dirigido"] = grafo.to_undirected()

        grafo_no_dirigido = grafo.graph["grafo_no_dirigido"]
        ruta = nx.shortest_path(grafo_no_dirigido, origen, destino, weight="length")
        distancia = nx.shortest_path_length(grafo_no_dirigido, origen, destino, weight="length")
    except nx.NetworkXNoPath:
        ruta = []
        distancia = float("inf")
    except nx.NodeNotFound:
        ruta = []
        distancia = float("inf")

    return ruta, distancia


def electrolinera_mas_cercana(grafo, nodo_actual, nodos_electrolineras):
    # se comparan las rutas a todas las electrolineras y se escoge la menor
    mejor_id = ""
    mejor_nodo = None
    mejor_ruta = []
    mejor_distancia = float("inf")
    tiempo_total = 0

    for id_electrolinera, nodo_electrolinera in nodos_electrolineras.items():
        ruta, distancia, tiempo_ms = dijkstra(grafo, nodo_actual, nodo_electrolinera)
        tiempo_total = tiempo_total + tiempo_ms

        if distancia < mejor_distancia:
            mejor_id = id_electrolinera
            mejor_nodo = nodo_electrolinera
            mejor_ruta = ruta
            mejor_distancia = distancia

    return mejor_id, mejor_nodo, mejor_ruta, mejor_distancia, tiempo_total
