# menu principal del sistema
# se usan print, while, if, elif, else y match case como en clase

import random

from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS
from recursos.grafos.constructor import construir_grafo
from recursos.grafos.visualizacion import generar_grafico_dispersion, generar_mapa
from recursos.ml.modelo import entrenar_modelos, nombre_modelo, predecir_electrolinera
from recursos.simulacion.simulacion import ejecutar_simulacion, imprimir_resumen
from recursos.utilidades.archivos import (
    abrir_archivo,
    guardar_semilla,
    guardar_xlsx,
    leer_csv,
    leer_json,
    leer_semillas_guardadas,
)
from recursos.utilidades.validacion import confirmar, leer_decimal, leer_entero, limpiar_pantalla


def mostrar_encabezado(grafo, estadisticas, modelos):
    # muestra el estado actual del programa
    print("=" * 70)
    print("sistema de electrolineras - area metropolitana de bucaramanga")
    print("uis 2026-1 - algoritmos y programacion - matematicas discretas")
    print("=" * 70)

    if grafo is None:
        print("grafo cargado: no")
    else:
        print("grafo cargado: si")

    if estadisticas:
        print("simulacion ejecutada: si")
    else:
        print("simulacion ejecutada: no")

    if modelos:
        print("modelos entrenados: si")
    else:
        print("modelos entrenados: no")

    print()


def mostrar_menu():
    # opciones principales del proyecto
    print("MENU DE OPCIONES")
    print("1. Cargar o construir el grafo vial")
    print("2. Ver electrolineras, puntos de referencia y vehiculos")
    print("3. Ejecutar simulacion de recorridos")
    print("4. Ver resumen estadistico")
    print("5. Generar mapa interactivo")
    print("6. Entrenar modelos de Machine Learning")
    print("7. Predecir electrolinera con ML")
    print("8. Exportar historial a Excel")
    print("9. Comparar Dijkstra y ML")
    print("0. Salir")
    print()




def mostrar_electrolineras():
    # imprime las electrolineras registradas
    print("electrolineras")

    i = 0
    while i < len(ELECTROLINERAS):
        e = ELECTROLINERAS[i]
        print(
            e["id"],
            "-",
            e["nombre"],
            "| potencia:",
            e["potencia_kw"],
            "kw",
            "| coordenadas:",
            round(e["lat"], 4),
            round(e["lon"], 4),
        )
        i += 1


def mostrar_puntos_referencia():
    print()
    print("puntos fijos de referencia")

    i = 0
    while i < len(PUNTOS_REFERENCIA):
        p = PUNTOS_REFERENCIA[i]
        print(
            p["id"],
            "-",
            p["nombre"],
            "| coordenadas:",
            round(p["lat"], 4),
            round(p["lon"], 4),
        )
        i += 1


def mostrar_vehiculos():

    print()
    print("vehiculos electricos")

    for clave in VEHICULOS:

        v = VEHICULOS[clave]

        print(
            v["id"],
            "-",
            v["nombre"], "-", v["gama"],
            "| bateria:",
            v["bateria_kwh"],
            "kwh",
            "| autonomia:",
            v["autonomia_km"],
            "km",
            "| consumo:",
            v["consumo_kwh_100km"],
            "kwh/100km",
        )


def mostrar_datos_base():
    # agrupa los datos base para la opcion dos
    mostrar_electrolineras()
    mostrar_puntos_referencia()
    mostrar_vehiculos()


def obtener_semilla(cantidad):
    # permite crear una semilla nueva o usar una guardada
    print()
    print("manejo de semillas")
    print("1. generar semilla nueva")
    print("2. usar semilla guardada")
    opcion = leer_entero("seleccione una opcion: ", 1, 2)

    if opcion == 1:
        semilla = random.randint(1000, 999999)
        print("semilla generada:", semilla)

        if confirmar("desea guardar esta semilla"):
            guardada = guardar_semilla(semilla, cantidad)
            print("semilla guardada con codigo:", guardada["codigo"])

        return semilla
    else:
        semillas = leer_semillas_guardadas()

        if len(semillas) == 0:
            print("no hay semillas guardadas. se generara una nueva.")
            return random.randint(1000, 999999)

        i = 0
        while i < len(semillas):
            print(
                str(i + 1) + ".",
                "codigo:",
                semillas[i].get("codigo", ""),
                "| semilla:",
                semillas[i].get("semilla", ""),
            )
            i = i + 1

        posicion = leer_entero("seleccione una semilla: ", 1, len(semillas))
        return semillas[posicion - 1]["semilla"]


def pedir_vehiculo_numero():
    # retorna el numero del vehiculo para el modelo de machine learning
    print()
    print("seleccione vehiculo")
    print("1. tesla model y long range")
    print("2. byd dolphin surf")
    opcion = leer_entero("opcion: ", 1, 2)

    if opcion == 1:
        return 0
    else:
        return 1


def obtener_nombre_electrolinera(id_electrolinera):
    # busca una electrolinera por su id
    i = 0
    while i < len(ELECTROLINERAS):
        if ELECTROLINERAS[i]["id"] == id_electrolinera:
            return ELECTROLINERAS[i]["nombre"]
        i = i + 1

    return "no encontrada"


def preguntar_abrir(ruta):
    # pregunta si se desea abrir un archivo generado
    if ruta == "":
        return

    print("archivo generado en:")
    print(ruta)

    if confirmar("desea abrirlo ahora"):
        abierto = abrir_archivo(ruta)

        if abierto:
            print("archivo abierto correctamente.")
        else:
            print("no se pudo abrir automaticamente.")


def calcular_promedio_dijkstra(estadisticas):
    # calcula el tiempo promedio de dijkstra usando los recorridos simulados
    if not estadisticas:
        return None

    recorridos = estadisticas.get("recorridos", [])
    suma = 0
    contador = 0

    i = 0
    while i < len(recorridos):
        tiempo = recorridos[i].get("tiempo_dijkstra_ms", None)

        if tiempo is not None:
            suma = suma + float(tiempo)
            contador = contador + 1

        i = i + 1

    if contador == 0:
        return None
    else:
        return suma / contador


def mostrar_comparacion(modelos, estadisticas):
    # compara metricas guardadas de ml con una referencia de dijkstra
    if not modelos:
        metricas = leer_json("metricas_modelos")
    else:
        metricas = modelos

    if not metricas:
        print("no hay metricas disponibles. primero entrene los modelos.")
        return

    print()
    print("comparacion dijkstra y machine learning")
    print("dijkstra calcula la ruta exacta usando el peso de las aristas.")
    print("machine learning predice una electrolinera usando datos historicos.")
    print()

    promedio_dijkstra = calcular_promedio_dijkstra(estadisticas)

    for clave, datos in metricas.items():
        print("modelo:", nombre_modelo(clave))
        print("accuracy:", datos.get("accuracy", ""))
        print("f1:", datos.get("f1", ""))
        print("tiempo ml:", datos.get("tiempo_prediccion_ms", ""), "ms")

        if promedio_dijkstra is None:
            print("tiempo promedio dijkstra: no disponible. ejecute una simulacion primero.")
        else:
            print("tiempo promedio dijkstra:", round(promedio_dijkstra, 3), "ms")

        print()


def ejecutar_menu():
    # ciclo principal del programa
    grafo = None
    estadisticas = {}
    modelos = {}

    while True:
        limpiar_pantalla()
        mostrar_encabezado(grafo, estadisticas, modelos)
        mostrar_menu()
        opcion = input("seleccione una opcion: ").strip()

        match opcion:
            case "1":
                print()
                print("carga del grafo")
                grafo = construir_grafo()
            case "2":
                mostrar_datos_base()

            case "3":
                if grafo is None:
                    print("primero cargue el grafo en la opcion 1.")
                else:
                    print()
                    print("simulacion de recorridos")
                    cantidad = leer_entero("cantidad de recorridos (1-20000): ", 1, 20000)
                    semilla = obtener_semilla(cantidad)
                    estadisticas = ejecutar_simulacion(grafo, cantidad, semilla)
                    imprimir_resumen(estadisticas)

            case "4":
                if not estadisticas:
                    print("no hay estadisticas. ejecute primero la simulacion.")
                else:
                    imprimir_resumen(estadisticas)

                    if confirmar("desea generar grafico de dispersion"):
                        ruta = generar_grafico_dispersion(estadisticas)  # ← NUEVO
                        preguntar_abrir(ruta)

            case "5":
                ruta = generar_mapa()
                preguntar_abrir(ruta)

            case "6":
                print()
                print("entrenamiento de modelos")
                modelos = entrenar_modelos()

                if not modelos:
                    print("no se entrenaron modelos con los datos actuales.")

            case "7":
                print()
                print("prediccion de electrolinera")
                nivel = leer_decimal("nivel actual de bateria (0-100): ", 0, 100)
                distancia = leer_decimal("distancia recorrida en metros: ", 0)
                vehiculo_numero = pedir_vehiculo_numero()
                prediccion, tiempo = predecir_electrolinera(nivel, distancia, vehiculo_numero)

                if prediccion != "":
                    print("electrolinera predicha:", prediccion, "-", obtener_nombre_electrolinera(prediccion))
                    print("tiempo de prediccion:", round(tiempo, 3), "ms")

            case "8":
                print()
                print("exportar historial")
                filas = leer_csv("historial_recargas")

                if len(filas) == 0:
                    print("no hay historial para exportar.")
                else:
                    ruta = guardar_xlsx("historial_recargas", filas)
                    preguntar_abrir(ruta)

            case "9":
                mostrar_comparacion(modelos, estadisticas)

            case "0":
                print("programa finalizado.")
                break

            case _:
                print("opcion no valida. escriba un numero de 0 a 9.")
        print(input("Presione Enter para continuar..."))
