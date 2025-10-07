# main.py
import streamlit.web.bootstrap
import os
import sys

def get_base_path():
    """ Obtém o caminho base, seja em modo de desenvolvimento ou como executável. """
    if getattr(sys, 'frozen', False):
        # Rodando como .exe (congelado pelo PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Rodando como script .py normal
        return os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    # Define o diretório base onde o executável está
    BASE_DIR = get_base_path()
    
    # O nome do seu arquivo principal do Streamlit
    main_script_path = os.path.join(BASE_DIR, 'app.py')

    # Argumentos para o bootstrap do Streamlit (pode deixar vazio)
    args = []

    # Executa o servidor Streamlit diretamente do código
    streamlit.web.bootstrap.run(main_script_path, '', args, flag_options={})