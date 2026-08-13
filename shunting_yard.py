"""Convierte expresiones regulares infix a postfix con Shunting Yard.

Este módulo conserva la interfaz usada en el Laboratorio 3 para que el árbol
sintáctico y la construcción de Thompson partan exactamente de la misma
representación de la expresión regular.
"""

CONCAT = "·"
BINARIOS = {"|", CONCAT}
PRECEDENCIA = {"|": 1, CONCAT: 2}
CONTROL = {"(", ")", "|", "*", "+", "?", CONCAT}


class ErrorRegex(ValueError):
    """Error de sintaxis en una expresión regular."""


def mostrar(tokens):
    return " ".join(tokens) if tokens else "∅"


def es_operando(token):
    return token not in CONTROL


def tokenizar(regex):
    """Agrupa escapes y clases de caracteres en tokens individuales."""
    tokens = []
    i = 0
    while i < len(regex):
        caracter = regex[i]
        if caracter.isspace():
            i += 1
        elif caracter == "\\":
            if i + 1 == len(regex):
                raise ErrorRegex("barra invertida sin carácter escapado")
            tokens.append(regex[i : i + 2])
            i += 2
        elif caracter == "[":
            inicio = i
            i += 1
            escapado = False
            while i < len(regex):
                if escapado:
                    escapado = False
                elif regex[i] == "\\":
                    escapado = True
                elif regex[i] == "]":
                    break
                i += 1
            if i == len(regex):
                raise ErrorRegex("clase de caracteres sin cierre ']'")
            tokens.append(regex[inicio : i + 1])
            i += 1
        else:
            if caracter == CONCAT:
                raise ErrorRegex(f"'{CONCAT}' es un símbolo interno reservado")
            tokens.append(caracter)
            i += 1

    if not tokens:
        raise ErrorRegex("expresión vacía")
    return tokens


def inicio_ultimo_atomo(tokens):
    """Localiza el operando al que pertenece un cuantificador postfix."""
    i = len(tokens) - 1
    while i >= 0 and tokens[i] == "*":
        i -= 1
    if i < 0:
        raise ErrorRegex("cuantificador sin operando")

    if tokens[i] == ")":
        nivel = 1
        i -= 1
        while i >= 0:
            nivel += (tokens[i] == ")") - (tokens[i] == "(")
            if nivel == 0:
                return i
            i -= 1
        raise ErrorRegex("paréntesis de cierre sin apertura")

    if es_operando(tokens[i]):
        return i
    raise ErrorRegex("cuantificador sin operando válido")


def quitar_parentesis_externos(tokens):
    """Elimina solo los paréntesis que envuelven al átomo completo."""
    tokens = list(tokens)
    while len(tokens) >= 2 and tokens[0] == "(" and tokens[-1] == ")":
        nivel = 0
        envuelven_todo = True
        for i, token in enumerate(tokens):
            nivel += (token == "(") - (token == ")")
            if nivel == 0 and i < len(tokens) - 1:
                envuelven_todo = False
                break
        if not envuelven_todo:
            break
        tokens = tokens[1:-1]
    return tokens


def expandir(tokens):
    """Reemplaza R+ por RR* y R? por (R|ε)."""
    resultado = []
    cambios = []
    for token in tokens:
        if token not in {"+", "?"}:
            resultado.append(token)
            continue

        inicio = inicio_ultimo_atomo(resultado)
        atomo = resultado[inicio:]
        del resultado[inicio:]
        if token == "+":
            reemplazo = ["(", *atomo, ")", "(", *atomo, ")", "*"]
        else:
            base = quitar_parentesis_externos(atomo)
            # (R?)? = R?; evita generar alternativas ε redundantes.
            if len(base) >= 2 and base[-2:] == ["|", "ε"]:
                reemplazo = ["(", *base, ")"]
            else:
                reemplazo = ["(", *atomo, "|", "ε", ")"]
        resultado.extend(reemplazo)
        cambios.append(f"{''.join(atomo)}{token} → {''.join(reemplazo)}")
    return resultado, cambios


def agregar_concatenacion(tokens):
    resultado = []
    for token in tokens:
        termina = resultado and (
            es_operando(resultado[-1]) or resultado[-1] in {")", "*"}
        )
        inicia = es_operando(token) or token == "("
        if termina and inicia:
            resultado.append(CONCAT)
        resultado.append(token)
    return resultado


def shunting_yard(tokens):
    """Convierte tokens infix normalizados a postfix y conserva una traza."""
    salida, pila, pasos = [], [], []
    espera_operando = True

    for numero, token in enumerate(tokens, 1):
        if es_operando(token):
            if not espera_operando:
                raise ErrorRegex(f"falta un operador antes de '{token}'")
            salida.append(token)
            espera_operando = False
            accion = "salida"
        elif token == "(":
            if not espera_operando:
                raise ErrorRegex("falta concatenación antes de '('")
            pila.append(token)
            accion = "apilar"
        elif token == ")":
            if espera_operando:
                raise ErrorRegex("paréntesis vacío o cierre inválido")
            movidos = []
            while pila and pila[-1] != "(":
                movidos.append(pila.pop())
                salida.append(movidos[-1])
            if not pila:
                raise ErrorRegex("paréntesis ')' sin apertura")
            pila.pop()
            accion = "cerrar grupo"
            if movidos:
                accion += f", mover {mostrar(movidos)}"
            espera_operando = False
        elif token == "*":
            if espera_operando:
                raise ErrorRegex("'*' sin operando")
            salida.append(token)
            accion = "postfix"
        elif token in BINARIOS:
            if espera_operando:
                raise ErrorRegex(f"'{token}' sin operando izquierdo")
            movidos = []
            while (
                pila
                and pila[-1] in BINARIOS
                and PRECEDENCIA[pila[-1]] >= PRECEDENCIA[token]
            ):
                movidos.append(pila.pop())
                salida.append(movidos[-1])
            pila.append(token)
            accion = "apilar" if not movidos else f"mover {mostrar(movidos)}, apilar"
            espera_operando = True

        pasos.append(
            f"{numero:02}. {token} → {accion}; salida=[{mostrar(salida)}]; "
            f"pila=[{mostrar(pila)}]"
        )

    if espera_operando:
        raise ErrorRegex("la expresión termina con un operador")

    movidos = []
    while pila:
        if pila[-1] == "(":
            raise ErrorRegex("paréntesis '(' sin cierre")
        movidos.append(pila.pop())
        salida.append(movidos[-1])
    if movidos:
        pasos.append(f"FIN → mover {mostrar(movidos)}; salida=[{mostrar(salida)}]")
    return salida, pasos


def convertir(regex):
    """Devuelve infix normalizada, postfix, expansiones y traza."""
    tokens, cambios = expandir(tokenizar(regex))
    normalizada = agregar_concatenacion(tokens)
    postfix, pasos = shunting_yard(normalizada)
    return normalizada, postfix, cambios, pasos
