# modelo sencillo de machine learning para predecir electrolineras
# se entrena con el historial de recargas generado por la simulacion

import warnings
import time

from recursos.utilidades.archivos import guardar_json, leer_csv, ruta_modelo


try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier
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
