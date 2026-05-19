# visualizacion de mapas y graficos del proyecto
# folium genera el mapa html y matplotlib genera el grafico de barras

import os

from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA, VEHICULOS
from recursos.utilidades.archivos import ruta_salida


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

                if coord is not None:
                    # el mejor candidato (posicion 0) va en naranja mas grande
                    if i == 0:
                        color_circulo = "orange"
                        radio         = 400 + cantidad * 80
                        texto_popup   = (
                            "<b>MEJOR CANDIDATO PARA NUEVA ELECTROLINERA</b><br>"
                            "lugar: " + nombre_lugar + "<br>"
                            "eventos de bateria baja: " + str(cantidad) + "<br>"
                            "este punto concentra la mayor demanda no cubierta"
                        )
                    else:
                        color_circulo = "yellow"
                        radio         = 200 + cantidad * 50
                        texto_popup   = (
                            "<b>zona candidata</b><br>"
                            "lugar: " + nombre_lugar + "<br>"
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
      zona candidata
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


# =========================================================
# GRAFICO DE BARRAS
# =========================================================

def generar_grafico_dispersion(estadisticas):
    """
    Grafico de dispersion: cada punto es una ELECTROLINERA.
    Tamaño = cuantas veces se uso (chocolate = grande, galleta = pequeno).
    Muestra cuales estan aisladas y necesitan apoyo.
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
        
        # Color: rojo si muy usada (chocolate), azul si poco usada (galleta)
        if veces_usada >= 50:
            lista_colores.append("darkred")    # chocolate: super popular
        elif veces_usada >= 20:
            lista_colores.append("red")         # bastante usada
        elif veces_usada >= 5:
            lista_colores.append("orange")      # regular
        else:
            lista_colores.append("blue")        # galleta: aislada, poco usada
        
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
    plt.title("electrolineras: chocolate vs galleta\n" +
              "circulos grandes/rojos = muy usadas (chocolate)\n" +
              "circulos pequenos/azules = aisladas (galleta - necesitan apoyo)")
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    ruta = ruta_salida("dispersion_electrolineras_chocolate_galleta.png")
    plt.savefig(ruta, dpi=150)
    plt.close()
    
    # Resumen
    print()
    print("=" * 50)
    print("RESUMEN: Chocolate vs Galleta")
    print("=" * 50)
    
    i = 0
    while i < len(lista_nombres):
        tipo = ""
        if lista_usos[i] >= 50:
            tipo = "CHOCOLATE (super popular)"
        elif lista_usos[i] >= 20:
            tipo = "chocolate (bastante usada)"
        elif lista_usos[i] >= 5:
            tipo = "regular"
        else:
            tipo = "GALLETA (aislada - necesita electrolinera cerca)"
        
        print(lista_nombres[i] + ":", lista_usos[i], "usos -", tipo)
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
