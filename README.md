# Laboratorio 4 - AFN de Thompson

El programa convierte cada expresión regular de `expresiones.txt` a postfix,
construye su árbol sintáctico, aplica el algoritmo de Thompson y simula una
cadena `w`. También abre una ventana desplazable con cada AFN y guarda una
imagen SVG en `grafos/`.


El código está separado por responsabilidad: `thompson.py` contiene la
construcción y simulación, `visualizacion_afn.py` genera SVG/Tkinter y
`entrada_afn.py` procesa los archivos de entrada.

## Ejecución

```powershell
python thompson.py
```

Para ejecutar sin interfaz gráfica:

```powershell
python thompson.py --sin-gui
```

`cadenas.txt` contiene una cadena por cada expresión no comentada. También se
puede proporcionar una misma cadena para todas las expresiones:

```powershell
python thompson.py --cadena abba
```

O una cadena por expresión repitiendo `--cadena`. Use `ε` para representar la
cadena vacía. Las expresiones admiten unión `|`, concatenación implícita,
cerradura `*`, cerradura positiva `+`, opcional `?`, paréntesis, escapes y clases
de caracteres.
