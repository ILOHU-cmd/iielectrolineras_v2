# simulacion de recorridos de vehiculos electricos

import random
from datetime import datetime, timedelta

from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS
from recursos.grafos.algoritmo_grafos import dijkstra, electrolinera_mas_cercana
from recursos.grafos.constructor import obtener_nodos_electrolineras, obtener_nodos_referencia
from recursos.utilidades.archivos import agregar_recarga, exportar_estadisticas, guardar_txt


BATERIA_INICIAL = 100.0
BATERIA_DESPUES_RECARGA = 80.0
METROS_POR_KM = 1000.0


def crear_estado_vehiculos():
    vehiculos = []

    for clave in VEHICULOS:
        datos = VEHICULOS[clave]
        vehiculos.append({
            "id": datos["id"],
            "nombre_mostrado": datos["nombre"] + " - " + datos["gama"],
            "bateria_kwh": datos["bateria_kwh"],
            "consumo_kwh_100km": datos["consumo_kwh_100km"],
            "nivel_bateria": BATERIA_INICIAL,
            "km_total": 0.0,
        })

    return vehiculos


def buscar_nombre(lista, id_lugar):
    for lugar in lista:
        if lugar["id"] == id_lugar:
            return lugar["nombre"]
    return id_lugar


def nombre_electrolinera(id_electrolinera):
    return buscar_nombre(ELECTROLINERAS, id_electrolinera)


def nombre_referencia(id_referencia):
    return buscar_nombre(PUNTOS_REFERENCIA, id_referencia)


def gasto_bateria(vehiculo, distancia_m):
    distancia_km = distancia_m / METROS_POR_KM
    kwh_usados = (vehiculo["consumo_kwh_100km"] / 100.0) * distancia_km
    return (kwh_usados / vehiculo["bateria_kwh"]) * 100.0


def longitud_tramo(grafo, nodo_a, nodo_b):
    datos = grafo.get_edge_data(nodo_a, nodo_b)

    if datos is None:
        return 0.0

    if "length" in datos:
        return float(datos.get("length", 0.0))

    menor = None
    for clave, arista in datos.items():
        largo = float(arista.get("length", 0.0))
        if menor is None or largo < menor:
            menor = largo

    return menor if menor is not None else 0.0


def avanzar_por_ruta(grafo, vehiculo, ruta, distancia_total_m, limite_recarga):
    # devuelve si hubo recarga, en que nodo y cuantos metros recorrio antes de bajar bateria
    distancia = 0.0

    if len(ruta) < 2:
        distancia = distancia_total_m
        vehiculo["nivel_bateria"] = max(0.0, vehiculo["nivel_bateria"] - gasto_bateria(vehiculo, distancia))
        vehiculo["km_total"] = vehiculo["km_total"] + distancia / METROS_POR_KM
        return False, None, distancia

    i = 0
    while i < len(ruta) - 1:
        tramo = longitud_tramo(grafo, ruta[i], ruta[i + 1])
        distancia = distancia + tramo
        vehiculo["nivel_bateria"] = max(0.0, vehiculo["nivel_bateria"] - gasto_bateria(vehiculo, tramo))
        vehiculo["km_total"] = vehiculo["km_total"] + tramo / METROS_POR_KM

        if vehiculo["nivel_bateria"] <= limite_recarga:
            return True, ruta[i + 1], distancia

        i = i + 1

    return False, None, distancia


def coordenadas_nodo(grafo, nodo):
    if nodo is None:
        return "", ""

    datos = grafo.nodes[nodo]
    return round(float(datos.get("y", 0)), 7), round(float(datos.get("x", 0)), 7)


def crear_referencias(nodos_referencia):
    referencias = []

    for id_ref, nodo in nodos_referencia.items():
        referencias.append({
            "id": id_ref,
            "nombre": nombre_referencia(id_ref),
            "nodo": nodo,
        })

    return referencias


def inicializar_estadisticas(vehiculos):
    estadisticas = {
        "total_recorridos": 0,
        "total_recargas": 0,
        "uso_electrolineras": {},
        "uso_electrolineras_id": {},
        "por_vehiculo": {},
        "puntos_candidatos": {},
        "puntos_candidatos_detalle": {},
        "recorridos": [],
    }

    for elec in ELECTROLINERAS:
        estadisticas["uso_electrolineras"][elec["nombre"]] = 0
        estadisticas["uso_electrolineras_id"][elec["id"]] = 0

    for vehiculo in vehiculos:
        estadisticas["por_vehiculo"][vehiculo["nombre_mostrado"]] = {"recargas": 0, "km_total": 0.0}

    return estadisticas


def ejecutar_simulacion(grafo, cantidad_recorridos, semilla):
    if grafo is None:
        print("no hay grafo cargado.")
        return {}

    random.seed(semilla)
    nodos_electrolineras = obtener_nodos_electrolineras(grafo)
    nodos_referencia = obtener_nodos_referencia(grafo)

    if len(nodos_electrolineras) == 0 or len(nodos_referencia) < 2:
        print("faltan nodos de electrolineras o puntos de referencia.")
        return {}

    referencias = crear_referencias(nodos_referencia)
    vehiculos = crear_estado_vehiculos()
    estadisticas = inicializar_estadisticas(vehiculos)
    fecha_base = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)

    print()
    print("iniciando simulacion con", cantidad_recorridos, "recorridos.")
    print("semilla usada:", semilla)

    i = 0
    intentos = 0

    while i < cantidad_recorridos and intentos < cantidad_recorridos * 10:
        intentos = intentos + 1
        origen_ref = random.choice(referencias)
        destino_ref = random.choice(referencias)

        if origen_ref["nodo"] == destino_ref["nodo"]:
            continue

        vehiculo = vehiculos[i % len(vehiculos)]
        limite_recarga = random.uniform(10.0, 20.0)
        ruta, distancia_m, tiempo_dijkstra = dijkstra(grafo, origen_ref["nodo"], destino_ref["nodo"])

        if len(ruta) == 0:
            continue

        recarga, nodo_descarga, distancia_descarga = avanzar_por_ruta(
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
            "distancia_hasta_descarga_km": round(distancia_descarga / METROS_POR_KM, 3),
            "bateria_final": round(vehiculo["nivel_bateria"], 2),
            "limite_recarga": round(limite_recarga, 2),
            "recarga_activada": False,
            "tiempo_dijkstra_ms": round(tiempo_dijkstra, 3),
        }

        if recarga:
            fecha = fecha_base + timedelta(minutes=i * 25)
            registrar_recarga(grafo, vehiculo, nodo_descarga, nodos_electrolineras, detalle, estadisticas, fecha, distancia_descarga)

        estadisticas["recorridos"].append(detalle)
        estadisticas["total_recorridos"] = estadisticas["total_recorridos"] + 1
        estadisticas["por_vehiculo"][vehiculo["nombre_mostrado"]]["km_total"] = round(vehiculo["km_total"], 3)
        i = i + 1

    exportar_estadisticas(estadisticas)
    exportar_resumen_txt(estadisticas)
    print("simulacion terminada.")
    return estadisticas


def registrar_recarga(grafo, vehiculo, nodo_descarga, nodos_electrolineras, detalle, estadisticas, fecha, distancia_descarga):
    resultado = electrolinera_mas_cercana(
        grafo,
        nodo_descarga,
        nodos_electrolineras,
    )
    id_electro = resultado[0]
    distancia_carga = resultado[3]
    tiempo_busqueda = resultado[4]

    if id_electro == "":
        return

    nombre = nombre_electrolinera(id_electro)
    punto = detalle["origen"] + " -> " + detalle["destino"]
    lat, lon = coordenadas_nodo(grafo, nodo_descarga)

    evento = {
        "timestamp": fecha.strftime("%Y-%m-%d %H:%M:%S"),
        "vehiculo_id": vehiculo["id"],
        "vehiculo_nombre": vehiculo["nombre_mostrado"],
        "electrolinera_id": id_electro,
        "electrolinera_nombre": nombre,
        "punto_bateria_baja": punto,
        "lat_bateria_baja": lat,
        "lon_bateria_baja": lon,
        "nodo_bateria_baja": nodo_descarga,
        "nivel_bateria_llegada": round(vehiculo["nivel_bateria"], 2),
        "distancia_recorrida_m": round(distancia_descarga, 1),
        "distancia_a_electrolinera_m": round(distancia_carga, 1),
        "hora": fecha.hour,
    }
    agregar_recarga(evento)

    vehiculo["nivel_bateria"] = BATERIA_DESPUES_RECARGA
    estadisticas["total_recargas"] = estadisticas["total_recargas"] + 1
    estadisticas["uso_electrolineras"][nombre] = estadisticas["uso_electrolineras"].get(nombre, 0) + 1
    estadisticas["uso_electrolineras_id"][id_electro] = estadisticas["uso_electrolineras_id"].get(id_electro, 0) + 1
    estadisticas["por_vehiculo"][vehiculo["nombre_mostrado"]]["recargas"] += 1

    clave = str(lat) + "," + str(lon)
    estadisticas["puntos_candidatos"][punto] = estadisticas["puntos_candidatos"].get(punto, 0) + 1
    estadisticas["puntos_candidatos_detalle"][clave] = {
        "punto": punto,
        "lat": lat,
        "lon": lon,
        "eventos": estadisticas["puntos_candidatos"].get(punto, 0),
    }

    detalle["recarga_activada"] = True
    detalle["electrolinera_usada"] = nombre
    detalle["distancia_a_electrolinera_km"] = round(distancia_carga / METROS_POR_KM, 3)
    detalle["lat_bateria_baja"] = lat
    detalle["lon_bateria_baja"] = lon
    detalle["nodo_bateria_baja"] = nodo_descarga
    detalle["tiempo_busqueda_ms"] = round(tiempo_busqueda, 3)


def ordenar_por_valor(datos):
    lista = []
    for clave, valor in datos.items():
        lista.append([clave, valor])

    lista.sort(key=lambda item: item[1], reverse=True)
    return lista


def obtener_uso_todas_electrolineras(estadisticas):
    uso = {}
    for elec in ELECTROLINERAS:
        uso[elec["nombre"]] = estadisticas.get("uso_electrolineras_id", {}).get(elec["id"], 0)
    return ordenar_por_valor(uso)


def exportar_resumen_txt(estadisticas):
    lineas = [
        "resumen de simulacion",
        "total de recorridos: " + str(estadisticas["total_recorridos"]),
        "total de recargas: " + str(estadisticas["total_recargas"]),
        "",
        "uso de electrolineras:",
    ]

    for nombre, cantidad in obtener_uso_todas_electrolineras(estadisticas):
        lineas.append(nombre + ": " + str(cantidad))

    guardar_txt("resumen_simulacion", lineas)


def imprimir_resumen(estadisticas):
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
    for nombre, cantidad in obtener_uso_todas_electrolineras(estadisticas):
        print(nombre, "->", cantidad, "recargas")

    print()
    print("resumen por vehiculo:")
    for nombre, datos in estadisticas["por_vehiculo"].items():
        print(nombre, "| recargas:", datos["recargas"], "| km:", datos["km_total"])

    print()
    print("puntos candidatos para nuevas electrolineras:")
    candidatos = ordenar_por_valor(estadisticas.get("puntos_candidatos", {}))

    if len(candidatos) == 0:
        print("sin candidatos porque no hubo recargas.")
    else:
        for i, candidato in enumerate(candidatos, start=1):
            print(str(i) + ".", candidato[0], "->", candidato[1], "eventos")

    print("=" * 60)
