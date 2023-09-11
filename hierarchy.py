import os

def get_hierarchy(directorio, nivel=0, max_archivos=15):
    if not os.path.exists(directorio):
        return "El directorio no existe"

    if not os.path.isdir(directorio):
        return "La ruta proporcionada no es un directorio"

    resultado = ""

    for item in os.listdir(directorio):
        item_ruta = os.path.join(directorio, item)
        indentacion = "  " * nivel

        if os.path.isfile(item_ruta):
            resultado += f"{indentacion}- {item}\n"
        elif os.path.isdir(item_ruta):
            resultado += f"{indentacion}+ {item}/\n"
            if nivel < max_archivos:
                resultado += get_hierarchy(item_ruta, nivel=nivel + 1, max_archivos=max_archivos)

    return resultado

directorio_a_analizar = 'C:/Users/felip/Documents/Concurso'
hierarchy = get_hierarchy(directorio_a_analizar, max_archivos=15)
# print(hierarchy)
