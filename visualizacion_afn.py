"""Exportación SVG e interfaz gráfica para un AFN de Thompson."""

import html
import math
from collections import defaultdict

EPSILON = "ε"


def _transiciones_agrupadas(afn):
    grupos = defaultdict(list)
    for transicion in afn.transiciones:
        clave = (transicion.origen, transicion.destino)
        if transicion.simbolo not in grupos[clave]:
            grupos[clave].append(transicion.simbolo)
    return sorted(grupos.items())


def _geometria(afn):
    minimo_y = min(y for _, y in afn.posiciones.values())
    maximo_y = max(y for _, y in afn.posiciones.values())
    maximo_x = max(x for x, _ in afn.posiciones.values())
    escala_x, escala_y = 90, 95
    margen_x, margen_superior = 100, 145
    posiciones = {
        estado: (
            margen_x + x * escala_x,
            margen_superior + (y - minimo_y) * escala_y,
        )
        for estado, (x, y) in afn.posiciones.items()
    }
    ancho = max(900, int(2 * margen_x + maximo_x * escala_x))
    alto = max(500, int(margen_superior + (maximo_y - minimo_y) * escala_y + 145))
    return posiciones, ancho, alto


def _ruta_transicion(origen, destino):
    x1, y1 = origen
    x2, y2 = destino
    dx, dy = x2 - x1, y2 - y1
    distancia = math.hypot(dx, dy)
    if distancia < 1:
        ruta = (
            f"M {x1-13} {y1-23} C {x1-55} {y1-85}, "
            f"{x1+55} {y1-85}, {x1+13} {y1-23}"
        )
        puntos = (
            x1 - 13, y1 - 23, x1 - 55, y1 - 85,
            x1 + 55, y1 - 85, x1 + 13, y1 - 23,
        )
        return ruta, puntos, True, x1, y1 - 86

    sx, sy = x1 + 26 * dx / distancia, y1 + 26 * dy / distancia
    ex, ey = x2 - 31 * dx / distancia, y2 - 31 * dy / distancia
    if abs(dy) < 5 and 0 < dx <= 210:
        return (
            f"M {sx} {sy} L {ex} {ey}",
            (sx, sy, ex, ey),
            False,
            (sx + ex) / 2,
            sy - 11,
        )

    if abs(dy) < 5:
        altura = min(135, 45 + abs(dx) * 0.10)
        control_y = y1 - altura if dx > 0 else y1 + altura
        ruta = f"M {sx} {sy} Q {(x1+x2)/2} {control_y} {ex} {ey}"
        etiqueta_y = (y1 + control_y) / 2 + (-9 if dx > 0 else 18)
        return ruta, (sx, sy, (x1 + x2) / 2, control_y, ex, ey), True, (x1 + x2) / 2, etiqueta_y

    direccion = 1 if dx >= 0 else -1
    control = min(75, max(35, abs(dx) / 3))
    c1x, c1y = sx + direccion * control, sy
    c2x, c2y = ex - direccion * control, ey
    ruta = f"M {sx} {sy} C {c1x} {c1y}, {c2x} {c2y}, {ex} {ey}"
    return ruta, (sx, sy, c1x, c1y, c2x, c2y, ex, ey), True, (x1 + x2) / 2, (y1 + y2) / 2 - 10


def guardar_svg(afn, ruta, titulo, aceptada, cadena):
    """Exporta el AFN a una imagen SVG sin dependencias externas."""
    posiciones, ancho, alto = _geometria(afn)
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">',
        '<defs><marker id="flecha" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#475569"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="30" y="38" font-family="Segoe UI, sans-serif" font-size="19" font-weight="700" fill="#0f172a">{html.escape(titulo)}</text>',
        f'<text x="30" y="67" font-family="Segoe UI, sans-serif" font-size="15" fill="#334155">Cadena: {html.escape(cadena or EPSILON)} — Resultado: {"SÍ" if aceptada else "NO"}</text>',
    ]
    for (origen, destino), simbolos in _transiciones_agrupadas(afn):
        ruta_svg, _, _, lx, ly = _ruta_transicion(
            posiciones[origen], posiciones[destino]
        )
        etiqueta = html.escape(", ".join(simbolos))
        partes.extend([
            f'<path d="{ruta_svg}" fill="none" stroke="#64748b" stroke-width="1.8" marker-end="url(#flecha)"/>',
            f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="13" font-weight="600" fill="#1e293b" paint-order="stroke" stroke="#f8fafc" stroke-width="5">{etiqueta}</text>',
        ])

    xi, yi = posiciones[afn.inicial]
    partes.extend([
        f'<line x1="{xi-65}" y1="{yi}" x2="{xi-29}" y2="{yi}" stroke="#0f172a" stroke-width="2" marker-end="url(#flecha)"/>',
        f'<text x="{xi-68}" y="{yi-10}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="12" fill="#334155">inicio</text>',
    ])
    for estado, (x, y) in posiciones.items():
        relleno = "#dcfce7" if estado == afn.aceptacion else "#dbeafe"
        partes.append(
            f'<circle cx="{x}" cy="{y}" r="25" fill="{relleno}" stroke="#1e3a5f" stroke-width="2"/>'
        )
        if estado == afn.aceptacion:
            partes.append(
                f'<circle cx="{x}" cy="{y}" r="20" fill="none" stroke="#1e3a5f" stroke-width="1.5"/>'
            )
        partes.append(
            f'<text x="{x}" y="{y+5}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#0f172a">q{estado}</text>'
        )
    partes.append("</svg>")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(partes), encoding="utf-8")


def _dibujar_afn(canvas, afn):
    import tkinter as tk

    posiciones, ancho, alto = _geometria(afn)
    canvas.configure(scrollregion=(0, 0, ancho, alto))
    for (origen, destino), simbolos in _transiciones_agrupadas(afn):
        _, puntos, suave, lx, ly = _ruta_transicion(
            posiciones[origen], posiciones[destino]
        )
        canvas.create_line(
            *puntos, smooth=suave, width=2, fill="#64748b", arrow=tk.LAST
        )
        canvas.create_text(
            lx, ly, text=", ".join(simbolos), font=("Segoe UI", 10, "bold")
        )
    xi, yi = posiciones[afn.inicial]
    canvas.create_line(xi - 65, yi, xi - 29, yi, width=2, arrow=tk.LAST)
    canvas.create_text(xi - 68, yi - 10, text="inicio", anchor="e")
    for estado, (x, y) in posiciones.items():
        relleno = "#dcfce7" if estado == afn.aceptacion else "#dbeafe"
        canvas.create_oval(
            x - 25, y - 25, x + 25, y + 25,
            fill=relleno, outline="#1e3a5f", width=2,
        )
        if estado == afn.aceptacion:
            canvas.create_oval(
                x - 20, y - 20, x + 20, y + 20,
                outline="#1e3a5f", width=2,
            )
        canvas.create_text(x, y, text=f"q{estado}", font=("Segoe UI", 10, "bold"))


def mostrar_ventana(resultados):
    """Abre una pestaña desplazable por cada AFN."""
    import tkinter as tk
    from tkinter import ttk

    ventana = tk.Tk()
    ventana.title("Laboratorio 4 - AFN de Thompson")
    ventana.geometry("1180x720")
    cuaderno = ttk.Notebook(ventana)
    cuaderno.pack(fill="both", expand=True)
    for numero, regex, cadena, afn, aceptada in resultados:
        marco = ttk.Frame(cuaderno)
        cuaderno.add(marco, text=f"Línea {numero}")
        ttk.Label(
            marco, text=f"r = {regex}", font=("Segoe UI", 12, "bold")
        ).pack(pady=(8, 2))
        ttk.Label(
            marco,
            text=f"w = {cadena or EPSILON} → {'SÍ: w ∈ L(r)' if aceptada else 'NO: w ∉ L(r)'}",
            foreground="#166534" if aceptada else "#b91c1c",
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(0, 6))
        contenedor = ttk.Frame(marco)
        contenedor.pack(fill="both", expand=True)
        canvas = tk.Canvas(contenedor, background="#f8fafc")
        barra_x = ttk.Scrollbar(contenedor, orient="horizontal", command=canvas.xview)
        barra_y = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=barra_x.set, yscrollcommand=barra_y.set)
        barra_x.pack(side="bottom", fill="x")
        barra_y.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        _dibujar_afn(canvas, afn)
    ventana.mainloop()
