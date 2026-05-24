# visualizacion de mapas y graficos del proyecto
# folium genera el mapa html y matplotlib genera el grafico de barras

import os

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


# =========================================================
# MAPA INTERACTIVO
# =========================================================

def generar_mapa(estadisticas=None, grafo=None):
    # crea un mapa html con:
    # - marcadores rojos para electrolineras existentes
    # - marcadores azules para puntos de referencia
    # - lineas verdes para las rutas que hicieron los vehiculos
    # - circulos amarillos para zonas candidatas a nueva electrolinera
    # - circulo naranja para el mejor candidato segun el ML o la frecuencia

    if not FOLIUM_DISPONIBLE:
        print("folium no esta instalado. no se pudo generar el mapa.")
        return ""

    mapa = folium.Map(location=[7.0800, -73.1050], zoom_start=11)
    puntos_mapa = []

    # ── electrolineras existentes (marcadores rojos) ──────────
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

    # ── puntos de referencia (marcadores azules) ──────────────
    i = 0
    while i < len(PUNTOS_REFERENCIA):
        punto = PUNTOS_REFERENCIA[i]
        puntos_mapa.append([punto["lat"], punto["lon"]])
        texto = "<b>" + punto["nombre"] + "</b><br>id: " + punto["id"]
        folium.Marker(
            location=[punto["lat"], punto["lon"]],
            popup=folium.Popup(texto, max_width=250),
            tooltip=punto["nombre"],
            icon=folium.Icon(color="blue", icon="university", prefix="fa"),
        ).add_to(mapa)
        i = i + 1

    # ── rutas de la simulacion (lineas verdes) ────────────────
    # cada recorrido guarda el origen y destino con nombre
    # buscamos las coordenadas reales de esos puntos y dibujamos la linea
    if estadisticas and grafo is not None:
        recorridos = estadisticas.get("recorridos", [])

        i = 0
        while i < len(recorridos):
            rec = recorridos[i]
            origen_nombre  = rec.get("origen", "")
            destino_nombre = rec.get("destino", "")

            coord_origen  = buscar_coordenadas(origen_nombre)
            coord_destino = buscar_coordenadas(destino_nombre)

            if coord_origen is not None and coord_destino is not None:
                # linea verde normal para recorridos sin recarga
                # linea naranja para recorridos donde hubo recarga
                if rec.get("recarga_activada", False):
                    color_linea = "orange"
                    grosor      = 3
                else:
                    color_linea = "green"
                    grosor      = 2

                tooltip_ruta = (
                    rec.get("vehiculo", "") + " | " +
                    origen_nombre + " → " + destino_nombre + " | " +
                    str(rec.get("distancia_km", "")) + " km"
                )

                folium.PolyLine(
                    locations=[coord_origen, coord_destino],
                    color=color_linea,
                    weight=grosor,
                    opacity=0.6,
                    tooltip=tooltip_ruta,
                ).add_to(mapa)

            i = i + 1

    # ── zonas candidatas para nuevas electrolineras ───────────
    # puntos_candidatos guarda cuantas veces bajo la bateria en cada lugar
    # entre mas veces, mas urgente es una electrolinera ahi
    if estadisticas:
        candidatos = estadisticas.get("puntos_candidatos", {})
        candidatos_detalle = estadisticas.get("puntos_candidatos_detalle", {})

        if len(candidatos) > 0:
            # ordenar de mayor a menor para pintar primero los mas importantes
            lista_candidatos = []
            for nombre_lugar, cantidad in candidatos.items():
                lista_candidatos.append([nombre_lugar, cantidad])

            # burbuja de mayor a menor
            j = 0
            while j < len(lista_candidatos):
                k = 0
                while k < len(lista_candidatos) - 1:
                    if lista_candidatos[k][1] < lista_candidatos[k + 1][1]:
                        temp                    = lista_candidatos[k]
                        lista_candidatos[k]     = lista_candidatos[k + 1]
                        lista_candidatos[k + 1] = temp
                    k = k + 1
                j = j + 1

            # dibujar circulos amarillos para todos los candidatos
            # el radio es proporcional a la frecuencia de bateria baja
            i = 0
            while i < len(lista_candidatos):
                nombre_lugar = lista_candidatos[i][0]
                cantidad     = lista_candidatos[i][1]
                coord        = buscar_coordenadas(nombre_lugar)
                coord_exacta = buscar_coordenada_candidata(nombre_lugar, candidatos_detalle)

                if coord_exacta is not None:
                    coord = coord_exacta

                if coord is not None:
                    # el mejor candidato (posicion 0) va en naranja mas grande
                    if i == 0:
                        color_circulo = "orange"
                        radio         = 400 + cantidad * 80
                        texto_popup   = (
                            "<b>MEJOR CANDIDATO PARA NUEVA ELECTROLINERA</b><br>"
                            "lugar: " + nombre_lugar + "<br>"
                            "coordenadas exactas: " + str(coord[0]) + ", " + str(coord[1]) + "<br>"
                            "eventos de bateria baja: " + str(cantidad) + "<br>"
                            "este punto concentra la mayor demanda no cubierta"
                        )
                    else:
                        color_circulo = "yellow"
                        radio         = 200 + cantidad * 50
                        texto_popup   = (
                            "<b>zona candidata</b><br>"
                            "lugar: " + nombre_lugar + "<br>"
                            "coordenadas exactas: " + str(coord[0]) + ", " + str(coord[1]) + "<br>"
                            "eventos de bateria baja: " + str(cantidad)
                        )

                    folium.Circle(
                        location=coord,
                        radius=radio,
                        color=color_circulo,
                        fill=True,
                        fill_color=color_circulo,
                        fill_opacity=0.35,
                        popup=folium.Popup(texto_popup, max_width=300),
                        tooltip="candidato: " + nombre_lugar,
                    ).add_to(mapa)

                i = i + 1

    agregar_recomendaciones_ml(mapa)

    # ── leyenda ───────────────────────────────────────────────
    leyenda = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 12px; border: 2px solid #cccccc;
                font-size: 13px; border-radius: 6px;">
      <b>leyenda</b><br><br>
      <span style="display:inline-block;width:12px;height:12px;
                   background:red;border-radius:50%;margin-right:6px;"></span>
      electrolinera existente<br>
      <span style="display:inline-block;width:12px;height:12px;
                   background:blue;border-radius:50%;margin-right:6px;"></span>
      punto de referencia<br>
      <span style="display:inline-block;width:30px;height:4px;
                   background:green;margin-right:6px;vertical-align:middle;"></span>
      ruta simulada<br>
      <span style="display:inline-block;width:30px;height:4px;
                   background:orange;margin-right:6px;vertical-align:middle;"></span>
      ruta con recarga<br>
      <span style="display:inline-block;width:12px;height:12px;
                   background:orange;border-radius:50%;margin-right:6px;
                   opacity:0.6;"></span>
      mejor candidato nueva electrolinera<br>
      <span style="display:inline-block;width:12px;height:12px;
                   background:yellow;border-radius:50%;margin-right:6px;
                   opacity:0.6;border:1px solid #aaa;"></span>
      zona candidata<br>
      <span style="display:inline-block;width:12px;height:12px;
                   background:purple;border-radius:50%;margin-right:6px;
                   opacity:0.6;"></span>
      recomendacion ML
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(leyenda))

    if len(puntos_mapa) > 0:
        mapa.fit_bounds(puntos_mapa, padding=[30, 30])

    ruta = ruta_salida("mapa_electrolineras.html")
    mapa.save(ruta)
    print("mapa guardado en:", ruta)
    return ruta


# =========================================================
# BUSCAR COORDENADAS DE UN LUGAR POR NOMBRE
# =========================================================

def buscar_coordenadas(nombre_lugar):
    # busca las coordenadas de un lugar buscando su nombre
    # en la lista de electrolineras y puntos de referencia
    # devuelve [lat, lon] o None si no lo encuentra

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


def buscar_coordenada_candidata(nombre_lugar, candidatos_detalle):
    for clave, datos in candidatos_detalle.items():
        if datos.get("punto") == nombre_lugar:
            lat = datos.get("lat", "")
            lon = datos.get("lon", "")

            if lat != "" and lon != "":
                return [float(lat), float(lon)]

    return None


def agregar_recomendaciones_ml(mapa):
    datos = leer_json("recomendaciones_nuevas_electrolineras")

    if datos is None:
        return

    recomendaciones = datos.get("recomendaciones", [])

    i = 0
    while i < len(recomendaciones):
        rec = recomendaciones[i]
        lat = rec.get("lat", "")
        lon = rec.get("lon", "")

        if lat != "" and lon != "":
            radio = 250 + rec.get("puntaje_ml_demanda", 0) * 60

            if i == 0:
                color = "purple"
                texto_titulo = "MEJOR RECOMENDACION ML"
            else:
                color = "cadetblue"
                texto_titulo = "recomendacion ML"

            texto = (
                "<b>" + texto_titulo + "</b><br>"
                "punto: " + str(rec.get("punto", "")) + "<br>"
                "coordenadas: " + str(lat) + ", " + str(lon) + "<br>"
                "eventos bateria baja: " + str(rec.get("eventos_bateria_baja", "")) + "<br>"
                "distancia promedio a electrolinera: " + str(rec.get("distancia_promedio_a_electrolinera_m", "")) + " m<br>"
                "puntaje ML: " + str(rec.get("puntaje_ml_demanda", ""))
            )

            folium.Circle(
                location=[lat, lon],
                radius=radio,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.28,
                popup=folium.Popup(texto, max_width=320),
                tooltip=texto_titulo + ": " + str(rec.get("punto", "")),
            ).add_to(mapa)

        i = i + 1


# =========================================================
# GRAFICO DE BARRAS
# =========================================================

def generar_grafico_dispersion(estadisticas):
    """
    Grafico de dispersion: cada punto es una ELECTROLINERA.
    Tamano = cuantas veces se uso.
    Muestra demanda alta, media y baja por ubicacion.
    """
    if not MATPLOTLIB_DISPONIBLE:
        print("matplotlib no esta instalado. no se pudo generar el grafico.")
        return ""

    if not estadisticas:
        print("no hay estadisticas para graficar.")
        return ""

    # =========================================================
    # OBTENER USO DE ELECTROLINERAS
    # =========================================================
    
    uso = {}
    uso_por_id = {}
    
    if "uso_electrolineras" in estadisticas:
        uso = estadisticas["uso_electrolineras"]

    if "uso_electrolineras_id" in estadisticas:
        uso_por_id = estadisticas["uso_electrolineras_id"]

    # =========================================================
    # PREPARAR DATOS: lat, lon, uso, nombre
    # =========================================================
    
    lista_lats = []
    lista_lons = []
    lista_usos = []
    lista_nombres = []
    lista_colores = []
    lista_tamanos = []
    
    # Recorrer todas las electrolineras definidas en datos.data
    i = 0
    while i < len(ELECTROLINERAS):
        elec = ELECTROLINERAS[i]
        nombre = elec["nombre"]
        id_electrolinera = elec["id"]
        
        # Buscar cuantas veces se uso
        veces_usada = 0
        if id_electrolinera in uso_por_id:
            veces_usada = uso_por_id[id_electrolinera]
        elif nombre in uso:
            veces_usada = uso[nombre]
        
        # Coordenadas
        lat = elec["lat"]
        lon = elec["lon"]
        
        lista_lats.append(lat)
        lista_lons.append(lon)
        lista_usos.append(veces_usada)
        lista_nombres.append(nombre)
        
        # Tamaño proporcional al uso (minimo 100, maximo 2000)
        tamano = 100 + (veces_usada * 30)
        if tamano > 2000:
            tamano = 2000
        if tamano < 100:
            tamano = 100
        lista_tamanos.append(tamano)
        
        # Color segun el nivel de uso de cada electrolinera
        if veces_usada >= 50:
            lista_colores.append("darkred")
        elif veces_usada >= 20:
            lista_colores.append("red")
        elif veces_usada >= 5:
            lista_colores.append("orange")
        else:
            lista_colores.append("blue")
        
        i = i + 1

    # =========================================================
    # CREAR GRAFICO
    # =========================================================
    
    plt.figure(figsize=(12, 10))
    
    # Graficar cada electrolinera
    i = 0
    while i < len(lista_lats):
        plt.scatter(
            lista_lons[i],
            lista_lats[i],
            s=lista_tamanos[i],
            c=lista_colores[i],
            alpha=0.6,
            edgecolors="black",
            linewidths=2
        )
        
        # Etiqueta con nombre y uso
        plt.annotate(
            lista_nombres[i] + "\n(" + str(lista_usos[i]) + " usos)",
            (lista_lons[i], lista_lats[i]),
            textcoords="offset points",
            xytext=(0, 15),
            ha="center",
            fontsize=9,
            fontweight="bold"
        )
        
        i = i + 1
    
    # Graficar puntos de referencia (pequenos, grises)
    i = 0
    while i < len(PUNTOS_REFERENCIA):
        punto = PUNTOS_REFERENCIA[i]
        plt.scatter(
            punto["lon"],
            punto["lat"],
            s=30,
            c="lightgray",
            alpha=0.5,
            marker="s"
        )
        i = i + 1
    
    plt.xlabel("longitud")
    plt.ylabel("latitud")
    plt.title("uso de electrolineras por ubicacion\n" +
              "circulos grandes/rojos = alta demanda\n" +
              "circulos pequenos/azules = baja demanda")
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    ruta = ruta_salida("dispersion_uso_electrolineras.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    
    # Resumen
    print()
    print("=" * 50)
    print("RESUMEN: Uso de electrolineras")
    print("=" * 50)
    
    i = 0
    while i < len(lista_nombres):
        tipo = ""
        if lista_usos[i] >= 50:
            tipo = "demanda muy alta"
        elif lista_usos[i] >= 20:
            tipo = "demanda alta"
        elif lista_usos[i] >= 5:
            tipo = "demanda media"
        else:
            tipo = "demanda baja"
        
        print(lista_nombres[i] + ":", lista_usos[i], "usos -", tipo)
        i = i + 1
    
    print()
    print("grafico guardado en:", ruta)
    return ruta


def generar_grafico_dispersion(estadisticas):
    """
    Grafico mejorado de uso de electrolineras.
    Muestra demanda por estacion, puntos de referencia y candidatos detectados.
    """
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
    usos = []
    nombres = []
    tamanos = []

    i = 0
    while i < len(ELECTROLINERAS):
        elec = ELECTROLINERAS[i]
        nombre = elec["nombre"]
        id_electrolinera = elec["id"]
        veces_usada = 0

        if id_electrolinera in uso_por_id:
            veces_usada = uso_por_id[id_electrolinera]
        elif nombre in uso:
            veces_usada = uso[nombre]

        lats.append(elec["lat"])
        lons.append(elec["lon"])
        usos.append(veces_usada)
        nombres.append(nombre)

        tamano = 140 + (veces_usada ** 0.5) * 120
        if tamano > 1700:
            tamano = 1700
        tamanos.append(tamano)
        i = i + 1

    figura, eje = plt.subplots(figsize=(13, 9))
    figura.patch.set_facecolor("#f8fafc")
    eje.set_facecolor("#ffffff")

    eje.scatter(
        [p["lon"] for p in PUNTOS_REFERENCIA],
        [p["lat"] for p in PUNTOS_REFERENCIA],
        s=42,
        c="#94a3b8",
        marker="s",
        alpha=0.65,
        label="puntos de referencia",
    )

    max_uso = max(usos) if len(usos) > 0 else 0
    dispersion = eje.scatter(
        lons,
        lats,
        s=tamanos,
        c=usos,
        cmap="YlOrRd",
        vmin=0,
        vmax=max_uso if max_uso > 0 else 1,
        alpha=0.82,
        edgecolors="#111827",
        linewidths=1.2,
        label="electrolineras",
    )

    offsets = [(10, 10), (10, -18), (-10, 12), (-10, -20)]
    i = 0
    while i < len(nombres):
        offset = offsets[i % len(offsets)]
        eje.annotate(
            nombres[i] + "\n" + str(usos[i]) + " usos",
            (lons[i], lats[i]),
            textcoords="offset points",
            xytext=offset,
            ha="left" if offset[0] >= 0 else "right",
            fontsize=8,
            color="#111827",
            bbox={
                "boxstyle": "round,pad=0.25",
                "fc": "white",
                "ec": "#cbd5e1",
                "alpha": 0.88,
            },
        )
        i = i + 1

    detalles_candidatos = estadisticas.get("puntos_candidatos_detalle", {})
    candidatos_lats = []
    candidatos_lons = []
    candidatos_eventos = []

    for clave, datos in detalles_candidatos.items():
        lat = datos.get("lat", "")
        lon = datos.get("lon", "")

        if lat != "" and lon != "":
            candidatos_lats.append(float(lat))
            candidatos_lons.append(float(lon))
            candidatos_eventos.append(datos.get("eventos", 1))

    if len(candidatos_lats) > 0:
        tamanos_candidatos = []
        i = 0
        while i < len(candidatos_eventos):
            tamanos_candidatos.append(150 + candidatos_eventos[i] * 70)
            i = i + 1

        eje.scatter(
            candidatos_lons,
            candidatos_lats,
            s=tamanos_candidatos,
            marker="X",
            c="#7c3aed",
            edgecolors="white",
            linewidths=1.2,
            alpha=0.9,
            label="candidatos por bateria baja",
        )

    barra = figura.colorbar(dispersion, ax=eje, shrink=0.82, pad=0.02)
    barra.set_label("recargas registradas", fontsize=10)

    eje.set_title(
        "Uso espacial de electrolineras y zonas candidatas",
        fontsize=16,
        fontweight="bold",
        color="#0f172a",
        pad=16,
    )
    eje.set_xlabel("longitud", fontsize=11)
    eje.set_ylabel("latitud", fontsize=11)
    eje.grid(True, color="#e2e8f0", linewidth=0.8)
    eje.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#cbd5e1")

    if len(lats) > 0:
        eje.set_xlim(min(lons) - 0.015, max(lons) + 0.015)
        eje.set_ylim(min(lats) - 0.015, max(lats) + 0.015)

    plt.tight_layout()
    ruta = ruta_salida("dispersion_uso_electrolineras.png")
    plt.savefig(ruta, dpi=170)
    plt.close()

    print()
    print("=" * 50)
    print("RESUMEN: Uso de electrolineras")
    print("=" * 50)

    i = 0
    while i < len(nombres):
        if usos[i] >= 50:
            tipo = "demanda muy alta"
        elif usos[i] >= 20:
            tipo = "demanda alta"
        elif usos[i] >= 5:
            tipo = "demanda media"
        else:
            tipo = "demanda baja"

        print(nombres[i] + ":", usos[i], "usos -", tipo)
        i = i + 1

    print()
    print("grafico guardado en:", ruta)
    return ruta


def mostrar_vehiculos_en_mapa():
    # devuelve un texto con los vehiculos usados
    texto = []
    claves = list(VEHICULOS.keys())

    i = 0
    while i < len(claves):
        vehiculo = VEHICULOS[claves[i]]
        texto.append(vehiculo["nombre"] + " - " + vehiculo["gama"])
        i = i + 1

    return ", ".join(texto)
