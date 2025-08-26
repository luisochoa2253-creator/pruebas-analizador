import sys
from dataclasses import dataclass
from typing import Optional, Iterator

# =============================
# Tabla de tipos de token (códigos exactos del PDF)
# =============================
TOKEN = {
    "identificador": 0,
    "entero": 1,
    "real": 2,
    "cadena": 3,
    "tipo": 4,                 # int, float, void
    "opSuma": 5,               # +, -
    "opMul": 6,                # *, /
    "opRelac": 7,              # <, <=, >, >=
    "opOr": 8,                 # ||
    "opAnd": 9,                # &&
    "opNot": 10,               # !
    "opIgualdad": 11,          # ==, !=
    ";": 12,
    ",": 13,
    "(": 14,
    ")": 15,
    "{": 16,
    "}": 17,
    "=": 18,                   # asignación
    "if": 19,
    "while": 20,
    "return": 21,
    "else": 22,
    "$": 23,                   # EOF
}

# Palabras reservadas
RESERVED_SINGLE = {
    "if": TOKEN["if"],
    "while": TOKEN["while"],
    "return": TOKEN["return"],
    "else": TOKEN["else"],
}

# Palabras de tipo -> token "tipo" (código 4)
RESERVED_TYPES = {"int", "float", "void"}

@dataclass
class Token:
    tipo: int
    lexema: str
    linea: int
    columna: int

    def __repr__(self) -> str:
        return f"Token(tipo={self.tipo}, lexema={self.lexema!r}, linea={self.linea}, columna={self.columna})"

class LexerError(Exception):
    def __init__(self, message: str, linea: int, columna: int):
        super().__init__(f"[L{linea}:C{columna}] {message}")
        self.linea = linea
        self.columna = columna

class Lexer:
    def __init__(self, fuente: str):
        self.fuente = fuente
        self.i = 0
        self.linea = 1
        self.columna = 1
        self.n = len(fuente)

    # Utilidades -------------------------------------
    def _peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.fuente[j] if j < self.n else "\0"

    def _advance(self) -> str:
        ch = self._peek()
        if ch == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        self.i += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _skip_whitespace(self):
        while True:
            ch = self._peek()
            if ch in {" ", "\t", "\r", "\n"}:
                self._advance()
                continue
            # comentarios estilo // y /* */ (no obligatorios, pero útiles)
            if ch == "/" and self._peek(1) == "/":
                while self._peek() not in {"\n", "\0"}:
                    self._advance()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._advance(); self._advance()
                while True:
                    if self._peek() == "\0":
                        raise LexerError("Comentario bloque sin cerrar", self.linea, self.columna)
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance(); self._advance()
                        break
                    self._advance()
                continue
            break

    # Escaneos ---------------------------------------
    def _scan_ident_or_reserved(self) -> Token:
        start_i, start_line, start_col = self.i, self.linea, self.columna
        # letra (letra|digito)* — permitimos letras ASCII y _ como extensión común
        def is_letter(c: str) -> bool:
            return c.isalpha() or c == "_"
        def is_digit(c: str) -> bool:
            return c.isdigit()

        if not is_letter(self._peek()):
            raise AssertionError("_scan_ident_or_reserved mal invocado")
        self._advance()
        while is_letter(self._peek()) or is_digit(self._peek()):
            self._advance()
        lex = self.fuente[start_i:self.i]
        if lex in RESERVED_SINGLE:
            return Token(RESERVED_SINGLE[lex], lex, start_line, start_col)
        if lex in RESERVED_TYPES:
            return Token(TOKEN["tipo"], lex, start_line, start_col)
        return Token(TOKEN["identificador"], lex, start_line, start_col)

    def _scan_number(self) -> Token:
        # entero = digito+ ; real = entero . entero
        start_i, start_line, start_col = self.i, self.linea, self.columna
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()  # consume '.'
            if not self._peek().isdigit():
                raise LexerError("Se esperaba al menos un dígito después del punto", self.linea, self.columna)
            while self._peek().isdigit():
                self._advance()
            lex = self.fuente[start_i:self.i]
            return Token(TOKEN["real"], lex, start_line, start_col)
        lex = self.fuente[start_i:self.i]
        return Token(TOKEN["entero"], lex, start_line, start_col)

    def _scan_string(self) -> Token:
        # cadena: secuencia entre comillas dobles, sin escapes complejos
        start_line, start_col = self.linea, self.columna
        quote = self._advance()  # consume '"'
        start_i = self.i
        while True:
            ch = self._peek()
            if ch == "\0":
                raise LexerError("Cadena sin cerrar", start_line, start_col)
            if ch == "\n":
                raise LexerError("Salto de línea dentro de cadena", self.linea, self.columna)
            if ch == '"':
                lex = self.fuente[start_i:self.i]
                self._advance()  # consume '"'
                return Token(TOKEN["cadena"], lex, start_line, start_col)
            # soporte muy sencillo de escape \" y \\
            if ch == "\\":
                # consumir barra y el siguiente carácter si existe
                self._advance()
                if self._peek() != "\0":
                    self._advance()
                continue
            self._advance()

    # API pública ------------------------------------
    def tokens(self) -> Iterator[Token]:
        while True:
            self._skip_whitespace()
            ch = self._peek()
            if ch == "\0":
                yield Token(TOKEN["$"], "$", self.linea, self.columna)
                break

            # Identificadores / reservadas / tipos
            if ch.isalpha() or ch == "_":
                yield self._scan_ident_or_reserved()
                continue

            # Números
            if ch.isdigit():
                yield self._scan_number()
                continue

            # Cadenas
            if ch == '"':
                yield self._scan_string()
                continue

            # Operadores y separadores (manejar primero los de 2 caracteres)
            start_line, start_col = self.linea, self.columna

            # opIgualdad: ==, !=  (preferente sobre '!')
            if ch == "=" and self._peek(1) == "=":
                self._advance(); self._advance()
                yield Token(TOKEN["opIgualdad"], "==", start_line, start_col)
                continue
            if ch == "!" and self._peek(1) == "=":
                self._advance(); self._advance()
                yield Token(TOKEN["opIgualdad"], "!=", start_line, start_col)
                continue

            # opRelac: <=, >=
            if ch == "<" and self._peek(1) == "=":
                self._advance(); self._advance()
                yield Token(TOKEN["opRelac"], "<=", start_line, start_col)
                continue
            if ch == ">" and self._peek(1) == "=":
                self._advance(); self._advance()
                yield Token(TOKEN["opRelac"], ">=", start_line, start_col)
                continue

            # opAnd &&, opOr ||
            if ch == "&" and self._peek(1) == "&":
                self._advance(); self._advance()
                yield Token(TOKEN["opAnd"], "&&", start_line, start_col)
                continue
            if ch == "|" and self._peek(1) == "|":
                self._advance(); self._advance()
                yield Token(TOKEN["opOr"], "||", start_line, start_col)
                continue

            # Un solo carácter
            ch = self._advance()
            if ch in "+-":
                yield Token(TOKEN["opSuma"], ch, start_line, start_col)
            elif ch in "*/":
                yield Token(TOKEN["opMul"], ch, start_line, start_col)
            elif ch in "<>":
                # opRelac: <, >
                yield Token(TOKEN["opRelac"], ch, start_line, start_col)
            elif ch == "!":
                yield Token(TOKEN["opNot"], ch, start_line, start_col)
            elif ch == "=":
                yield Token(TOKEN["="], ch, start_line, start_col)
            elif ch == ";":
                yield Token(TOKEN[";"], ch, start_line, start_col)
            elif ch == ",":
                yield Token(TOKEN[","] , ch, start_line, start_col)
            elif ch == "(":
                yield Token(TOKEN["("], ch, start_line, start_col)
            elif ch == ")":
                yield Token(TOKEN[")"], ch, start_line, start_col)
            elif ch == "{":
                yield Token(TOKEN["{"], ch, start_line, start_col)
            elif ch == "}":
                yield Token(TOKEN["}"], ch, start_line, start_col)
            else:
                raise LexerError(f"Símbolo inesperado: {ch}", start_line, start_col)

# ----------------------------------------------------
# Ejecución directa para probar desde la terminal
# ----------------------------------------------------

def _demo(texto: str):
    lex = Lexer(texto)
    for tok in lex.tokens():
        print(tok)

if __name__ == "__main__":
    if sys.stdin.isatty():
        print("Introduce código fuente; fin con Ctrl+D (Unix) o Ctrl+Z+Enter (Windows).\n")
    fuente = sys.stdin.read()
    try:
        _demo(fuente)
    except LexerError as e:
        print("Error léxico:", e, file=sys.stderr)
        sys.exit(1)
