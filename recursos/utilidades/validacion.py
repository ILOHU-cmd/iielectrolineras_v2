# funciones para validar datos digitados por el usuario
# se usan ciclos while para repetir hasta recibir una entrada correcta

import os


def limpiar_pantalla():
    # limpia la pantalla dependiendo del sistema operativo
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def leer_entero(mensaje, minimo=None, maximo=None):
    # lee numeros enteros y valida vacios, letras, negativos y rangos
    while True:
        entrada = input(mensaje).strip()

        if entrada == "":
            print("entrada vacia. digite un numero entero.")
        else:
            if entrada[0] == "-":
                parte_numerica = entrada[1:]
            else:
                parte_numerica = entrada

            if parte_numerica == "":
                print("debe digitar un numero.")
            elif not parte_numerica.isdigit():
                print("solo se permiten numeros enteros.")
            else:
                valor = int(entrada)

                if minimo is not None and valor < minimo:
                    print("el numero debe ser mayor o igual a", minimo)
                elif maximo is not None and valor > maximo:
                    print("el numero debe ser menor o igual a", maximo)
                else:
                    return valor

        print()


def leer_decimal(mensaje, minimo=None, maximo=None):
    # lee numeros decimales y permite usar punto o coma
    while True:
        entrada = input(mensaje).strip()

        if entrada == "":
            print("entrada vacia. digite un numero.")
        else:
            entrada = entrada.replace(",", ".")

            try:
                valor = float(entrada)

                if minimo is not None and valor < minimo:
                    print("el numero debe ser mayor o igual a", minimo)
                elif maximo is not None and valor > maximo:
                    print("el numero debe ser menor o igual a", maximo)
                else:
                    return valor
            except ValueError:
                print("formato invalido. ejemplo valido: 12.5")

        print()


def confirmar(mensaje):
    # lee una respuesta de si o no
    while True:
        respuesta = input(mensaje + " [s/n]: ").strip().lower()

        if respuesta == "s":
            return True
        elif respuesta == "n":
            return False
        else:
            print("respuesta invalida. escriba s o n.")
            print()
