"""Construcción y simulación de AFN mediante el algoritmo de Thompson."""

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import count
from pathlib import Path

from entrada_afn import asignar_cadenas, leer_expresiones
from shunting_yard import CONCAT, ErrorRegex, convertir, mostrar
from syntax_tree import construir_arbol
from visualizacion_afn import guardar_svg, mostrar_ventana

EPSILON = "ε"


@dataclass(frozen=True)
class Transicion:
    origen: int
    simbolo: str
    destino: int


@dataclass
class AFN:
    inicial: int
    aceptacion: int
    estados: set[int]
    transiciones: list[Transicion]
    posiciones: dict[int, tuple[float, float]]


@dataclass
class Fragmento:
    inicial: int
    aceptacion: int
    estados: set[int]
    transiciones: list[Transicion]
    posiciones: dict[int, tuple[float, float]]
    ancho: float
    minimo_y: float
    maximo_y: float


def _mover(posiciones, dx=0, dy=0):
    return {estado: (x + dx, y + dy) for estado, (x, y) in posiciones.items()}


def _limites(posiciones):
    valores_y = [y for _, y in posiciones.values()]
    return min(valores_y), max(valores_y)


def construir_afn(raiz):
    """Aplica Thompson al árbol y devuelve un AFN con disposición estructural."""
    estados = count()

    def construir(nodo):
        if nodo.izquierdo is None and nodo.derecho is None:
            inicio, fin = next(estados), next(estados)
            return Fragmento(
                inicio,
                fin,
                {inicio, fin},
                [Transicion(inicio, nodo.valor, fin)],
                {inicio: (0, 0), fin: (2, 0)},
                2,
                0,
                0,
            )

        if nodo.valor == CONCAT:
            izquierdo, derecho = construir(nodo.izquierdo), construir(nodo.derecho)
            dx = izquierdo.ancho + 1
            posiciones = izquierdo.posiciones | _mover(derecho.posiciones, dx)
            minimo_y, maximo_y = _limites(posiciones)
            return Fragmento(
                izquierdo.inicial,
                derecho.aceptacion,
                izquierdo.estados | derecho.estados,
                izquierdo.transiciones
                + [Transicion(izquierdo.aceptacion, EPSILON, derecho.inicial)]
                + derecho.transiciones,
                posiciones,
                dx + derecho.ancho,
                minimo_y,
                maximo_y,
            )

        if nodo.valor == "|":
            izquierdo, derecho = construir(nodo.izquierdo), construir(nodo.derecho)
            inicio, fin = next(estados), next(estados)
            ancho = max(izquierdo.ancho, derecho.ancho) + 4
            posiciones = {inicio: (0, 0), fin: (ancho, 0)}
            posiciones |= _mover(
                izquierdo.posiciones, 2, -1.25 - izquierdo.maximo_y
            )
            posiciones |= _mover(
                derecho.posiciones, 2, 1.25 - derecho.minimo_y
            )
            minimo_y, maximo_y = _limites(posiciones)
            return Fragmento(
                inicio,
                fin,
                izquierdo.estados | derecho.estados | {inicio, fin},
                [
                    Transicion(inicio, EPSILON, izquierdo.inicial),
                    Transicion(inicio, EPSILON, derecho.inicial),
                    *izquierdo.transiciones,
                    *derecho.transiciones,
                    Transicion(izquierdo.aceptacion, EPSILON, fin),
                    Transicion(derecho.aceptacion, EPSILON, fin),
                ],
                posiciones,
                ancho,
                minimo_y,
                maximo_y,
            )

        if nodo.valor == "*":
            interior = construir(nodo.izquierdo)
            inicio, fin = next(estados), next(estados)
            ancho = interior.ancho + 4
            posiciones = {inicio: (0, 0), fin: (ancho, 0)} | _mover(
                interior.posiciones, 2
            )
            minimo_y, maximo_y = _limites(posiciones)
            return Fragmento(
                inicio,
                fin,
                interior.estados | {inicio, fin},
                [
                    Transicion(inicio, EPSILON, interior.inicial),
                    Transicion(inicio, EPSILON, fin),
                    *interior.transiciones,
                    Transicion(interior.aceptacion, EPSILON, interior.inicial),
                    Transicion(interior.aceptacion, EPSILON, fin),
                ],
                posiciones,
                ancho,
                minimo_y,
                maximo_y,
            )

        raise ErrorRegex(f"nodo no compatible con Thompson: '{nodo.valor}'")

    fragmento = construir(raiz)
    orden = sorted(
        fragmento.estados,
        key=lambda estado: (
            fragmento.posiciones[estado][0],
            fragmento.posiciones[estado][1],
        ),
    )
    nombre = {estado: numero for numero, estado in enumerate(orden)}
    return AFN(
        nombre[fragmento.inicial],
        nombre[fragmento.aceptacion],
        set(nombre.values()),
        [
            Transicion(nombre[t.origen], t.simbolo, nombre[t.destino])
            for t in fragmento.transiciones
        ],
        {
            nombre[estado]: posicion
            for estado, posicion in fragmento.posiciones.items()
        },
    )


def _mapa_transiciones(afn):
    mapa = defaultdict(list)
    for transicion in afn.transiciones:
        mapa[transicion.origen].append((transicion.simbolo, transicion.destino))
    return mapa


def cerradura_epsilon(estados, mapa):
    """Calcula ε-closure para un conjunto de estados."""
    cierre, pendientes = set(estados), list(estados)
    while pendientes:
        for simbolo, destino in mapa.get(pendientes.pop(), []):
            if simbolo == EPSILON and destino not in cierre:
                cierre.add(destino)
                pendientes.append(destino)
    return cierre


def _coincide(simbolo, caracter):
    if simbolo.startswith("\\") and len(simbolo) == 2:
        return simbolo[1] == caracter
    if not (simbolo.startswith("[") and simbolo.endswith("]")):
        return simbolo == caracter

    contenido, caracteres, i = simbolo[1:-1], [], 0
    while i < len(contenido):
        if contenido[i] == "\\" and i + 1 < len(contenido):
            caracteres.append(contenido[i + 1])
            i += 2
        elif i + 2 < len(contenido) and contenido[i + 1] == "-":
            caracteres.extend(
                chr(n)
                for n in range(ord(contenido[i]), ord(contenido[i + 2]) + 1)
            )
            i += 3
        else:
            caracteres.append(contenido[i])
            i += 1
    return caracter in caracteres


def formatear_estados(estados):
    return "{" + ", ".join(f"q{estado}" for estado in sorted(estados)) + "}"


def simular(afn, cadena):
    """Simula el AFN mediante ε-cerraduras y devuelve resultado y traza."""
    mapa = _mapa_transiciones(afn)
    actuales = cerradura_epsilon({afn.inicial}, mapa)
    traza = [f"Inicio: ε-closure = {formatear_estados(actuales)}"]
    for posicion, caracter in enumerate(cadena, 1):
        destinos = {
            destino
            for estado in actuales
            for simbolo, destino in mapa.get(estado, [])
            if simbolo != EPSILON and _coincide(simbolo, caracter)
        }
        actuales = cerradura_epsilon(destinos, mapa)
        traza.append(
            f"{posicion:02}. leer '{caracter}' → {formatear_estados(actuales)}"
        )
    aceptada = afn.aceptacion in actuales
    traza.append(
        f"Estado q{afn.aceptacion} "
        + ("alcanzado: SÍ" if aceptada else "no alcanzado: NO")
    )
    return aceptada, traza


def procesar(expresiones, cadenas, directorio_grafos):
    bloques, resultados = [], []
    hubo_error = False
    for (numero, regex), cadena in zip(expresiones, cadenas):
        try:
            normalizada, postfix, cambios, _ = convertir(regex)
            raiz, _ = construir_arbol(postfix)
            afn = construir_afn(raiz)
            aceptada, traza = simular(afn, cadena)
            ruta_svg = directorio_grafos / f"afn_{numero:02}.svg"
            guardar_svg(afn, ruta_svg, f"AFN de Thompson: {regex}", aceptada, cadena)
            bloque = [
                "=" * 76,
                f"EXPRESIÓN {numero}: {regex}",
                f"CADENA w: {cadena or EPSILON}",
                f"INFIX NORMALIZADA: {mostrar(normalizada)}",
            ]
            if cambios:
                bloque += ["EXPANSIONES:", *[f"  {c}" for c in cambios]]
            bloque += [
                f"POSTFIX: {mostrar(postfix)}",
                f"ESTADO INICIAL: q{afn.inicial}",
                f"ESTADO DE ACEPTACIÓN: q{afn.aceptacion}",
                f"ESTADOS: {formatear_estados(afn.estados)}",
                "TRANSICIONES:",
                *[
                    f"  δ(q{t.origen}, {t.simbolo}) → q{t.destino}"
                    for t in afn.transiciones
                ],
                "SIMULACIÓN:",
                *[f"  {paso}" for paso in traza],
                f"RESULTADO: {'SÍ' if aceptada else 'NO'}",
                f"GRAFO: {ruta_svg}",
            ]
            resultados.append((numero, regex, cadena, afn, aceptada))
        except ErrorRegex as error:
            hubo_error = True
            bloque = ["=" * 76, f"EXPRESIÓN {numero}: {regex}", f"ERROR: {error}"]
        bloques.append("\n".join(bloque))
    return "\n\n".join(bloques), resultados, hubo_error


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Construye y simula AFN con el algoritmo de Thompson."
    )
    parser.add_argument(
        "archivo", nargs="?", type=Path, default=base / "expresiones.txt"
    )
    parser.add_argument("--cadena", action="append")
    parser.add_argument(
        "--archivo-cadenas", type=Path, default=base / "cadenas.txt"
    )
    parser.add_argument(
        "--directorio-grafos", type=Path, default=base / "grafos"
    )
    parser.add_argument("--sin-gui", action="store_true")
    args = parser.parse_args()

    try:
        expresiones = leer_expresiones(args.archivo)
        if not expresiones:
            raise ValueError("el archivo no contiene expresiones")
        cadenas = asignar_cadenas(expresiones, args.cadena, args.archivo_cadenas)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    reporte, resultados, hubo_error = procesar(
        expresiones, cadenas, args.directorio_grafos
    )
    print(reporte)
    if resultados and not args.sin_gui:
        try:
            mostrar_ventana(resultados)
        except Exception as error:
            print(f"\nNo se pudo abrir la ventana: {error}", file=sys.stderr)
            print("Las imágenes SVG sí fueron generadas.", file=sys.stderr)
            return 1
    return int(hubo_error)


if __name__ == "__main__":
    raise SystemExit(main())
