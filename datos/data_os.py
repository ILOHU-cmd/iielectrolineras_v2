# archivo de apoyo para explicar como se podrian consultar coordenadas con osmnx
# no se ejecuta automaticamente para evitar descargas cuando solo se importa el proyecto


def mostrar_mensaje_data_os():
    # esta funcion solo informa que las coordenadas ya estan guardadas en data.py
    print("las coordenadas base del proyecto estan en datos/data.py")
    print("si se desea consultar openstreetmap, se puede usar osmnx desde el constructor del grafo.")
