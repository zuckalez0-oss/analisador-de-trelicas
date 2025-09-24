# src/dxf_analyzer.py (versão final corrigida e flexível)

import ezdxf
import os
import math

# A função get_length permanece exatamente a mesma.
def get_length(entity):
    if entity.dxftype() == 'LINE':
        start_point = entity.dxf.start
        end_point = entity.dxf.end
        return math.dist(start_point, end_point)
    elif entity.dxftype() == 'LWPOLYLINE':
        with entity.points() as points:
            length = 0.0
            if len(points) < 2: return 0.0
            for i in range(len(points) - 1):
                length += math.dist(points[i], points[i+1])
            if entity.is_closed:
                length += math.dist(points[-1], points[0])
            return length
    return 0

def analyze_dxf_file(file_path):
    """
    Analisa um arquivo DXF e extrai peças.
    AGORA SUPORTA AMBOS OS FORMATOS DE LAYER:
    1. Novo: 'DIAGONAL_PERFIL_X' -> Tipo='DIAGONAL', Perfil='PERFIL_X'
    2. Antigo: 'DIAGONAL' -> Tipo='DIAGONAL', Perfil='PADRÃO'
    """
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return None

    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        extracted_pieces = []
        valid_types = ("DIAGONAL", "MONTANTE", "BANZO")

        for entity in msp:
            if entity.dxf.hasattr('layer'):
                layer_name = entity.dxf.layer.upper()
                
                piece_type = None
                piece_profile = None

                # --- LÓGICA DE CORREÇÃO ---
                # 1. Tenta o novo formato (TIPO_PERFIL) primeiro
                if '_' in layer_name:
                    parts = layer_name.split('_', 1)
                    if parts[0] in valid_types:
                        piece_type = parts[0]
                        piece_profile = parts[1]
                # 2. Se não funcionar, tenta o formato antigo (TIPO)
                else:
                    if layer_name in valid_types:
                        piece_type = layer_name
                        piece_profile = "PADRÃO" # Atribui um perfil padrão
                # --- FIM DA LÓGICA DE CORREÇÃO ---

                # Se um tipo válido foi encontrado (por qualquer um dos métodos)
                if piece_type:
                    if entity.dxftype() in ('LINE', 'LWPOLYLINE'):
                        length = get_length(entity)
                        if length > 0:
                            extracted_pieces.append({
                                'Tipo': piece_type,
                                'Perfil': piece_profile,
                                'Comprimento (mm)': length
                            })
        
        return extracted_pieces

    except IOError:
        print(f"Erro: Não foi possível ler o arquivo {file_path}.")
        return None
    except ezdxf.DXFStructureError:
        print(f"Erro: Arquivo DXF inválido ou corrompido: {file_path}.")
        return None