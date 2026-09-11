from enum import Enum, auto

class EstadoJSON(Enum):
    BUSCANDO_LLAVE_INICIO = auto() # Espera '{'
    ESPERANDO_CLAVE        = auto() # Espera comilla de inicio de clave '"'
    LEYENDO_CLAVE          = auto() # Acumula caracteres de la clave
    ESPERANDO_DOS_PUNTOS   = auto() # Espera ':'
    ESPERANDO_VALOR        = auto() # Espera inicio de valor (comilla o número)
    LEYENDO_VALOR          = auto() # Acumula caracteres del valor
    ESPERANDO_COMA_O_CIERRE= auto() # Espera ',' o '}'

class ParserJSONIncrementalFSM:
    def __init__(self, claves_objetivo: list[str]):
        self.estado = EstadoJSON.BUSCANDO_LLAVE_INICIO
        self.claves_objetivo = claves_objetivo
        
        # Buffer acumulador para lo que estamos leyendo
        self.buffer = ""
        self.clave_actual = ""
        self.datos_extraidos = {}

    def procesar_chunk(self, chunk: str):
        """Procesa un fragmento de texto que llega poco a poco."""
        for char in chunk:
            self._transicionar(char)

    def _transicionar(self, char: str):
        # Ignorar espacios en blanco fuera de cadenas de texto
        if char.isspace() and self.estado not in (EstadoJSON.LEYENDO_CLAVE, EstadoJSON.LEYENDO_VALOR):
            return

        match self.estado:
            case EstadoJSON.BUSCANDO_LLAVE_INICIO:
                if char == '{':
                    self.estado = EstadoJSON.ESPERANDO_CLAVE

            case EstadoJSON.ESPERANDO_CLAVE:
                if char == '"':
                    self.buffer = ""
                    self.estado = EstadoJSON.LEYENDO_CLAVE

            case EstadoJSON.LEYENDO_CLAVE:
                if char == '"':
                    self.clave_actual = self.buffer
                    self.buffer = ""
                    self.estado = EstadoJSON.ESPERANDO_DOS_PUNTOS
                else:
                    self.buffer += char

            case EstadoJSON.ESPERANDO_DOS_PUNTOS:
                if char == ':':
                    self.estado = EstadoJSON.ESPERANDO_VALOR

            case EstadoJSON.ESPERANDO_VALOR:
                if char == '"': # Asumiendo valores tipo string para este ejemplo
                    self.buffer = ""
                    self.estado = EstadoJSON.LEYENDO_VALOR

            case EstadoJSON.LEYENDO_VALOR:
                if char == '"':
                    valor = self.buffer
                    # Si la clave leída nos interesa, guardamos el parámetro
                    if self.clave_actual in self.claves_objetivo:
                        self.datos_extraidos[self.clave_actual] = valor
                        print(f"-> ¡Parámetro detectado! '{self.clave_actual}': '{valor}'")
                    
                    self.estado = EstadoJSON.ESPERANDO_COMA_O_CIERRE
                else:
                    self.buffer += char

            case EstadoJSON.ESPERANDO_COMA_O_CIERRE:
                if char == ',':
                    self.estado = EstadoJSON.ESPERANDO_CLAVE
                elif char == '}':
                    self.estado = EstadoJSON.BUSCANDO_LLAVE_INICIO
                    print("-> Objeto JSON completado.")

# --- Ejemplo de uso con flujo recibido en fragmentos ---

parser = ParserJSONIncrementalFSM(claves_objetivo=["status", "sensor_id"])

# Simulamos que los datos llegan en trozos arbitrarios
flujo_datos = [
    '{"stat',
    'us": "ok", ',
    '"temp": 23, "sen',
    'sor_id": "A-123"','}'
]

for trozo in flujo_datos:
    print(f"Recibido chunk: '{trozo}'")
    parser.procesar_chunk(trozo)

print("\nResultado final capturado:", parser.datos_extraidos)