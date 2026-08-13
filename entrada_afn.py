"""Lectura y asignación de entradas para el simulador de AFN."""

import sys

EPSILON = "ε"


def leer_expresiones(ruta):
    return [
        (numero, linea.strip())
        for numero, linea in enumerate(
            ruta.read_text(encoding="utf-8").splitlines(), 1
        )
        if linea.strip() and not linea.lstrip().startswith("#")
    ]


def leer_cadenas(ruta):
    return [
        "" if linea.strip() == EPSILON else linea.strip()
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if not linea.lstrip().startswith("#")
    ]


def asignar_cadenas(expresiones, argumentos, archivo):
    if argumentos:
        cadenas = ["" if valor == EPSILON else valor for valor in argumentos]
        if len(cadenas) == 1:
            return cadenas * len(expresiones)
        if len(cadenas) == len(expresiones):
            return cadenas
        raise ValueError("use una sola --cadena o una por cada expresión")

    if archivo.exists():
        cadenas = leer_cadenas(archivo)
        if len(cadenas) != len(expresiones):
            raise ValueError(
                f"{archivo} tiene {len(cadenas)} cadenas; se esperaban {len(expresiones)}"
            )
        return cadenas
    if not sys.stdin.isatty():
        raise ValueError("indique --cadena o cree un archivo de cadenas")
    return [input(f"Cadena w para r = {regex}: ") for _, regex in expresiones]
