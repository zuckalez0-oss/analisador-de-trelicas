# main.py 
# (Este arquivo deve ficar na raiz do projeto, ao lado das pastas src, data, etc.)

import os
from src.dxf_analyzer import analyze_dxf_file
from src.excel_reporter import create_excel_report

# Definindo os caminhos com base na estrutura do projeto
DATA_FOLDER = 'data'
REPORTS_FOLDER = 'reports'

def main():
    """
    Função principal que executa o fluxo de análise dos arquivos DXF.
    """
    print("Iniciando análise dos arquivos DXF na pasta 'data'...")

    # Lista todos os arquivos na pasta 'data' que terminam com .dxf
    dxf_files = [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith('.dxf')]

    if not dxf_files:
        print("Nenhum arquivo .dxf encontrado na pasta 'data'.")
        return

    for dxf_file in dxf_files:
        print(f"\nProcessando arquivo: {dxf_file}")
        file_path = os.path.join(DATA_FOLDER, dxf_file)
        
        # Analisa o arquivo DXF
        analysis_result = analyze_dxf_file(file_path)
        
        # Se a análise foi bem-sucedida, cria o relatório em Excel
        if analysis_result:
            create_excel_report(analysis_result, dxf_file, REPORTS_FOLDER)

    print("\nProcesso concluído.")

if __name__ == "__main__":
    main()