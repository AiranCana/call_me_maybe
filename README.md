4º. Implementa la carga y validación de los ficheros de entrada
Lee functions_definition.json y function_calling_tests.json, valida que sean JSON correcto y que cumplan el esquema esperado, con manejo de errores (fichero ausente, JSON corrupto, etc.) sin que el programa crashee.

6º. Carga y entiende el vocabulario
Lee el fichero devuelto por get_path_to_vocab_file() y construye una estructura en memoria que te permita, dado un token ID, saber qué string representa (y viceversa). Esto es la base de todo lo que viene después.

7º. Diseña el "validador de continuación"
Antes de tocar el LLM, diseña (en papel/pseudocódigo) la lógica que, dado un fragmento de JSON generado hasta el momento y el schema objetivo, determina qué caracteres serían válidos a continuación (ej: si acabas de abrir {, solo son válidos espacio o comilla; si estás dentro del valor de un campo number, solo dígitos, punto, etc.). Esto es el núcleo del proyecto.

8º. Traduce ese validador a nivel de tokens
Para cada token del vocabulario, comprueba si añadirlo mantiene la cadena generada como "JSON parcialmente válido según el schema". Esto te da, en cada paso, el conjunto de token IDs permitidos.

9º. Implementa el bucle de generación con constrained decoding
Genera token a token: pides los logits, aplicas tu máscara (pones a -inf los tokens no permitidos según el paso 8), eliges el token con mayor probabilidad entre los válidos, lo añades a la secuencia, y repites hasta cerrar el JSON.

10º. Resuelve primero la elección de función
Usa el mismo mecanismo (o uno más simple, restringido a los nombres de función válidos) para que el LLM elija cuál name usar dado el prompt y la lista de funciones disponibles.

11º. Genera los parámetros con el schema de la función elegida
Una vez sabes qué función se llama, usa el schema de esa función concreta para restringir la generación de su objeto parameters (nombres de campo exactos, tipos correctos).

12º. Ensambla el resultado por cada prompt
Por cada entrada del test, junta prompt + name + parameters en un objeto, valídalo con tu modelo pydantic, y añádelo a la lista de resultados.

13º. Escribe el fichero de salida
Serializa la lista completa a data/output/function_calling_results.json, con manejo de errores de escritura.

14º. Añade manejo de errores global
Envuelve el flujo completo (por prompt y global) en try/except para que ningún fallo puntual tumbe el programa entero; si un prompt falla, decide cómo lo registras sin crashear.

15º. Testing y validación
Escribe tests (no se entregan pero te sirven) que cubran casos límite: números grandes, strings vacíos, prompts ambiguos, funciones con varios parámetros.

16º. Lint y tipado
Pasa flake8 y mypy con las flags exigidas, corrige avisos.

18º. README.md
Documenta todo: descripción, instrucciones, recursos, uso de IA, explicación del algoritmo de constrained decoding, decisiones de diseño, análisis de rendimiento, retos encontrados, estrategia de testing y ejemplos de uso — en inglés y con la primera línea en el formato exigido.

19º (opcional). Bonus
Solo si te sobra tiempo: soporte multi-modelo, evitar encode/decode directos, optimizaciones, tests exhaustivos, visualización del proceso de generación, etc.