# modelo sencillo de machine learning para predecir electrolineras
# se entrena con el historial de recargas generado por la simulacion

import warnings
import time

from recursos.utilidades.archivos import guardar_json, leer_csv, ruta_modelo


try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    SKLEARN_DISPONIBLE = True
except ImportError:
    SKLEARN_DISPONIBLE = False


def convertir_decimal(valor):
    # convierte texto a numero decimal de forma segura
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def vehiculo_a_numero(vehiculo_id):
    # convierte el id del vehiculo a un numero para el modelo
    if vehiculo_id == "V1":
        return 0
    elif vehiculo_id == "V2":
        return 1
    else:
        return 2


def texto_decimal(valor, defecto=0.0):
    numero = convertir_decimal(valor)

    if numero is None:
        return defecto
    else:
        return numero


def preparar_datos():
    # lee el historial csv y arma las listas x y y
    filas = leer_csv("historial_recargas")
    x = []
    y = []

    i = 0
    while i < len(filas):
        nivel = convertir_decimal(filas[i].get("nivel_bateria_llegada", ""))
        distancia = convertir_decimal(filas[i].get("distancia_recorrida_m", ""))
        vehiculo = vehiculo_a_numero(filas[i].get("vehiculo_id", ""))
        objetivo = filas[i].get("electrolinera_id", "")

        if nivel is not None and distancia is not None and objetivo != "":
            x.append([nivel, distancia, vehiculo])
            y.append(objetivo)

        i = i + 1

    return x, y


def contar_clases(y):
    # cuenta cuantas electrolineras diferentes aparecen en el historial
    clases = []

    i = 0
    while i < len(y):
        if y[i] not in clases:
            clases.append(y[i])
        i = i + 1

    return len(clases)


def nombre_modelo(nombre):
    # nombre bonito para mostrar en pantalla
    if nombre == "random_forest":
        return "bosque aleatorio"
    elif nombre == "regresion_logistica":
        return "regresion logistica"
    else:
        return nombre


def entrenar_modelos():
    # entrena dos modelos sencillos con scikit-learn
    if not SKLEARN_DISPONIBLE:
        print("scikit-learn o joblib no estan instalados.")
        return {}

    x, y = preparar_datos()

    if len(x) < 8:
        print("faltan datos para entrenar. ejecute mas recorridos en la opcion 3.")
        print("registros disponibles:", len(x))
        return {}
    elif contar_clases(y) < 2:
        print("se necesitan recargas en al menos dos electrolineras diferentes.")
        return {}

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.30,
        random_state=42,
    )

    modelos = {
        "random_forest": RandomForestClassifier(n_estimators=60, random_state=42),
        "regresion_logistica": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=3000),
        ),
    }
    resultados = {}

    for clave, modelo in modelos.items():
        print()
        print("entrenando modelo:", nombre_modelo(clave))

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                inicio = time.perf_counter()
                modelo.fit(x_train, y_train)
                fin = time.perf_counter()

            tiempo_entrenamiento = (fin - inicio) * 1000

            inicio = time.perf_counter()
            predicciones = modelo.predict(x_test)
            fin = time.perf_counter()
            tiempo_prediccion = (fin - inicio) * 1000

            exactitud = accuracy_score(y_test, predicciones)
            f1 = f1_score(y_test, predicciones, average="weighted", zero_division=0)

            paquete = {
                "modelo": modelo,
                "nombre": clave,
            }
            joblib.dump(paquete, ruta_modelo("modelo_" + clave + ".pkl"))

            resultados[clave] = {
                "accuracy": round(exactitud, 4),
                "f1": round(f1, 4),
                "tiempo_entrenamiento_ms": round(tiempo_entrenamiento, 3),
                "tiempo_prediccion_ms": round(tiempo_prediccion, 3),
            }

            print("exactitud:", round(exactitud, 4))
            print("f1:", round(f1, 4))
            print("tiempo de entrenamiento:", round(tiempo_entrenamiento, 3), "ms")
        except Exception as error:
            print("no se pudo entrenar", nombre_modelo(clave))
            print("detalle:", error)

    if len(resultados) > 0:
        guardar_json("metricas_modelos", resultados)
        recomendar_nuevas_electrolineras()

    return resultados


def predecir_electrolinera(nivel_bateria, distancia_m, vehiculo_numero):
    # carga el modelo random forest y predice la electrolinera
    if not SKLEARN_DISPONIBLE:
        print("scikit-learn o joblib no estan instalados.")
        return "", 0

    ruta = ruta_modelo("modelo_random_forest.pkl")

    try:
        paquete = joblib.load(ruta)
    except FileNotFoundError:
        print("no existe un modelo entrenado. use primero la opcion 6.")
        return "", 0

    modelo = paquete["modelo"]
    datos = [[nivel_bateria, distancia_m, vehiculo_numero]]

    inicio = time.perf_counter()
    prediccion = modelo.predict(datos)[0]
    fin = time.perf_counter()
    tiempo_ms = (fin - inicio) * 1000

    return prediccion, tiempo_ms


def agrupar_eventos_bateria_baja():
    # agrupa el historial por coordenada exacta aproximada del nodo donde bajo la bateria
    filas = leer_csv("historial_recargas")
    grupos = {}

    i = 0
    while i < len(filas):
        fila = filas[i]
        lat = convertir_decimal(fila.get("lat_bateria_baja", ""))
        lon = convertir_decimal(fila.get("lon_bateria_baja", ""))

        if lat is None or lon is None:
            i = i + 1
            continue

        clave = str(round(lat, 5)) + "," + str(round(lon, 5))

        if clave not in grupos:
            grupos[clave] = {
                "punto": fila.get("punto_bateria_baja", ""),
                "lat": round(lat, 7),
                "lon": round(lon, 7),
                "eventos": 0,
                "bateria_total": 0.0,
                "distancia_total_m": 0.0,
                "hora_total": 0.0,
                "vehiculos": [],
            }

        bateria = texto_decimal(fila.get("nivel_bateria_llegada", ""), 0.0)
        distancia = texto_decimal(
            fila.get("distancia_a_electrolinera_m", fila.get("distancia_recorrida_m", "")),
            0.0,
        )
        hora = texto_decimal(fila.get("hora", "0"), 0.0)
        vehiculo = fila.get("vehiculo_id", "")

        grupos[clave]["eventos"] = grupos[clave]["eventos"] + 1
        grupos[clave]["bateria_total"] = grupos[clave]["bateria_total"] + bateria
        grupos[clave]["distancia_total_m"] = grupos[clave]["distancia_total_m"] + distancia
        grupos[clave]["hora_total"] = grupos[clave]["hora_total"] + hora

        if vehiculo not in grupos[clave]["vehiculos"]:
            grupos[clave]["vehiculos"].append(vehiculo)

        i = i + 1

    return grupos


def crear_dataset_candidatos(grupos):
    x = []
    y = []
    claves = []

    for clave, datos in grupos.items():
        eventos = datos["eventos"]

        if eventos > 0:
            bateria_promedio = datos["bateria_total"] / eventos
            distancia_promedio = datos["distancia_total_m"] / eventos
            hora_promedio = datos["hora_total"] / eventos
        else:
            bateria_promedio = 0.0
            distancia_promedio = 0.0
            hora_promedio = 0.0

        x.append([
            datos["lat"],
            datos["lon"],
            bateria_promedio,
            distancia_promedio,
            hora_promedio,
            len(datos["vehiculos"]),
        ])
        y.append(eventos)
        claves.append(clave)

    return x, y, claves


def recomendar_nuevas_electrolineras():
    # usa regresion con bosque aleatorio para estimar demanda por coordenada de bateria baja
    if not SKLEARN_DISPONIBLE:
        print("scikit-learn o joblib no estan instalados.")
        return []

    grupos = agrupar_eventos_bateria_baja()

    if len(grupos) == 0:
        print("no hay coordenadas de bateria baja. ejecute una simulacion nueva.")
        return []

    x, y, claves = crear_dataset_candidatos(grupos)

    if len(x) < 2:
        print("faltan candidatos para entrenar el recomendador de nuevas electrolineras.")
        return []

    modelo = RandomForestRegressor(n_estimators=80, random_state=42)
    inicio = time.perf_counter()
    modelo.fit(x, y)
    fin = time.perf_counter()
    tiempo_entrenamiento = (fin - inicio) * 1000

    inicio = time.perf_counter()
    puntajes = modelo.predict(x)
    fin = time.perf_counter()
    tiempo_prediccion = (fin - inicio) * 1000

    recomendaciones = []

    i = 0
    while i < len(claves):
        datos = grupos[claves[i]]
        eventos = datos["eventos"]
        bateria_promedio = datos["bateria_total"] / eventos
        distancia_promedio = datos["distancia_total_m"] / eventos

        recomendaciones.append({
            "punto": datos["punto"],
            "lat": datos["lat"],
            "lon": datos["lon"],
            "eventos_bateria_baja": eventos,
            "bateria_promedio": round(bateria_promedio, 2),
            "distancia_promedio_a_electrolinera_m": round(distancia_promedio, 1),
            "vehiculos_distintos": len(datos["vehiculos"]),
            "puntaje_ml_demanda": round(float(puntajes[i]), 4),
        })
        i = i + 1

    recomendaciones = ordenar_recomendaciones(recomendaciones)
    paquete = {
        "modelo": "random_forest_regressor",
        "objetivo": "estimar demanda de nuevas electrolineras por coordenada de bateria baja",
        "tiempo_entrenamiento_ms": round(tiempo_entrenamiento, 3),
        "tiempo_prediccion_ms": round(tiempo_prediccion, 3),
        "recomendaciones": recomendaciones,
    }

    guardar_json("recomendaciones_nuevas_electrolineras", paquete)
    joblib.dump({"modelo": modelo, "nombre": "recomendador_nuevas_electrolineras"}, ruta_modelo("modelo_recomendador_nuevas.pkl"))

    print()
    print("recomendaciones de nuevas electrolineras guardadas.")
    mostrar_recomendaciones(recomendaciones)
    return recomendaciones


def ordenar_recomendaciones(recomendaciones):
    i = 0
    while i < len(recomendaciones):
        j = 0
        while j < len(recomendaciones) - 1:
            actual = recomendaciones[j]
            siguiente = recomendaciones[j + 1]

            if actual["puntaje_ml_demanda"] < siguiente["puntaje_ml_demanda"]:
                temporal = recomendaciones[j]
                recomendaciones[j] = recomendaciones[j + 1]
                recomendaciones[j + 1] = temporal
            elif actual["puntaje_ml_demanda"] == siguiente["puntaje_ml_demanda"]:
                if actual["distancia_promedio_a_electrolinera_m"] < siguiente["distancia_promedio_a_electrolinera_m"]:
                    temporal = recomendaciones[j]
                    recomendaciones[j] = recomendaciones[j + 1]
                    recomendaciones[j + 1] = temporal

            j = j + 1
        i = i + 1

    return recomendaciones


def mostrar_recomendaciones(recomendaciones):
    if len(recomendaciones) == 0:
        print("no hay recomendaciones disponibles.")
        return

    print()
    print("top de ubicaciones candidatas para nuevas electrolineras")
    limite = 5

    if len(recomendaciones) < limite:
        limite = len(recomendaciones)

    i = 0
    while i < limite:
        rec = recomendaciones[i]
        print(
            str(i + 1) + ".",
            rec["punto"],
            "| coordenadas:",
            rec["lat"],
            rec["lon"],
            "| eventos:",
            rec["eventos_bateria_baja"],
            "| puntaje ml:",
            rec["puntaje_ml_demanda"],
        )
        i = i + 1
