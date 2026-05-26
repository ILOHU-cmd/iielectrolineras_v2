# visualizacion sencilla de mapas y graficos del proyecto

from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS
from recursos.utilidades.archivos import leer_json, ruta_salida


try:
    import folium
    FOLIUM_DISPONIBLE = True
except ImportError:
    FOLIUM_DISPONIBLE = False


try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


def generar_mapa(estadisticas=None, grafo=None):
    # mapa html con electrolineras, puntos de referencia y candidatos
    if not FOLIUM_DISPONIBLE:
        print("folium no esta instalado. no se pudo generar el mapa.")
        return ""

    mapa = folium.Map(location=[7.0800, -73.1050], zoom_start=11)
    puntos_mapa = []

    i = 0
    while i < len(ELECTROLINERAS):
        estacion = ELECTROLINERAS[i]
        puntos_mapa.append([estacion["lat"], estacion["lon"]])
        texto = (
            "<b>" + estacion["nombre"] + "</b><br>"
            "id: " + estacion["id"] + "<br>"
            "potencia: " + str(estacion["potencia_kw"]) + " kw"
        )
        folium.Marker(
            location=[estacion["lat"], estacion["lon"]],
            popup=folium.Popup(texto, max_width=250),
            tooltip=estacion["nombre"],
            icon=folium.Icon(color="red", icon="bolt", prefix="fa"),
        ).add_to(mapa)
        i = i + 1

    i = 0
    while i < len(PUNTOS_REFERENCIA):
        punto = PUNTOS_REFERENCIA[i]
        puntos_mapa.append([punto["lat"], punto["lon"]])
        folium.Marker(
            location=[punto["lat"], punto["lon"]],
            popup=folium.Popup("<b>" + punto["nombre"] + "</b><br>id: " + punto["id"], max_width=250),
            tooltip=punto["nombre"],
            icon=folium.Icon(color="blue", icon="university", prefix="fa"),
        ).add_to(mapa)
        i = i + 1

    if estadisticas:
        dibujar_rutas_simuladas(mapa, estadisticas)
        dibujar_candidatos(mapa, estadisticas)

    dibujar_recomendaciones_ml(mapa)
    agregar_leyenda(mapa)

    if len(puntos_mapa) > 0:
        mapa.fit_bounds(puntos_mapa, padding=[30, 30])

    ruta = ruta_salida("mapa_electrolineras.html")
    mapa.save(ruta)
    print("mapa guardado en:", ruta)
    return ruta


def dibujar_rutas_simuladas(mapa, estadisticas):
    recorridos = estadisticas.get("recorridos", [])
    limite = len(recorridos)

    if limite > 60:
        limite = 60

    i = 0
    while i < limite:
        rec = recorridos[i]
        coord_origen = buscar_coordenadas(rec.get("origen", ""))
        coord_destino = buscar_coordenadas(rec.get("destino", ""))

        if coord_origen is not None and coord_destino is not None:
            color = "orange" if rec.get("recarga_activada", False) else "green"
            folium.PolyLine(
                locations=[coord_origen, coord_destino],
                color=color,
                weight=2,
                opacity=0.55,
                tooltip=rec.get("vehiculo", "") + " | " + str(rec.get("distancia_km", "")) + " km",
            ).add_to(mapa)

        i = i + 1


def dibujar_candidatos(mapa, estadisticas):
    detalles = estadisticas.get("puntos_candidatos_detalle", {})

    for clave, datos in detalles.items():
        lat = datos.get("lat", "")
        lon = datos.get("lon", "")

        if lat != "" and lon != "":
            eventos = datos.get("eventos", 1)
            texto = (
                "<b>candidato para nueva electrolinera</b><br>"
                "punto: " + str(datos.get("punto", "")) + "<br>"
                "coordenadas: " + str(lat) + ", " + str(lon) + "<br>"
                "eventos: " + str(eventos)
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=6 + eventos,
                color="purple",
                fill=True,
                fill_color="purple",
                fill_opacity=0.55,
                popup=folium.Popup(texto, max_width=280),
                tooltip="candidato: " + str(datos.get("punto", "")),
            ).add_to(mapa)


def dibujar_recomendaciones_ml(mapa):
    datos = leer_json("recomendaciones_nuevas_electrolineras")

    if datos is None:
        return

    recomendaciones = datos.get("recomendaciones", [])
    limite = len(recomendaciones)

    if limite > 5:
        limite = 5

    i = 0
    while i < limite:
        rec = recomendaciones[i]
        lat = rec.get("lat", "")
        lon = rec.get("lon", "")

        if lat != "" and lon != "":
            texto = (
                "<b>recomendacion ML</b><br>"
                "punto: " + str(rec.get("punto", "")) + "<br>"
                "coordenadas: " + str(lat) + ", " + str(lon) + "<br>"
                "puntaje: " + str(rec.get("puntaje_ml_demanda", ""))
            )
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(texto, max_width=280),
                tooltip="recomendacion ML",
                icon=folium.Icon(color="purple", icon="plus", prefix="fa"),
            ).add_to(mapa)

        i = i + 1


def agregar_leyenda(mapa):
    leyenda = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 10px; border: 1px solid #999;
                font-size: 13px;">
      <b>leyenda</b><br>
      rojo: electrolinera<br>
      azul: punto de referencia<br>
      verde: recorrido simulado<br>
      naranja: recorrido con recarga<br>
      morado: candidato o recomendacion ML
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda))


def buscar_coordenadas(nombre_lugar):
    i = 0
    while i < len(ELECTROLINERAS):
        if ELECTROLINERAS[i]["nombre"] == nombre_lugar:
            return [ELECTROLINERAS[i]["lat"], ELECTROLINERAS[i]["lon"]]
        i = i + 1

    i = 0
    while i < len(PUNTOS_REFERENCIA):
        if PUNTOS_REFERENCIA[i]["nombre"] == nombre_lugar:
            return [PUNTOS_REFERENCIA[i]["lat"], PUNTOS_REFERENCIA[i]["lon"]]
        i = i + 1

    return None


def generar_grafico_dispersion(estadisticas):
    # grafico basico: ubicacion de electrolineras y cantidad de recargas
    if not MATPLOTLIB_DISPONIBLE:
        print("matplotlib no esta instalado. no se pudo generar el grafico.")
        return ""

    if not estadisticas:
        print("no hay estadisticas para graficar.")
        return ""

    uso = estadisticas.get("uso_electrolineras", {})
    uso_por_id = estadisticas.get("uso_electrolineras_id", {})
    lats = []
    lons = []
    tamanos = []
    colores = []
    nombres = []
    usos = []

    i = 0
    while i < len(ELECTROLINERAS):
        elec = ELECTROLINERAS[i]
        veces = 0

        if elec["id"] in uso_por_id:
            veces = uso_por_id[elec["id"]]
        elif elec["nombre"] in uso:
            veces = uso[elec["nombre"]]

        lats.append(elec["lat"])
        lons.append(elec["lon"])
        usos.append(veces)
        nombres.append(elec["nombre"])
        tamanos.append(80 + veces * 20)

        if veces >= 20:
            colores.append("red")
        elif veces >= 5:
            colores.append("orange")
        else:
            colores.append("blue")

        i = i + 1

    plt.figure(figsize=(10, 7))
    plt.scatter(lons, lats, s=tamanos, c=colores, alpha=0.7, edgecolors="black")

    i = 0
    while i < len(nombres):
        plt.text(lons[i], lats[i], nombres[i] + " (" + str(usos[i]) + ")", fontsize=8)
        i = i + 1

    plt.xlabel("longitud")
    plt.ylabel("latitud")
    plt.title("uso de electrolineras")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    ruta = ruta_salida("dispersion_uso_electrolineras.png")
    plt.savefig(ruta, dpi=120)
    plt.close()

    print()
    print("resumen de uso de electrolineras")
    i = 0
    while i < len(nombres):
        print(nombres[i] + ":", usos[i], "recargas")
        i = i + 1

    print("grafico guardado en:", ruta)
    return ruta


def mostrar_vehiculos_en_mapa():
    texto = []
    claves = list(VEHICULOS.keys())

    i = 0
    while i < len(claves):
        vehiculo = VEHICULOS[claves[i]]
        texto.append(vehiculo["nombre"] + " - " + vehiculo["gama"])
        i = i + 1

    return ", ".join(texto)
