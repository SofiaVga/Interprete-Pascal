import math


class InterpreteUnificado:
    def __init__(self):
        self.variables = {}
        self.lineas = []
        self.indice = 0
        self.registros_float = [f"ft{i}" for i in range(32)]
        self.registros_usados = set()
        self.codigo_ensamblador = []
        self.contador_temporal = 7
        self.contador_etiquetas = 0

    def obtener_nueva_etiqueta(self):
        self.contador_etiquetas += 1
        return f"L{self.contador_etiquetas}"

    def obtener_registro_disponible(self):
        for r in self.registros_float:
            if r not in self.registros_usados:
                self.registros_usados.add(r)
                return r
        raise Exception("No hay registros disponibles")

    def liberar_registro(self, registro):
        if registro in self.registros_usados:
            self.registros_usados.remove(registro)

    def validar_punto_coma(self, linea, numero_linea):
        """Valida que las líneas que requieren ';' lo tengan"""
        linea_limpia = linea.strip().lower()

        # Líneas que requieren punto y coma
        requiere_semicolon = (
                linea_limpia.startswith("var") or
                ":=" in linea_limpia or
                linea_limpia.startswith("read(") or
                linea_limpia.startswith("print(") or
                linea_limpia.startswith("println(")
        )

        # Líneas que NO requieren punto y coma
        no_requiere_semicolon = (
                linea_limpia.startswith("for ") or
                linea_limpia.startswith("while ") or
                linea_limpia.endswith(" do") or
                linea_limpia in ["endfor", "endwhile"]
        )

        if requiere_semicolon and not no_requiere_semicolon and not linea.strip().endswith(";"):
            raise Exception(f"Error en línea {numero_linea}: Falta punto y coma (;)")

    def declarar_variable(self, nombre, tipo):
        """Declara una variable con validación de redeclaración"""
        if nombre in self.variables:
            raise Exception(f"Error: Variable '{nombre}' ya está declarada")

        registro = self.obtener_registro_disponible()
        self.variables[nombre] = {
            'tipo': tipo,
            'valor': None,
            'registro': registro
        }

    def asignar_valor(self, nombre, valor):
        if nombre not in self.variables:
            raise Exception(f"Error: Variable '{nombre}' no declarada.")
        self.variables[nombre]['valor'] = valor

    def obtener_valor(self, nombre):
        if nombre in self.variables and self.variables[nombre]['valor'] is not None:
            return self.variables[nombre]['valor']
        raise Exception(f"Error: Variable '{nombre}' no tiene valor.")

    def evaluar_funcion(self, func, valor):
        """Evalúa funciones trigonométricas"""
        if func == 'sin':
            return math.sin(valor)
        elif func == 'cos':
            return math.cos(valor)
        elif func == 'tan':
            return math.tan(valor)
        else:
            raise Exception(f"Función no reconocida: {func}")

    def evaluar_condicion(self, condicion):
        """Evalúa condiciones para estructuras de control"""
        tokens = condicion.split()

        if len(tokens) == 3:
            var1, var2, op = tokens

            if var1 in self.variables:
                val1 = self.obtener_valor(var1)
                reg1 = self.variables[var1]['registro']
            else:
                val1 = float(var1)
                reg1 = f"ft{self.contador_temporal}"
                self.codigo_ensamblador.append(f"li.s {reg1}, {val1}")

            if var2 in self.variables:
                val2 = self.obtener_valor(var2)
                reg2 = self.variables[var2]['registro']
            else:
                val2 = float(var2)
                reg2 = f"ft{self.contador_temporal + 1}"
                self.codigo_ensamblador.append(f"li.s {reg2}, {val2}")

            reg_temp = f"ft{self.contador_temporal + 2}"

            resultado = False
            if op == '<':
                self.codigo_ensamblador.append(f"flt.s {reg_temp}, {reg1}, {reg2}")
                resultado = val1 < val2
            elif op == '>':
                self.codigo_ensamblador.append(f"fgt.s {reg_temp}, {reg1}, {reg2}")
                resultado = val1 > val2
            elif op == '<=':
                self.codigo_ensamblador.append(f"fle.s {reg_temp}, {reg1}, {reg2}")
                resultado = val1 <= val2
            elif op == '>=':
                self.codigo_ensamblador.append(f"fge.s {reg_temp}, {reg1}, {reg2}")
                resultado = val1 >= val2
            elif op == '==':
                self.codigo_ensamblador.append(f"feq.s {reg_temp}, {reg1}, {reg2}")
                resultado = val1 == val2
            elif op == '!=':
                self.codigo_ensamblador.append(f"fne.s {reg_temp}, {reg1}, {reg2}")
                resultado = val1 != val2

            return resultado
        return False

    def evaluar_postfija(self, postfija, variable_destino=None):
        """Evalúa expresiones en notación postfija"""
        stack = []
        for token in postfija:
            if token in ['+', '-', '*', '/', '^']:
                b_token = stack.pop()
                a_token = stack.pop()

                if isinstance(a_token, str) and a_token in self.variables:
                    reg_a = self.variables[a_token]['registro']
                    val_a = self.obtener_valor(a_token)
                else:
                    reg_a = f"ft{self.contador_temporal}"
                    val_a = float(a_token)
                    if variable_destino:
                        self.codigo_ensamblador.append(f"li.s {reg_a}, {val_a}")

                if isinstance(b_token, str) and b_token in self.variables:
                    reg_b = self.variables[b_token]['registro']
                    val_b = self.obtener_valor(b_token)
                else:
                    reg_b = f"ft{self.contador_temporal + 1}"
                    val_b = float(b_token)
                    if variable_destino:
                        self.codigo_ensamblador.append(f"li.s {reg_b}, {val_b}")

                if token == '+':
                    resultado = val_a + val_b
                    if variable_destino:
                        reg_temp = f"ft{self.contador_temporal + 2}"
                        reg_destino = self.variables[variable_destino]['registro']
                        self.codigo_ensamblador.append(f"fadd.s {reg_temp}, {reg_a}, {reg_b}")
                        self.codigo_ensamblador.append(f"fmv.s {reg_destino}, {reg_temp}")
                elif token == '-':
                    resultado = val_a - val_b
                    if variable_destino:
                        reg_temp = f"ft{self.contador_temporal + 2}"
                        reg_destino = self.variables[variable_destino]['registro']
                        self.codigo_ensamblador.append(f"fsub.s {reg_temp}, {reg_a}, {reg_b}")
                        self.codigo_ensamblador.append(f"fmv.s {reg_destino}, {reg_temp}")
                elif token == '*':
                    resultado = val_a * val_b
                    if variable_destino:
                        reg_temp = f"ft{self.contador_temporal + 2}"
                        reg_destino = self.variables[variable_destino]['registro']
                        self.codigo_ensamblador.append(f"fmul.s {reg_temp}, {reg_a}, {reg_b}")
                        self.codigo_ensamblador.append(f"fmv.s {reg_destino}, {reg_temp}")
                elif token == '/':
                    if val_b == 0:
                        raise Exception("Error: División por cero")
                    resultado = val_a / val_b
                    if variable_destino:
                        reg_temp = f"ft{self.contador_temporal + 2}"
                        reg_destino = self.variables[variable_destino]['registro']
                        self.codigo_ensamblador.append(f"fdiv.s {reg_temp}, {reg_a}, {reg_b}")
                        self.codigo_ensamblador.append(f"fmv.s {reg_destino}, {reg_temp}")
                elif token == '^':
                    resultado = val_a ** val_b
                    if variable_destino:
                        reg_destino = self.variables[variable_destino]['registro']
                        self.codigo_ensamblador.append(f"# Función pow llamada")

                stack.append(resultado)

            elif token.lower() in ['sin', 'cos', 'tan']:
                a_token = stack.pop()
                if isinstance(a_token, str) and a_token in self.variables:
                    val_a = self.obtener_valor(a_token)
                    reg_a = self.variables[a_token]['registro']
                else:
                    val_a = float(a_token)
                    reg_a = f"ft{self.contador_temporal}"

                resultado = self.evaluar_funcion(token.lower(), val_a)

                if variable_destino:
                    reg_destino = self.variables[variable_destino]['registro']
                    self.codigo_ensamblador.append(f"# Llamada a función {token}")
                    self.codigo_ensamblador.append(f"fmv.s {reg_destino}, fa0")

                stack.append(resultado)

            elif token in self.variables:
                stack.append(token)
            else:
                try:
                    stack.append(float(token))
                except ValueError:
                    raise Exception(f"Token no reconocido: {token}")

        return stack[0] if stack else 0

    def evaluar_expresion(self, expr, variable_destino=None):
        """Evalúa una expresión en notación postfija"""
        return self.evaluar_postfija(expr.split(), variable_destino)

    def encontrar_fin_bloque(self, inicio, palabra_inicio, palabra_fin):
        """Encuentra el final de un bloque (for/endfor, while/endwhile)"""
        contador = 1
        i = inicio + 1
        while i < len(self.lineas) and contador > 0:
            linea = self.lineas[i].strip().lower()
            if linea.startswith(palabra_inicio):
                contador += 1
            elif linea.startswith(palabra_fin):
                contador -= 1
            i += 1
        return i - 1

    def ejecutar_linea(self, linea, numero_linea):
        """Ejecuta una línea de código"""
        # Validar punto y coma
        self.validar_punto_coma(linea, numero_linea)

        if linea.startswith("var"):
            partes = linea.replace(";", "").split()
            for nombre in partes[1:]:
                if nombre != ':' and nombre != ',':
                    nombre = nombre.replace(',', '')
                    if nombre:
                        self.declarar_variable(nombre, 'real')

        elif linea.startswith("read"):
            nombre = linea[linea.find('(') + 1:linea.find(')')]
            nombre = nombre.strip()
            if nombre in self.variables:
                try:
                    valor = float(input(f"Ingrese valor para {nombre}: "))
                    self.asignar_valor(nombre, valor)
                    registro = self.variables[nombre]['registro']
                    self.codigo_ensamblador.append(f"# leer {nombre} → valor {valor}")
                except ValueError:
                    raise Exception("Valor inválido ingresado")
            else:
                raise Exception(f"Error: Variable '{nombre}' no declarada.")

        elif linea.startswith("print("):
            nombre = linea[linea.find('(') + 1:linea.find(')')]
            nombre = nombre.strip()
            if nombre in self.variables:
                valor = self.obtener_valor(nombre)
                registro = self.variables[nombre]['registro']
                print(valor, end='')
                self.codigo_ensamblador.append(f"# print {nombre} → valor {valor}")
            else:
                print(nombre.replace('"', '').replace("'", ""), end='')

        elif linea.startswith("println("):
            nombre = linea[linea.find('(') + 1:linea.find(')')]
            nombre = nombre.strip()
            if nombre in self.variables:
                valor = self.obtener_valor(nombre)
                registro = self.variables[nombre]['registro']
                print(valor)
                self.codigo_ensamblador.append(f"# println {nombre} → valor {valor}")
            else:
                print(nombre.replace('"', '').replace("'", ""))

        elif linea.startswith("for"):
            partes = linea.split()
            var = partes[1]
            inicio_val = partes[3]
            fin_var = partes[5]

            inicio = float(inicio_val)
            self.asignar_valor(var, inicio)
            reg_var = self.variables[var]['registro']
            self.codigo_ensamblador.append(f"li.s {reg_var}, {inicio}")

            if fin_var not in self.variables:
                raise Exception(f"Variable '{fin_var}' no declarada en el for")

            fin = self.obtener_valor(fin_var)

            etiqueta_inicio = self.obtener_nueva_etiqueta()
            etiqueta_fin = self.obtener_nueva_etiqueta()

            self.codigo_ensamblador.append(f"# Inicio del for")
            self.codigo_ensamblador.append(f"{etiqueta_inicio}:")

            fin_for = self.encontrar_fin_bloque(self.indice, "for", "endfor")

            reg_fin = self.variables[fin_var]['registro']
            reg_comp = f"ft{self.contador_temporal + 3}"
            self.codigo_ensamblador.append(f"fle.s {reg_comp}, {reg_var}, {reg_fin}")
            self.codigo_ensamblador.append(f"beqz {reg_comp}, {etiqueta_fin}")

            while self.obtener_valor(var) <= fin:
                indice_temp = self.indice + 1
                while indice_temp < fin_for:
                    self.ejecutar_linea(self.lineas[indice_temp], indice_temp + 1)
                    indice_temp += 1

                var_val = self.obtener_valor(var)
                nueva_val = var_val + 1
                self.asignar_valor(var, nueva_val)
                reg_var = self.variables[var]['registro']
                reg_uno = f"ft{self.contador_temporal + 4}"
                self.codigo_ensamblador.append(f"li.s {reg_uno}, 1.0")
                self.codigo_ensamblador.append(f"fadd.s {reg_var}, {reg_var}, {reg_uno}")

            self.codigo_ensamblador.append(f"j {etiqueta_inicio}")
            self.codigo_ensamblador.append(f"{etiqueta_fin}:")
            self.codigo_ensamblador.append(f"# Fin del for")
            self.indice = fin_for

        elif linea.startswith("while"):
            inicio_condicion = linea.find("while") + 5
            fin_condicion = linea.find(" do")
            if fin_condicion == -1:
                fin_condicion = len(linea)
            condicion = linea[inicio_condicion:fin_condicion].strip()

            etiqueta_inicio = self.obtener_nueva_etiqueta()
            etiqueta_fin = self.obtener_nueva_etiqueta()

            self.codigo_ensamblador.append(f"# Inicio del while")
            self.codigo_ensamblador.append(f"{etiqueta_inicio}:")

            fin_while = self.encontrar_fin_bloque(self.indice, "while", "endwhile")

            while self.evaluar_condicion(condicion):
                tokens = condicion.split()
                if len(tokens) == 3:
                    var1, var2, op = tokens
                    if var1 in self.variables and var2 in self.variables:
                        reg1 = self.variables[var1]['registro']
                        reg2 = self.variables[var2]['registro']
                        reg_comp = f"ft{self.contador_temporal + 2}"

                        if op == '<=':
                            self.codigo_ensamblador.append(f"fle.s {reg_comp}, {reg1}, {reg2}")
                        elif op == '<':
                            self.codigo_ensamblador.append(f"flt.s {reg_comp}, {reg1}, {reg2}")
                        elif op == '>=':
                            self.codigo_ensamblador.append(f"fge.s {reg_comp}, {reg1}, {reg2}")
                        elif op == '>':
                            self.codigo_ensamblador.append(f"fgt.s {reg_comp}, {reg1}, {reg2}")

                        self.codigo_ensamblador.append(f"beqz {reg_comp}, {etiqueta_fin}")

                indice_temp = self.indice + 1
                while indice_temp < fin_while:
                    self.ejecutar_linea(self.lineas[indice_temp], indice_temp + 1)
                    indice_temp += 1

                self.codigo_ensamblador.append(f"j {etiqueta_inicio}")

            self.codigo_ensamblador.append(f"{etiqueta_fin}:")
            self.codigo_ensamblador.append(f"# Fin del while")
            self.indice = fin_while

        elif ":=" in linea:
            nombre, expr = linea.replace(";", "").split(":=")
            nombre = nombre.strip()
            expr = expr.strip()

            if expr.replace('.', '').replace('-', '').isdigit():
                valor = float(expr)
                self.asignar_valor(nombre, valor)
                registro = self.variables[nombre]['registro']
                self.codigo_ensamblador.append(f"li.s {registro}, {valor}")
            else:
                valor = self.evaluar_expresion(expr, nombre)
                self.asignar_valor(nombre, valor)

        elif linea.startswith("write"):
            nombre = linea[linea.find('(') + 1:linea.find(')')]
            nombre = nombre.strip()
            if nombre in self.variables:
                valor = self.obtener_valor(nombre)
                registro = self.variables[nombre]['registro']
                print(f"{nombre}: {valor}")
                self.codigo_ensamblador.append(f"# escribir {nombre} → valor {valor}")
            else:
                print(nombre)

        elif linea.lower() in ["endfor", "endwhile"]:
            pass

    def mostrar_tabla_simbolos(self):
        """Muestra la tabla de símbolos"""
        print("\n--- Tabla de símbolos ---")
        print("Nombre     Tipo       Registro   Valor")
        print("-" * 40)
        for nombre, info in self.variables.items():
            valor = info['valor'] if info['valor'] is not None else 'None'
            print(f"{nombre:<10} {info['tipo']:<10} {info['registro']:<10} {valor}")

    def mostrar_codigo_ensamblador(self):
        """Muestra el código ensamblador generado"""
        print("\n--- Código ensamblador generado ---")
        for linea in self.codigo_ensamblador:
            print(linea)

    def ejecutar(self, codigo):
        """Ejecuta el programa completo"""
        self.lineas = [line.strip() for line in codigo.strip().split('\n') if line.strip()]
        self.indice = 0

        print("Ejecutando el programa...")
        print("=" * 40)

        while self.indice < len(self.lineas):
            try:
                self.ejecutar_linea(self.lineas[self.indice], self.indice + 1)
                self.indice += 1
            except Exception as e:
                print(f"Error en línea {self.indice + 1}: {e}")
                print(f"Línea: {self.lineas[self.indice]}")
                break

        print("\n--- Fin del programa ---")
        self.mostrar_tabla_simbolos()
        self.mostrar_codigo_ensamblador()


# EJEMPLOS DE PRUEBA INTERACTIVOS
def menu_principal():
    print(" INTÉRPRETE PASCAL - MENÚ PRINCIPAL ")
    print("=" * 50)
    print("1. Prueba de validación de errores")
    print("2. Programa con read() - Operaciones básicas")
    print("3. Programa con funciones trigonométricas")
    print("4. Programa con ciclo FOR")
    print("5. Programa con ciclo WHILE")
    print("6. Programa completo (combinado)")
    print("7. Ingresar código personalizado")
    print("0. Salir")
    print("=" * 50)


def prueba_errores():
    print("\n PRUEBA DE VALIDACIÓN DE ERRORES")
    print("Probando diferentes tipos de errores...")

    # Error de punto y coma
    print("\n1. Error de punto y coma:")
    interprete1 = InterpreteUnificado()
    codigo_error = """var x, y;
x := 5
print(x);"""
    print("Código:", codigo_error)
    try:
        interprete1.ejecutar(codigo_error)
    except Exception as e:
        print(f" Error capturado: {e}")

    # Error de redeclaración
    print("\n2. Error de redeclaración:")
    interprete2 = InterpreteUnificado()
    codigo_redecl = """var x;
var x;"""
    print("Código:", codigo_redecl)
    try:
        interprete2.ejecutar(codigo_redecl)
    except Exception as e:
        print(f" Error capturado: {e}")


def programa_basico():
    print("\n PROGRAMA CON READ() - OPERACIONES BÁSICAS")
    codigo = """var x, y, suma, resta, multiplicacion, division;
read(x);
read(y);
suma := x y +;
resta := x y -;
multiplicacion := x y *;
division := x y /;
println("Resultados:");
print("Suma: ");
println(suma);
print("Resta: ");
println(resta);
print("Multiplicación: ");
println(multiplicacion);
print("División: ");
println(division);"""

    print("Código a ejecutar:")
    print(codigo)
    print("\n Ingresa los valores cuando se soliciten:")

    interprete = InterpreteUnificado()
    interprete.ejecutar(codigo)


def programa_trigonometrico():
    print("\n PROGRAMA CON FUNCIONES TRIGONOMÉTRICAS")
    codigo = """var angulo, seno, coseno, tangente;
read(angulo);
seno := angulo sin;
coseno := angulo cos;
tangente := angulo tan;
println("Resultados trigonométricos:");
print("Seno: ");
println(seno);
print("Coseno: ");
println(coseno);
print("Tangente: ");
println(tangente);"""

    print("Código a ejecutar:")
    print(codigo)
    print("\n Ingresa el ángulo en radianes:")

    interprete = InterpreteUnificado()
    interprete.ejecutar(codigo)


def programa_for():
    print("\n PROGRAMA CON CICLO FOR")
    codigo = """var n, i, suma, factorial;
read(n);
suma := 0;
factorial := 1;
println("Calculando suma y factorial...");
for i := 1 to n do
    suma := suma i +;
    factorial := factorial i *;
    print("i=");
    print(i);
    print(" suma=");
    print(suma);
    print(" factorial=");
    println(factorial);
endfor
println("Resultados finales:");
print("Suma total: ");
println(suma);
print("Factorial: ");
println(factorial);"""

    print("Código a ejecutar:")
    print(codigo)
    print("\n Ingresa el valor de n:")

    interprete = InterpreteUnificado()
    interprete.ejecutar(codigo)


def programa_while():
    print("\n PROGRAMA CON CICLO WHILE")
    codigo = """var n, contador, potencia;
read(n);
contador := 1;
potencia := 1;
println("Calculando potencias de 2...");
while contador n <= do
    potencia := potencia 2 *;
    print("2^");
    print(contador);
    print(" = ");
    println(potencia);
    contador := contador 1 +;
endwhile"""

    print("Código a ejecutar:")
    print(codigo)
    print("\n Ingresa hasta qué potencia calcular:")

    interprete = InterpreteUnificado()
    interprete.ejecutar(codigo)


def programa_completo():
    print("\n PROGRAMA COMPLETO (COMBINADO)")
    codigo = """var a, b, c, discriminante, x, resultado, i;
println("Calculadora de ecuación cuadrática y análisis");
println("Ingresa los coeficientes a, b, c:");
read(a);
read(b);
read(c);
discriminante := b b * 4 a * c * -;
print("Discriminante: ");
println(discriminante);
println("Evaluando la función en varios puntos:");
for i := 1 to 3 do
    x := i;
    resultado := a x * x * b x * + c +;
    print("f(");
    print(x);
    print(") = ");
    println(resultado);
endfor
println("Análisis trigonométrico del discriminante:");
if discriminante > 0 then
    resultado := discriminante sin;
    print("sin(discriminante) = ");
    println(resultado);
endif"""

    print("Código a ejecutar:")
    print(codigo)
    print("\n Ingresa los coeficientes:")

    interprete = InterpreteUnificado()
    interprete.ejecutar(codigo)


def codigo_personalizado():
    print("\n️ CÓDIGO PERSONALIZADO")
    print("Ingresa tu código línea por línea. Escribe 'FIN' para terminar:")

    lineas = []
    while True:
        linea = input(">>> ")
        if linea.upper() == "FIN":
            break
        lineas.append(linea)

    codigo = "\n".join(lineas)
    print("\nEjecutando código personalizado...")

    interprete = InterpreteUnificado()
    interprete.ejecutar(codigo)


if __name__ == "__main__":
    while True:
        menu_principal()
        opcion = input("\nSelecciona una opción (0-7): ")

        try:
            if opcion == "0":
                print("¡FIN DEL PROGRAMA! ")
                break
            elif opcion == "1":
                prueba_errores()
            elif opcion == "2":
                programa_basico()
            elif opcion == "3":
                programa_trigonometrico()
            elif opcion == "4":
                programa_for()
            elif opcion == "5":
                programa_while()
            elif opcion == "6":
                programa_completo()
            elif opcion == "7":
                codigo_personalizado()
            else:
                print(" Opción inválida")
        except Exception as e:
            print(f" Error inesperado: {e}")

        input("\nPresiona Enter para continuar...")
        print("\n" + "=" * 80 + "\n")