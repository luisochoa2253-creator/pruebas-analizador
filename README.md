# 📌 Pruebas Analizador

Este proyecto implementa un **analizador léxico** en Python, diseñado para reconocer y clasificar los **tokens** de un lenguaje de programación sencillo.  

El analizador identifica **palabras reservadas, identificadores, números, cadenas, operadores y símbolos especiales**, generando una secuencia de tokens con su tipo, lexema, línea y columna.

---

## Características principales
- Reconocimiento de:
  - **Identificadores** y **palabras reservadas** (`if`, `while`, `return`, `else`).
  - **Tipos de datos** (`int`, `float`, `void`).
  - **Números enteros y reales**.
  - **Cadenas** entre comillas dobles (`"texto"`).
  - **Operadores**:
    - Aritméticos (`+`, `-`, `*`, `/`).
    - Relacionales (`<`, `<=`, `>`, `>=`).
    - Igualdad (`==`, `!=`).
    - Lógicos (`&&`, `||`, `!`).
    - Asignación (`=`).
  - **Símbolos especiales**: `; , ( ) { }`.
- Manejo de **comentarios** de tipo:
  - `// comentario en línea`
  - `/* comentario en bloque */`
- Reporte de **errores léxicos** con número de línea y columna.
- Compatible con **entrada por archivo** o directamente desde la terminal.

---

## 📂 Estructura de Tokens
Cada token generado tiene la forma:

```python
Token(tipo=<int>, lexema=<str>, linea=<int>, columna=<int>)
