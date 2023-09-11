import os

def convert_to_txt(input_folder, output_folder):
    # Obtener la lista de archivos en la carpeta de entrada
    file_list = os.listdir(input_folder)

    for file_name in file_list:
        input_file_path = os.path.join(input_folder, file_name)

        # Verificar si es un archivo regular y si la extensión no es .txt
        if os.path.isfile(input_file_path) and not file_name.endswith('.txt'):
            # Leer el contenido del archivo
            with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as original_file:
                content = original_file.read()

            # Crear un nuevo archivo .txt en la carpeta de salida
            output_file_path = os.path.join(output_folder, file_name + '.txt')
            with open(output_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(f"$$$$ FILE_NAME: {file_name}$$$$\n{content}")

# Ruta de la carpeta de entrada que contiene los archivos a convertir
# input_folder = 'C:/Users/felip/Documents/Concurso'

# # Ruta de la carpeta de salida donde se guardarán los archivos de texto (.txt)
# output_folder = 'docs'

# # Crear la carpeta de salida si no existe
# if not os.path.exists(output_folder):
#     os.makedirs(output_folder)

# convert_to_txt(input_folder, output_folder)
