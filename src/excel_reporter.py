# src/excel_reporter.py

import pandas as pd
import os
from datetime import datetime

# A função calculate_stock_cutting permanece exatamente a mesma.
def calculate_stock_cutting(lengths, stock_length=6000, kerf=4):
    # (nenhuma alteração aqui)
    if not lengths: return 0
    pieces_to_cut = sorted(lengths, reverse=True)
    bar_count = 1
    current_bar_length = stock_length
    while pieces_to_cut:
        piece_cut_in_this_bar = False
        for i, piece_length in enumerate(pieces_to_cut):
            space_needed = piece_length
            if current_bar_length < stock_length: space_needed += kerf
            if current_bar_length >= space_needed:
                if current_bar_length < stock_length: current_bar_length -= kerf
                current_bar_length -= piece_length
                pieces_to_cut.pop(i)
                piece_cut_in_this_bar = True
                break
        if not piece_cut_in_this_bar and pieces_to_cut:
            bar_count += 1
            current_bar_length = stock_length
    return bar_count

def create_excel_report(pieces_data, dxf_filename, output_folder):
    """
    Cria um relatório em Excel agrupando por TIPO e PERFIL.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not pieces_data:
        print(f"Nenhum dado encontrado para o arquivo {dxf_filename}.")
        return None

    # --- MUDANÇA: Cria o DataFrame diretamente da lista de peças ---
    df = pd.DataFrame(pieces_data)
    df['Arquivo DXF'] = dxf_filename
    
    # Adiciona colunas de Índice e Peça, reiniciando a contagem para cada grupo
    df['Índice'] = df.groupby(['Tipo', 'Perfil']).cumcount() + 1
    df['Peça'] = df['Tipo'] + '_' + df['Perfil'] + '_' + df['Índice'].astype(str)
    
    # Reordena as colunas para o relatório detalhado
    detalhamento_df = df[['Índice', 'Peça', 'Comprimento (mm)', 'Tipo', 'Perfil', 'Arquivo DXF']]

    # --- MUDANÇA: Agrupa por Tipo E Perfil para o resumo ---
    summary_df = df.groupby(['Tipo', 'Perfil']).agg(
        Quantidade_de_Peças=('Comprimento (mm)', 'count'),
        Comprimento_Total_mm=('Comprimento (mm)', 'sum')
    ).reset_index()

    # Aplica o cálculo de corte para cada grupo
    summary_df['Barras de 6m Necessárias'] = summary_df.apply(
        lambda row: calculate_stock_cutting(
            df[(df['Tipo'] == row['Tipo']) & (df['Perfil'] == row['Perfil'])]['Comprimento (mm)'].tolist()
        ),
        axis=1
    )
    
    # Renomeia colunas para um visual melhor
    summary_df.rename(columns={
        'Quantidade_de_Peças': 'Quantidade de Peças',
        'Comprimento_Total_mm': 'Comprimento Total (mm)'
    }, inplace=True)
    
    # Salva o arquivo Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.splitext(dxf_filename)[0]
    output_filename = f"Relatorio_{base_filename}_{timestamp}.xlsx"
    output_path = os.path.join(output_folder, output_filename)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        detalhamento_df.to_excel(writer, sheet_name='Detalhamento das Peças', index=False)
        summary_df.to_excel(writer, sheet_name='Resumo por Perfil', index=False)

    print(f"Relatório salvo com sucesso em: {output_path}")
    
    return summary_df