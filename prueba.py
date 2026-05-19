# prueba_nodos.py
# Verifica que electrolineras y puntos de referencia esten en el grafo
# Sin modificar nada del proyecto

import sys
import os

# Agregar la carpeta raiz al path para poder importar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recursos.grafos.constructor import construir_grafo, obtener_nodos_electrolineras, obtener_nodos_referencia
from datos.data import ELECTROLINERAS, PUNTOS_REFERENCIA


def verificar_todo():
    """
    Verifica electrolineras y puntos de referencia en el grafo.
    Muestra cuales estan y cuales faltan.
    """
    
    print("=" * 60)
    print("PRUEBA: Verificacion de nodos en el grafo")
    print("=" * 60)
    print()
    
    # Cargar grafo (usara cache si existe)
    print("Cargando grafo...")
    grafo = construir_grafo()
    
    if grafo is None:
        print("ERROR: No se pudo cargar el grafo.")
        return
    
    print()
    print("Grafo cargado. Nodos totales:", len(list(grafo.nodes)))
    print()
    
    # =========================================================
    # VERIFICAR ELECTROLINERAS
    # =========================================================
    
    nodos_electro = obtener_nodos_electrolineras(grafo)
    
    print("-" * 60)
    print("ELECTROLINERAS:")
    print("-" * 60)
    
    i = 0
    while i < len(ELECTROLINERAS):
        elec = ELECTROLINERAS[i]
        id_elec = elec["id"]
        
        if id_elec in nodos_electro:
            nodo = nodos_electro[id_elec]
            print("  ✓", id_elec, "-", elec["nombre"])
            print("    Nodo OSM:", nodo)
        else:
            print("  ✗", id_elec, "-", elec["nombre"], "NO ESTA EN EL GRAFO")
            print("    Coordenadas:", elec["lat"], elec["lon"])
        
        i = i + 1
    
    print()
    print("Total electrolineras en grafo:", len(nodos_electro), "de", len(ELECTROLINERAS))
    print()
    
    # =========================================================
    # VERIFICAR PUNTOS DE REFERENCIA
    # =========================================================
    
    nodos_ref = obtener_nodos_referencia(grafo)
    
    print("-" * 60)
    print("PUNTOS DE REFERENCIA:")
    print("-" * 60)
    
    i = 0
    while i < len(PUNTOS_REFERENCIA):
        ref = PUNTOS_REFERENCIA[i]
        id_ref = ref["id"]
        
        if id_ref in nodos_ref:
            nodo = nodos_ref[id_ref]
            print("  ✓", id_ref, "-", ref["nombre"])
            print("    Nodo OSM:", nodo)
        else:
            print("  ✗", id_ref, "-", ref["nombre"], "NO ESTA EN EL GRAFO")
            print("    Coordenadas:", ref["lat"], ref["lon"])
        
        i = i + 1
    
    print()
    print("Total puntos de referencia en grafo:", len(nodos_ref), "de", len(PUNTOS_REFERENCIA))
    print()
    print("=" * 60)
    print("FIN DE PRUEBA")
    print("=" * 60)


# Ejecutar
if __name__ == "__main__":
    verificar_todo()
    
    # Esperar para ver resultado
    print()
    input("Presione Enter para salir...")
    