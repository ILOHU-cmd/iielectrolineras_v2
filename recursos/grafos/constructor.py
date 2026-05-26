# construccion y carga del grafo vial de Bucaramanga

import os
import networkx as nx
import osmnx as ox

from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA



# CONFIGURACION GENERAL


CIUDADES = [
    "Bucaramanga, Santander, Colombia",
    "Floridablanca, Santander, Colombia",
    "Piedecuesta, Santander, Colombia",
]
ZONAS_OSM = [
    {
        "nombre": "Zona industrial Giron - CENFER y Autopista Giron",
        "osmid": "W725206257",
    }
]

carpeta_raw = os.path.join(os.path.dirname(__file__), "..", "..", "datos", "raw")
if not os.path.exists(carpeta_raw):
    os.makedirs(carpeta_raw)
RUTA_CACHE = os.path.join(
    os.path.dirname(__file__), "..", "..", "datos", "raw", "grafo_bga.graphml"
)
TOLERANCIA_BBOX = 0.002
VERSION_GRAFO = "bga_florida_piedecuesta_zona_giron_w725206257"


def construir_grafo():
    """
    Carga el grafo desde cache si ya existe.
    Si no existe, descarga la red vial de Bucaramanga y area metropolitana.
    """

    if os.path.exists(RUTA_CACHE):

        print("Cargando grafo desde cache...")

        grafo = ox.load_graphml(RUTA_CACHE)

        if grafo_cubre_puntos(grafo):
            print("Grafo cargado exitosamente.")
            return marcar_nodos_especiales(grafo)

        print("El cache no cubre todos los puntos. Se descargara nuevamente.")

    print("Descargando red vial desde OpenStreetMap...")
    print("Ciudades: Bucaramanga, Floridablanca, Piedecuesta")
    print("Zona especifica de Giron: OSM way 725206257")
    print("Esto puede tardar varios minutos la primera vez.")
    print()

    # Descargar primera ciudad
    print("Descargando Bucaramanga...")
    grafo = ox.graph_from_place(
        CIUDADES[0],
        network_type="drive"
    )
    print("  Nodos:", len(list(grafo.nodes)), "Aristas:", len(list(grafo.edges)))

    # Unir las demas ciudades
    i = 1
    while i < len(CIUDADES):
        ciudad = CIUDADES[i]
        print("Descargando", ciudad, "...")

        try:
            grafo_extra = ox.graph_from_place(
                ciudad,
                network_type="drive"
            )
            print("  Nodos:", len(list(grafo_extra.nodes)), "Aristas:", len(list(grafo_extra.edges)))

            # Unir con el grafo principal
            grafo = nx.compose(grafo, grafo_extra)
            print("  Grafo unido. Total nodos:", len(list(grafo.nodes)))

        except Exception as error:
            print("  ERROR:", str(error))
            print("  Continuando sin esta ciudad...")

        i = i + 1

    # Unir la zona especifica de Giron tomada desde OSM por id
    i = 0
    while i < len(ZONAS_OSM):
        zona = ZONAS_OSM[i]
        print("Descargando", zona["nombre"], "(", zona["osmid"], ")...")

        try:
            grafo_zona = descargar_zona_osm(zona)
            print("  Nodos:", len(list(grafo_zona.nodes)), "Aristas:", len(list(grafo_zona.edges)))
            grafo = nx.compose(grafo, grafo_zona)
            print("  Zona unida. Total nodos:", len(list(grafo.nodes)))
        except Exception as error:
            print("  ERROR:", str(error))
            print("  Continuando sin esta zona especifica...")

        i = i + 1

    print()
    print("Grafo completo descargado.")
    print("Total nodos:", len(list(grafo.nodes)))
    print("Total aristas:", len(list(grafo.edges)))

    grafo.graph["version_proyecto"] = VERSION_GRAFO
    ox.save_graphml(grafo, RUTA_CACHE)

    print("Grafo guardado en disco para usos futuros.")

    return marcar_nodos_especiales(grafo)


def grafo_cubre_puntos(grafo):
    if grafo is None:
        return False

    if grafo.graph.get("version_proyecto") != VERSION_GRAFO:
        return False

    xs = []
    ys = []

    for nodo, datos in grafo.nodes(data=True):
        if datos.get("x") is not None and datos.get("y") is not None:
            xs.append(float(datos.get("x")))
            ys.append(float(datos.get("y")))

    if len(xs) == 0 or len(ys) == 0:
        return False

    lat_min = min(ys) - TOLERANCIA_BBOX
    lat_max = max(ys) + TOLERANCIA_BBOX
    lon_min = min(xs) - TOLERANCIA_BBOX
    lon_max = max(xs) + TOLERANCIA_BBOX
    lugares = ELECTROLINERAS + PUNTOS_REFERENCIA

    i = 0
    while i < len(lugares):
        lat = lugares[i]["lat"]
        lon = lugares[i]["lon"]

        if lat < lat_min or lat > lat_max or lon < lon_min or lon > lon_max:
            return False

        i = i + 1

    return True


def descargar_zona_osm(zona):
    # Usa el identificador exacto de OSM mostrado en el mapa.
    # W725206257 corresponde al way 725206257.
    gdf = ox.geocode_to_gdf(zona["osmid"], by_osmid=True)
    geometria = gdf.geometry.iloc[0]
    return ox.graph_from_polygon(geometria, network_type="drive")



# MARCAR ELECTROLINERAS Y PUNTOS


def marcar_nodos_especiales(grafo):
    """
    Busca el nodo OSM mas cercano a cada electrolinera y punto
    de referencia y los marca dentro del grafo.
    """

    # inicializar todos los nodos
    for nodo in grafo.nodes:

        grafo.nodes[nodo]["tipo"] = None
        grafo.nodes[nodo]["id_lugar"] = None
        grafo.nodes[nodo]["nombre_lugar"] = None
        grafo.nodes[nodo]["electrolineras"] = []
        grafo.nodes[nodo]["referencias"] = []

    # =====================================================
    # MARCAR ELECTROLINERAS
    # =====================================================

    for lugar in ELECTROLINERAS:

        nodo_cercano = ox.distance.nearest_nodes(
            grafo,
            lugar["lon"],
            lugar["lat"]
        )

        agregar_lugar_nodo(grafo, nodo_cercano, lugar, "electrolineras")

    # =====================================================
    # MARCAR PUNTOS DE REFERENCIA
    # =====================================================

    for lugar in PUNTOS_REFERENCIA:

        nodo_cercano = ox.distance.nearest_nodes(
            grafo,
            lugar["lon"],
            lugar["lat"]
        )

        agregar_lugar_nodo(grafo, nodo_cercano, lugar, "referencias")

    # =====================================================
    # CONTAR RESULTADOS
    # =====================================================

    total_electro = len(obtener_nodos_electrolineras(grafo))
    total_ref = len(obtener_nodos_referencia(grafo))

    print("Electrolineras marcadas:", total_electro)
    print("Puntos de referencia marcados:", total_ref)

    return grafo


def agregar_lugar_nodo(grafo, nodo, lugar, clave_lista):
    datos = grafo.nodes[nodo]
    datos[clave_lista].append({
        "id": lugar["id"],
        "nombre": lugar["nombre"],
    })
    actualizar_datos_compatibilidad(datos)


def actualizar_datos_compatibilidad(datos):
    tiene_electrolinera = len(datos.get("electrolineras", [])) > 0
    tiene_referencia = len(datos.get("referencias", [])) > 0

    if tiene_electrolinera and tiene_referencia:
        datos["tipo"] = "mixto"
        lugar = datos["referencias"][0]
    elif tiene_referencia:
        datos["tipo"] = "referencia"
        lugar = datos["referencias"][0]
    elif tiene_electrolinera:
        datos["tipo"] = "electrolinera"
        lugar = datos["electrolineras"][0]
    else:
        datos["tipo"] = None
        lugar = None

    if lugar is None:
        datos["id_lugar"] = None
        datos["nombre_lugar"] = None
    else:
        datos["id_lugar"] = lugar["id"]
        datos["nombre_lugar"] = lugar["nombre"]



# FUNCIONES AUXILIARES


def obtener_nodos_electrolineras(grafo):
    """
    Devuelve un diccionario:
    id_electrolinera -> nodo_osm
    """

    return obtener_nodos_por_lugares(grafo, ELECTROLINERAS, "electrolineras", "electrolinera")


def obtener_nodos_referencia(grafo):
    """
    Devuelve un diccionario:
    id_referencia -> nodo_osm
    """

    return obtener_nodos_por_lugares(grafo, PUNTOS_REFERENCIA, "referencias", "referencia")


def obtener_nodos_por_lugares(grafo, lugares, clave_lista, tipo_legacy):
    resultado = {}

    i = 0
    while i < len(lugares):
        id_lugar = lugares[i]["id"]
        nodo_encontrado = None

        for nodo, datos in grafo.nodes(data=True):
            lista = datos.get(clave_lista, [])

            j = 0
            while j < len(lista):
                if lista[j].get("id") == id_lugar:
                    nodo_encontrado = nodo
                    break
                j = j + 1

            if nodo_encontrado is not None:
                break

            if datos.get("tipo") == tipo_legacy and datos.get("id_lugar") == id_lugar:
                nodo_encontrado = nodo
                break

        if nodo_encontrado is not None:
            resultado[id_lugar] = nodo_encontrado

        i = i + 1

    return resultado


def obtener_nombre_nodo(grafo, nodo):
    """
    Devuelve el nombre asociado al nodo.
    """

    if grafo is None:
        return ""

    datos = grafo.nodes[nodo]
    referencias = datos.get("referencias", [])
    electrolineras = datos.get("electrolineras", [])

    if len(referencias) > 0:
        return referencias[0].get("nombre", str(nodo))

    if len(electrolineras) > 0:
        return electrolineras[0].get("nombre", str(nodo))

    nombre = datos.get("nombre_lugar")

    if nombre is None:
        return str(nodo)

    elif nombre == "":
        return str(nodo)

    else:
        return nombre
