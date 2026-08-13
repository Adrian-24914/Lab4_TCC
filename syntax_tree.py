"""Construcción del árbol sintáctico a partir de una regex postfix."""

from dataclasses import dataclass

from shunting_yard import BINARIOS, ErrorRegex, es_operando


@dataclass
class Nodo:
    """Nodo del árbol sintáctico de una expresión regular."""

    valor: str
    izquierdo: "Nodo | None" = None
    derecho: "Nodo | None" = None


def construir_arbol(postfix):
    """Construye el árbol sintáctico consumiendo tokens postfix."""
    pila = []
    pasos = []
    for numero, token in enumerate(postfix, 1):
        if es_operando(token):
            pila.append(Nodo(token))
            accion = f"crear hoja '{token}'"
        elif token == "*":
            if not pila:
                raise ErrorRegex("postfix inválido: '*' no tiene operando")
            pila.append(Nodo(token, izquierdo=pila.pop()))
            accion = "crear nodo unario '*'"
        elif token in BINARIOS:
            if len(pila) < 2:
                raise ErrorRegex(f"postfix inválido: '{token}' no tiene dos operandos")
            derecho = pila.pop()
            izquierdo = pila.pop()
            pila.append(Nodo(token, izquierdo, derecho))
            accion = f"crear nodo binario '{token}'"
        else:
            raise ErrorRegex(f"operador postfix desconocido: '{token}'")
        pasos.append(f"{numero:02}. {token} → {accion}; nodos en pila={len(pila)}")

    if len(pila) != 1:
        raise ErrorRegex("postfix inválido: no produce un único árbol")
    return pila[0], pasos


def arbol_como_texto(raiz):
    """Representación textual útil cuando no hay interfaz gráfica."""
    lineas = []

    def recorrer(nodo, prefijo="", ultimo=True):
        lineas.append(prefijo + ("└── " if ultimo else "├── ") + nodo.valor)
        hijos = [hijo for hijo in (nodo.izquierdo, nodo.derecho) if hijo]
        for i, hijo in enumerate(hijos):
            recorrer(
                hijo,
                prefijo + ("    " if ultimo else "│   "),
                i == len(hijos) - 1,
            )

    recorrer(raiz)
    return "\n".join(lineas)
