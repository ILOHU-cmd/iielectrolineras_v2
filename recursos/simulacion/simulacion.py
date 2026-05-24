# simulacion de recorridos de vehiculos electricos
# cuando la bateria llega al rango bajo se busca la electrolinera mas cercana

import random
from datetime import datetime, timedelta

from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS
from recursos.grafos.algoritmo_grafos import dijkstra, electrolinera_mas_cercana
from recursos.grafos.constructor import (
    obtener_nodos_electrolineras,
    obtener_nodos_referencia,
)
from recursos.utilidades.archivos import agregar_recarga, exportar_estadisticas, guardar_txt


BATERIA_INICIAL = 100.0
BATERIA_DESPUES_RECARGA = 80.0
METROS_POR_KM = 1000.0


def crear_estado_vehiculos():
    # se crea una lista con la bateria actual y conteos de cada vehiculo
    estados = []
    claves = list(VEHICULOS.keys())

    i = 0
    while i < len(claves):
        datos = VEHICULOS[claves[i]]
        estado = {
            "id": datos["id"],
            "nombre": datos["nombre"],
            "nombre_mostrado": f"{datos['nombre']} - {datos['gama']}",
            "gama": datos["gama"],
            "bateria_kwh": datos["bateria_kwh"],
            "autonomia_km": datos["autonomia_km"],
            "consumo_kwh_100km": datos["consumo_kwh_100km"],
            "nivel_bateria": BATERIA_INICIAL,
            "recargas": 0,
            "km_total": 0.0,
        }
        estados.append(estado)
        i = i + 1

    return estados


def consumir_bateria(vehiculo, distancia_m):
    # se calcula el gasto de energia usando el consumo kwh por cada 100 km
    porcentaje_usado = calcular_porcentaje_bateria_usado(vehiculo, distancia_m)
    vehiculo["nivel_bateria"] = vehiculo["nivel_bateria"] - porcentaje_usado

    if vehiculo["nivel_bateria"] < 0:
        vehiculo["nivel_bateria"] = 0.0

    vehiculo["km_total"] = vehiculo["km_total"] + (distancia_m / METROS_POR_KM)


def calcular_porcentaje_bateria_usado(vehiculo, distancia_m):
    distancia_km = distancia_m / METROS_POR_KM
    kwh_usados = (vehiculo["consumo_kwh_100km"] / 100.0) * distancia_km
    return (kwh_usados / vehiculo["bateria_kwh"]) * 100.0


def obtener_longitud_arista(grafo, nodo_a, nodo_b):
    # obtiene la longitud menor entre dos nodos consecutivos de una ruta
    datos_arista = grafo.get_edge_data(nodo_a, nodo_b)

    if datos_arista is None:
        datos_arista = grafo.get_edge_data(nodo_b, nodo_a)

    if datos_arista is None:
        return 0.0

    if "length" in datos_arista:
        return float(datos_arista.get("length", 0.0))

    mejor_longitud = None

    for clave, datos in datos_arista.items():
        longitud = datos.get("length", 0.0)

        if mejor_longitud is None or longitud < mejor_longitud:
            mejor_longitud = longitud

    if mejor_longitud is None:
        return 0.0

    return float(mejor_longitud)


def avanzar_vehiculo_por_ruta(grafo, vehiculo, ruta, distancia_total_m, limite_recarga):
    # simula el consumo tramo por tramo y detecta el nodo donde baja al limite
    resultado = {
        "recarga_activada": False,
        "nodo_descarga": None,
        "distancia_hasta_descarga_m": distancia_total_m,
    }

    if len(ruta) < 2:
        consumir_bateria(vehiculo, distancia_total_m)
        return resultado

    distancia_acumulada = 0.0
    i = 0

    while i < len(ruta) - 1:
        nodo_actual = ruta[i]
        nodo_siguiente = ruta[i + 1]
        longitud_tramo = obtener_longitud_arista(grafo, nodo_actual, nodo_siguiente)

        if longitud_tramo <= 0:
            i = i + 1
            continue

        bateria_antes = vehiculo["nivel_bateria"]
        consumo_tramo = calcular_porcentaje_bateria_usado(vehiculo, longitud_tramo)
        bateria_despues = bateria_antes - consumo_tramo

        if bateria_despues < 0:
            bateria_despues = 0.0

        vehiculo["nivel_bateria"] = bateria_despues
        vehiculo["km_total"] = vehiculo["km_total"] + (longitud_tramo / METROS_POR_KM)
        distancia_acumulada = distancia_acumulada + longitud_tramo

        if bateria_despues <= limite_recarga:
            resultado["recarga_activada"] = True
            resultado["nodo_descarga"] = nodo_siguiente
            resultado["distancia_hasta_descarga_m"] = distancia_acumulada
            return resultado

        i = i + 1

    resultado["distancia_hasta_descarga_m"] = distancia_acumulada
    return resultado


def necesita_recarga(vehiculo, limite_recarga):
    # el proyecto pide recargar cuando la bateria este entre 10 y 20 por ciento
    if vehiculo["nivel_bateria"] <= limite_recarga:
        return True
    else:
        return False


def recargar_vehiculo(vehiculo):
    # despues de usar una electrolinera se deja la bateria en 80 por ciento
    vehiculo["nivel_bateria"] = BATERIA_DESPUES_RECARGA
    vehiculo["recargas"] = vehiculo["recargas"] + 1


def obtener_nombre_referencia(id_referencia):
    i = 0
    while i < len(PUNTOS_REFERENCIA):
        if PUNTOS_REFERENCIA[i]["id"] == id_referencia:
            return PUNTOS_REFERENCIA[i]["nombre"]
        i = i + 1

    return id_referencia


def obtener_nombre_electrolinera(id_electrolinera):
    i = 0
    while i < len(ELECTROLINERAS):
        if ELECTROLINERAS[i]["id"] == id_electrolinera:
            return ELECTROLINERAS[i]["nombre"]
        i = i + 1

    return id_electrolinera


def coordenadas_nodo(grafo, nodo):
    # devuelve las coordenadas exactas del nodo OSM donde quedo el vehiculo
    if grafo is None or nodo is None:
        return None, None

    datos = grafo.nodes[nodo]
    lat = datos.get("y")
    lon = datos.get("x")

    if lat is None or lon is None:
        return None, None

    return float(lat), float(lon)


def crear_lista_referencias(nodos_referencia):
    referencias = []

    for id_referencia, nodo in nodos_referencia.items():
        referencias.append({
            "id": id_referencia,
            "nombre": obtener_nombre_referencia(id_referencia),
            "nodo": nodo,
        })

    return referencias


def crear_pares_referencias(referencias):
    pares = []

    i = 0
    while i < len(referencias):
        j = 0
        while j < len(referencias):
            if referencias[i]["id"] != referencias[j]["id"] and referencias[i]["nodo"] != referencias[j]["nodo"]:
                pares.append([referencias[i], referencias[j]])
            j = j + 1
        i = i + 1

    return pares


def inicializar_estadisticas(vehiculos):
    # se crea la estructura donde se guardan los resultados de la simulacion
    estadisticas = {
        "total_recorridos": 0,
        "total_recargas": 0,
        "uso_electrolineras": {},
        "uso_electrolineras_id": {},
        "por_vehiculo": {},
        "puntos_candidatos": {},
        "recorridos": [],
    }

    i = 0
    while i < len(ELECTROLINERAS):
        estadisticas["uso_electrolineras"][ELECTROLINERAS[i]["nombre"]] = 0
        estadisticas["uso_electrolineras_id"][ELECTROLINERAS[i]["id"]] = 0
        i = i + 1

    i = 0
    while i < len(vehiculos):
        nombre = vehiculos[i]["nombre_mostrado"]
        estadisticas["por_vehiculo"][nombre] = {
            "recargas": 0,
            "km_total": 0.0,
        }
        i = i + 1

    return estadisticas


def ejecutar_simulacion(grafo, cantidad_recorridos, semilla):
    # esta funcion hace n recorridos aleatorios entre puntos fijos
    if grafo is None:
        print("no hay grafo cargado.")
        return {}

    random.seed(semilla)

    nodos_electrolineras = obtener_nodos_electrolineras(grafo)
    nodos_referencia = obtener_nodos_referencia(grafo)

    if len(nodos_electrolineras) == 0:
        print("no se encontraron electrolineras en el grafo.")
        return {}
    elif len(nodos_referencia) < 2:
        print("se necesitan al menos dos puntos de referencia.")
        return {}

    lista_referencias = crear_lista_referencias(nodos_referencia)
    pares_referencias = crear_pares_referencias(lista_referencias)

    if len(pares_referencias) == 0:
        print("los puntos de referencia quedaron en el mismo nodo del grafo.")
        print("regenere el grafo del area metropolitana para obtener rutas reales.")
        return {}

    vehiculos = crear_estado_vehiculos()
    estadisticas = inicializar_estadisticas(vehiculos)
    tiempo_base = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)

    print()
    print("iniciando simulacion con", cantidad_recorridos, "recorridos.")
    print("semilla usada:", semilla)

    i = 0
    intentos = 0
    maximo_intentos = cantidad_recorridos * 10

    while i < cantidad_recorridos and intentos < maximo_intentos:
        intentos = intentos + 1
        par_referencias = random.choice(pares_referencias)
        origen_ref = par_referencias[0]
        destino_ref = par_referencias[1]
        origen = origen_ref["nodo"]
        destino = destino_ref["nodo"]

        vehiculo = vehiculos[i % len(vehiculos)]
        limite_recarga = random.uniform(10.0, 20.0)
        ruta, distancia_m, tiempo_dijkstra = dijkstra(grafo, origen, destino)

        if len(ruta) == 0:
            # si no hay ruta entre esos dos puntos, se intenta otro recorrido
            # asi el total final queda igual a la cantidad solicitada
            continue

        resultado_consumo = avanzar_vehiculo_por_ruta(
            grafo,
            vehiculo,
            ruta,
            distancia_m,
            limite_recarga,
        )

        detalle = {
            "numero": i + 1,
            "vehiculo": vehiculo["nombre_mostrado"],
            "origen": origen_ref["nombre"],
            "destino": destino_ref["nombre"],
            "distancia_km": round(distancia_m / METROS_POR_KM, 3),
            "distancia_hasta_descarga_km": round(
                resultado_consumo["distancia_hasta_descarga_m"] / METROS_POR_KM,
                3,
            ),
            "bateria_final": round(vehiculo["nivel_bateria"], 2),
            "limite_recarga": round(limite_recarga, 2),
            "recarga_activada": False,
            "tiempo_dijkstra_ms": round(tiempo_dijkstra, 3),
        }

        if resultado_consumo["recarga_activada"]:
            registrar_evento_recarga(
                grafo,
                vehiculo,
                resultado_consumo["nodo_descarga"],
                nodos_electrolineras,
                detalle,
                estadisticas,
                tiempo_base + timedelta(minutes=i * 25),
                resultado_consumo["distancia_hasta_descarga_m"],
            )

        estadisticas["recorridos"].append(detalle)
        estadisticas["total_recorridos"] = estadisticas["total_recorridos"] + 1
        estadisticas["por_vehiculo"][vehiculo["nombre_mostrado"]]["km_total"] = round(
            vehiculo["km_total"],
            3,
        )
        i = i + 1

    if estadisticas["total_recorridos"] < cantidad_recorridos:
        print("no se pudieron completar todos los recorridos solicitados.")
        print("recorridos completados:", estadisticas["total_recorridos"])
        print("esto puede pasar si el grafo tiene rutas desconectadas.")

    exportar_estadisticas(estadisticas)
    exportar_resumen_txt(estadisticas)
    print("simulacion terminada.")
    return estadisticas


def exportar_resumen_txt(estadisticas):
    # guarda un resumen corto en txt para cumplir con manejo de archivos de texto
    lineas = []
    lineas.append("resumen de simulacion")
    lineas.append("total de recorridos: " + str(estadisticas["total_recorridos"]))
    lineas.append("total de recargas: " + str(estadisticas["total_recargas"]))
    lineas.append("")
    lineas.append("uso de electrolineras:")

    uso_ordenado = obtener_uso_todas_electrolineras(estadisticas)

    i = 0
    while i < len(uso_ordenado):
        lineas.append(uso_ordenado[i][0] + ": " + str(uso_ordenado[i][1]))
        i = i + 1

    guardar_txt("resumen_simulacion", lineas)


def registrar_evento_recarga(
    grafo,
    vehiculo,
    nodo_actual,
    nodos_electrolineras,
    detalle,
    estadisticas,
    fecha,
    distancia_hasta_descarga_m,
):
    # se busca la electrolinera mas cercana y se guarda el evento de recarga
    resultado = electrolinera_mas_cercana(grafo, nodo_actual, nodos_electrolineras)
    id_electrolinera = resultado[0]
    distancia_carga = resultado[3]
    tiempo_busqueda = resultado[4]

    if id_electrolinera == "":
        return

    nombre_electrolinera = obtener_nombre_electrolinera(id_electrolinera)
    punto_baja = detalle["origen"] + " -> " + detalle["destino"]
    lat_baja, lon_baja = coordenadas_nodo(grafo, nodo_actual)

    evento = {
        "timestamp": fecha.strftime("%Y-%m-%d %H:%M:%S"),
        "vehiculo_id": vehiculo["id"],
        "vehiculo_nombre": vehiculo["nombre_mostrado"],
        "electrolinera_id": id_electrolinera,
        "electrolinera_nombre": nombre_electrolinera,
        "punto_bateria_baja": punto_baja,
        "lat_bateria_baja": round(lat_baja, 7) if lat_baja is not None else "",
        "lon_bateria_baja": round(lon_baja, 7) if lon_baja is not None else "",
        "nodo_bateria_baja": nodo_actual,
        "nivel_bateria_llegada": round(vehiculo["nivel_bateria"], 2),
        "distancia_recorrida_m": round(distancia_hasta_descarga_m, 1),
        "distancia_a_electrolinera_m": round(distancia_carga, 1),
        "hora": fecha.hour,
    }

    agregar_recarga(evento)
    recargar_vehiculo(vehiculo)

    estadisticas["total_recargas"] = estadisticas["total_recargas"] + 1
    estadisticas["por_vehiculo"][vehiculo["nombre_mostrado"]]["recargas"] = (
        estadisticas["por_vehiculo"][vehiculo["nombre_mostrado"]]["recargas"] + 1
    )

    if nombre_electrolinera in estadisticas["uso_electrolineras"]:
        estadisticas["uso_electrolineras"][nombre_electrolinera] = (
            estadisticas["uso_electrolineras"][nombre_electrolinera] + 1
        )
    else:
        estadisticas["uso_electrolineras"][nombre_electrolinera] = 1

    if "uso_electrolineras_id" not in estadisticas:
        estadisticas["uso_electrolineras_id"] = {}

    if id_electrolinera in estadisticas["uso_electrolineras_id"]:
        estadisticas["uso_electrolineras_id"][id_electrolinera] = (
            estadisticas["uso_electrolineras_id"][id_electrolinera] + 1
        )
    else:
        estadisticas["uso_electrolineras_id"][id_electrolinera] = 1

    if punto_baja in estadisticas["puntos_candidatos"]:
        estadisticas["puntos_candidatos"][punto_baja] = estadisticas["puntos_candidatos"][punto_baja] + 1
    else:
        estadisticas["puntos_candidatos"][punto_baja] = 1

    if "puntos_candidatos_detalle" not in estadisticas:
        estadisticas["puntos_candidatos_detalle"] = {}

    clave_coord = punto_baja
    if lat_baja is not None and lon_baja is not None:
        clave_coord = str(round(lat_baja, 5)) + "," + str(round(lon_baja, 5))

    if clave_coord not in estadisticas["puntos_candidatos_detalle"]:
        estadisticas["puntos_candidatos_detalle"][clave_coord] = {
            "punto": punto_baja,
            "lat": round(lat_baja, 7) if lat_baja is not None else "",
            "lon": round(lon_baja, 7) if lon_baja is not None else "",
            "eventos": 0,
            "distancia_total_m": 0.0,
            "bateria_total": 0.0,
        }

    estadisticas["puntos_candidatos_detalle"][clave_coord]["eventos"] = (
        estadisticas["puntos_candidatos_detalle"][clave_coord]["eventos"] + 1
    )
    estadisticas["puntos_candidatos_detalle"][clave_coord]["distancia_total_m"] = round(
        estadisticas["puntos_candidatos_detalle"][clave_coord]["distancia_total_m"] + distancia_carga,
        1,
    )
    estadisticas["puntos_candidatos_detalle"][clave_coord]["bateria_total"] = round(
        estadisticas["puntos_candidatos_detalle"][clave_coord]["bateria_total"] + vehiculo["nivel_bateria"],
        2,
    )

    detalle["recarga_activada"] = True
    detalle["electrolinera_usada"] = nombre_electrolinera
    detalle["distancia_a_electrolinera_km"] = round(distancia_carga / METROS_POR_KM, 3)
    detalle["lat_bateria_baja"] = round(lat_baja, 7) if lat_baja is not None else ""
    detalle["lon_bateria_baja"] = round(lon_baja, 7) if lon_baja is not None else ""
    detalle["nodo_bateria_baja"] = nodo_actual
    detalle["tiempo_busqueda_ms"] = round(tiempo_busqueda, 3)


def ordenar_diccionario_por_valor(datos):
    # ordenamiento burbuja de mayor a menor para mostrar resultados sin usar cosas avanzadas
    lista = []

    for clave, valor in datos.items():
        lista.append([clave, valor])

    i = 0
    while i < len(lista):
        j = 0
        while j < len(lista) - 1:
            if lista[j][1] < lista[j + 1][1]:
                temporal = lista[j]
                lista[j] = lista[j + 1]
                lista[j + 1] = temporal
            j = j + 1
        i = i + 1

    return lista


def obtener_uso_todas_electrolineras(estadisticas):
    # arma una lista con las 8 electrolineras aunque alguna tenga cero recargas
    uso_por_id = estadisticas.get("uso_electrolineras_id", {})
    uso_por_nombre = estadisticas.get("uso_electrolineras", {})
    uso_completo = {}

    i = 0
    while i < len(ELECTROLINERAS):
        id_electrolinera = ELECTROLINERAS[i]["id"]
        nombre = ELECTROLINERAS[i]["nombre"]

        if id_electrolinera in uso_por_id:
            uso_completo[nombre] = uso_por_id[id_electrolinera]
        elif nombre in uso_por_nombre:
            uso_completo[nombre] = uso_por_nombre[nombre]
        else:
            uso_completo[nombre] = 0

        i = i + 1

    return ordenar_diccionario_por_valor(uso_completo)


def imprimir_resumen(estadisticas):
    # muestra en pantalla los resultados principales de la simulacion
    if not estadisticas:
        print("no hay estadisticas para mostrar.")
        return

    print()
    print("=" * 60)
    print("resumen de simulacion")
    print("=" * 60)
    print("total de recorridos:", estadisticas["total_recorridos"])
    print("total de recargas:", estadisticas["total_recargas"])

    print()
    print("uso de electrolineras:")
    uso_ordenado = obtener_uso_todas_electrolineras(estadisticas)

    i = 0
    while i < len(uso_ordenado):
        print(uso_ordenado[i][0], "->", uso_ordenado[i][1], "recargas")
        i = i + 1

    print()
    print("resumen por vehiculo:")
    for nombre, datos in estadisticas["por_vehiculo"].items():
        print(nombre, "| recargas:", datos["recargas"], "| km:", datos["km_total"])

    print()
    print("puntos candidatos para nuevas electrolineras:")
    candidatos = ordenar_diccionario_por_valor(estadisticas["puntos_candidatos"])

    if len(candidatos) == 0:
        print("sin candidatos porque no hubo recargas.")
    else:
        i = 0
        while i < len(candidatos):
            nombre = candidatos[i][0]
            coordenadas = ""
            detalles = estadisticas.get("puntos_candidatos_detalle", {})

            for clave, info in detalles.items():
                if info.get("punto") == nombre:
                    coordenadas = " | coord: " + str(info.get("lat", "")) + ", " + str(info.get("lon", ""))
                    break

            print(str(i + 1) + ".", nombre, "->", candidatos[i][1], "eventos de bateria baja" + coordenadas)
            i = i + 1

    print("=" * 60)
