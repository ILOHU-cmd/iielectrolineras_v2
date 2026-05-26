# datos del proyecto: electrolineras, puntos de referencia y vehiculos
# primero intenta geocodificar probando las 4 ciudades del area metropolitana
# si el lugar no esta en osm se usan las coordenadas manuales como respaldo

import osmnx as ox


# ciudades del area metropolitana que se prueban en orden
CIUDADES = [
    "Bucaramanga, Santander, Colombia",
    "Floridablanca, Santander, Colombia",
    "Giron, Santander, Colombia",
    "Piedecuesta, Santander, Colombia",
]

def geocodificar(nombre, lat_manual=None, lon_manual=None):
   
    # PRIORIDAD 1: usar coordenadas manuales si existen
    

    if lat_manual is not None and lon_manual is not None:
        return lat_manual, lon_manual, "Manual"

 
    # PRIORIDAD 2: intentar buscar en OSM
 

    i = 0

    while i < len(CIUDADES):

        try:
            consulta = nombre + ", " + CIUDADES[i]

            coords = ox.geocode(consulta)

            return coords[0], coords[1], CIUDADES[i].split(",")[0]

        except Exception:
            pass

        i += 1

 
    # SI NO ENCUENTRA NADA
 

    return None



# ELECTROLINERAS


lugares_busqueda = [
    {
        "id": "E1",
        "nombre": "Homecenter Bucaramanga",
        "potencia_kw": 50
    },
    {
        "id": "E2",
        "nombre": "Centro Comercial Quinta Etapa",
        "potencia_kw": 22,
        "lat": 7.115484517100732,
        "lon": -73.10763988929288
    },
    {
        "id": "E3",
        "nombre": "Centro Comercial Cacique",

    "lat": 7.099254238710049, "lon": -73.10795932316336,
        "potencia_kw": 50
    },
    {
        "id": "E4",
        "nombre": "Centro Comercial Canaveral",
        "potencia_kw": 22
    },
    {
        "id": "E5",
        "nombre": "Estacion de Servicio Terpel",

        "lat": 6.998112154358705, "lon": -73.05208417111548,
        "potencia_kw": 50
    },
    {
        "id": "E6",
        "nombre": "Exito La Rosita",
        "potencia_kw": 22
    },
    {
        "id": "E7",
        "nombre": "Centro Comercial La Florida",
        "lat": 7.070653288590229, "lon": -73.10520776140858,
        "potencia_kw": 22
    },
    {
        "id": "E8",
        "nombre": "Promotores del Oriente",
        "lat": 7.0851407748093775, "lon": -73.1645703641285,
        "potencia_kw": 50
    }
]

ELECTROLINERAS = []

for lugar in lugares_busqueda:
    resultado = geocodificar(
        lugar["nombre"],
        lugar.get("lat"),
        lugar.get("lon")
    )

    if resultado is not None:
        lat = resultado[0]
        lon = resultado[1]
        ciudad = resultado[2]

        ELECTROLINERAS.append({
            "id": lugar["id"],
            "nombre": lugar["nombre"],
            "lat": lat,
            "lon": lon,
            "potencia_kw": lugar["potencia_kw"]
        })

        print("OK    " + lugar["id"] + " | " + lugar["nombre"] + " -> " + str(round(lat, 6)) + ", " + str(round(lon, 6)) + " (" + ciudad + ")")

    else:
        print("ERROR " + lugar["id"] + " | " + lugar["nombre"] + ": no encontrado en osm y sin coordenadas manuales")



# PUNTOS FIJOS DE REFERENCIA


lugares_referencia = [
    {
        "id": "P1",
        "nombre": "Universidad Industrial de Santander"
    },
    {
        "id": "P2",
        "nombre": "Universidad Industrial de Santander - Sede Floridablanca"
    },
    {
        "id": "P3",
        "nombre": "Universidad Industrial de Santander - Sede guatiguara"
    },
    {
        "id": "P4",
        "nombre": "Universidad Industrial de Santander Sede Bucarica"
    },
    {
        "id": "P5",
        "nombre": "CENFER Bucaramanga",
        "lat": 7.082846, "lon": -73.152187
    },
    {
        "id": "P6",
        "nombre": "Universidad Autonoma de Bucaramanga"
    },
    {
        "id": "P7",
        "nombre": "Unidades Tecnologicas de Santander"
    },
    {
        "id": "P8",
        "nombre": "Universidad Pontificia Bolivariana"
    },
    {
        # ptar rio frio no aparece en osm, se usan coordenadas manuales
        "id": "P9",
        "nombre": "PTAR Rio Frio","lat": 7.0656867849653056, "lon": -73.1281074445238
    },
    {
        "id": "P10",
        "nombre": "Sede Recreacional Catay", "lat": 6.975989960681278, "lon": -73.04154073346824
    }
]

PUNTOS_REFERENCIA = []

for punto in lugares_referencia:
    resultado = geocodificar(
        punto["nombre"],
        punto.get("lat"),
        punto.get("lon")
    )

    if resultado is not None:
        lat = resultado[0]
        lon = resultado[1]
        ciudad = resultado[2]

        PUNTOS_REFERENCIA.append({
            "id": punto["id"],
            "nombre": punto["nombre"],
            "lat": lat,
            "lon": lon
        })

        print("OK    " + punto["id"] + " | " + punto["nombre"] + " -> " + str(round(lat, 6)) + ", " + str(round(lon, 6)) + " (" + ciudad + ")")

    else:
        print("ERROR " + punto["id"] + " | " + punto["nombre"] + ": no encontrado en osm y sin coordenadas manuales")



# VEHICULOS ELECTRICOS


VEHICULOS = {
    "tesla_modely": {
        "id": "V1",
        "nombre": "Tesla Model Y Long Range",
        "gama": "alta",
        "bateria_kwh": 79.0,
        "autonomia_km": 475.0,
        "consumo_kwh_100km": 16.6
    },
    "byd_dolphin": {
        "id": "V2",
        "nombre": "BYD Dolphin Surf",
        "gama": "baja",
        "bateria_kwh": 43.2,
        "autonomia_km": 265.0,
        "consumo_kwh_100km": 16.3
    }
}