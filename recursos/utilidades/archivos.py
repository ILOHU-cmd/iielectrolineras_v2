# funciones para leer y guardar archivos del proyecto
# se usan csv, json, txt y xlsx porque hacen parte de los formatos pedidos

import csv
import json
import os
import webbrowser
from datetime import datetime


try:
    import openpyxl

    OPENPYXL_DISPONIBLE = True
except ImportError:
    OPENPYXL_DISPONIBLE = False


CARPETA_SALIDA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "datos", "output")
)
CARPETA_MODELOS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "datos", "processed")
)


def preparar_carpetas():
    # crea las carpetas donde se guardan resultados y modelos
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    if not os.path.exists(CARPETA_MODELOS):
        os.makedirs(CARPETA_MODELOS)


preparar_carpetas()


def ruta_salida(nombre_archivo):
    # arma la ruta completa de un archivo de salida
    return os.path.join(CARPETA_SALIDA, nombre_archivo)


def ruta_modelo(nombre_archivo):
    # arma la ruta completa de un archivo de modelo
    return os.path.join(CARPETA_MODELOS, nombre_archivo)


def guardar_json(nombre, datos):
    # guarda un diccionario o lista en formato json
    ruta = ruta_salida(nombre + ".json")

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)

    return ruta


def guardar_txt(nombre, lineas):
    # guarda una lista de lineas en un archivo de texto
    ruta = ruta_salida(nombre + ".txt")

    with open(ruta, "w", encoding="utf-8") as archivo:
        i = 0
        while i < len(lineas):
            archivo.write(str(lineas[i]) + "\n")
            i = i + 1

    return ruta


def leer_json(nombre):
    # lee un archivo json si existe
    ruta = ruta_salida(nombre + ".json")

    if not os.path.exists(ruta):
        return None

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_csv(nombre, filas, campos):
    # guarda una lista de diccionarios en un archivo csv
    ruta = ruta_salida(nombre + ".csv")

    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()

        i = 0
        while i < len(filas):
            escritor.writerow(filas[i])
            i = i + 1

    return ruta


def leer_csv(nombre):
    # lee un archivo csv y devuelve una lista de diccionarios
    ruta = ruta_salida(nombre + ".csv")

    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        filas = []

        for fila in lector:
            filas.append(fila)

    return filas


def agregar_recarga(evento):
    # agrega una recarga al historial sin borrar las anteriores
    ruta = ruta_salida("historial_recargas.csv")
    existe = os.path.exists(ruta)
    campos = [
        "timestamp",
        "vehiculo_id",
        "vehiculo_nombre",
        "electrolinera_id",
        "electrolinera_nombre",
        "punto_bateria_baja",
        "nivel_bateria_llegada",
        "distancia_recorrida_m",
    ]

    with open(ruta, "a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)

        if not existe:
            escritor.writeheader()

        escritor.writerow(evento)


def exportar_estadisticas(estadisticas):
    # guarda las estadisticas de la simulacion con fecha y hora
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    return guardar_json("estadisticas_" + fecha, estadisticas)


def guardar_xlsx(nombre, filas):
    # exporta una lista de diccionarios a excel si openpyxl esta instalado
    if not OPENPYXL_DISPONIBLE:
        print("openpyxl no esta instalado. se conserva el archivo csv.")
        return ruta_salida(nombre + ".csv")

    ruta = ruta_salida(nombre + ".xlsx")
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = nombre[:31]

    if len(filas) == 0:
        libro.save(ruta)
        return ruta

    columnas = list(filas[0].keys())
    hoja.append(columnas)

    i = 0
    while i < len(filas):
        fila_excel = []
        j = 0
        while j < len(columnas):
            columna = columnas[j]
            fila_excel.append(filas[i].get(columna, ""))
            j = j + 1
        hoja.append(fila_excel)
        i = i + 1

    libro.save(ruta)
    return ruta


def leer_semillas_guardadas():
    # lee las semillas guardadas para repetir una simulacion
    semillas = leer_json("semillas_simulacion")

    if semillas is None:
        return []
    elif not isinstance(semillas, list):
        return []
    else:
        return semillas


def guardar_semilla(semilla, cantidad_recorridos):
    # guarda una semilla para poder repetir los recorridos
    semillas = leer_semillas_guardadas()

    i = 0
    while i < len(semillas):
        if semillas[i].get("semilla") == semilla:
            return semillas[i]
        i = i + 1

    nueva = {
        "codigo": "S" + str(len(semillas) + 1),
        "semilla": semilla,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cantidad_recorridos": cantidad_recorridos,
    }
    semillas.append(nueva)
    guardar_json("semillas_simulacion", semillas)
    return nueva


def abrir_archivo(ruta):
    # intenta abrir un archivo generado desde el sistema operativo
    if not os.path.exists(ruta):
        return False

    try:
        if os.name == "nt":
            os.startfile(ruta)
        else:
            webbrowser.open("file://" + ruta)
        return True
    except Exception:
        return False
