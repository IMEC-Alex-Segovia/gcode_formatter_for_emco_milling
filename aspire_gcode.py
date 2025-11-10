import re
import math

def skip_line_aspire(line: str):
    upper_line = line.upper()
    skip_code = [
        "G54", "G90", "G91", "G20", "G21", "G70", "G71", "G4", "G04", "M03", "M3", "G28", 
        "M05", "M30", "G43", "G40", "G49", "G80", "G17", ";", "%", "G54",
        'L100', 'G451', 'L2', 'G17D1', 'MSG', 'G53', 'G64', 'TRANS', "M0"
    ]

    for code in skip_code:
        if code in upper_line:
            return True
    
    return False


def emco_gcode_from_aspire_gcode(mastercam_file: str, emco_file: str, S: int, F: int, units: str):
    
    SEQUENCE_STEP = 10
    sequence = SEQUENCE_STEP
    last_g_code = None  # Registro del último código G usado

    with open(mastercam_file, 'r') as input_file, open(emco_file, 'w') as output_file:

        # CABECERA DEL PROGRAMA
        output_file.write(f"N{sequence} G90\n")
        sequence += SEQUENCE_STEP
        output_file.write(f"N{sequence} {'G71' if units == 'mm' else 'G70'}\n")
        sequence += SEQUENCE_STEP
        output_file.write(f"N{sequence} M03 S{S}\n")
        sequence += SEQUENCE_STEP
        
        for line in input_file:
            output_line = line.strip()
            
            # Eliminar números de secuencia (Nxxx) al inicio de la línea
            output_line = re.sub(r'^N\d+\s*', '', output_line)

            # 🔧 Normalizar formato M06T# → M6 T#
            output_line = re.sub(r'\bM0?6T(\d+)\b', r'M6 T\1', output_line, flags=re.IGNORECASE)

            # 🔧 Reordenar formato T# M6 → M6 T#
            output_line = re.sub(r'\bT(\d+)\s*M0?6\b', r'M6 T\1', output_line, flags=re.IGNORECASE)

            # Eliminar comentarios
            output_line = re.sub(r"\([^)]*\)", "", output_line)
            output_line = re.sub(r";.*", "", output_line)

            # ELIMINAR CÓDIGOS ESPECÍFICOS QUE QUEREMOS QUITAR
            if skip_line_aspire(output_line):
                continue

            # LIMPIAR ESPACIOS MÚLTIPLES
            output_line = re.sub(r'\s+', ' ', output_line).strip()

            # --- DETECTAR CAMBIO DE HERRAMIENTA Y AGREGAR M05 ANTES ---
            tool_change_detected = False
            tool_number = None
            
            # Detectar M6 T1, M6 T2, etc.
            m6_t_match = re.search(r'M6\s+T(\d+)', output_line, re.IGNORECASE)
            if m6_t_match:
                tool_change_detected = True
                tool_number = m6_t_match.group(1)
            
            # Si se detectó cambio de herramienta, agregar M05 antes
            if tool_change_detected:
                output_file.write(f"N{sequence} M05\n")
                sequence += SEQUENCE_STEP

            # --- CONVERSIÓN DE G2/G3 CON I J - PATRÓN MÁS FLEXIBLE ---
            if re.search(r"\bG[23]\b", output_line, re.IGNORECASE):
                aspire_arc_pattern = re.compile(r'^(.*G[23].*[XY][0-9.-]+)\s+([0-9.-]+)\s+([0-9.-]+)(.*)$', re.IGNORECASE)
                match_aspire_arc = aspire_arc_pattern.search(output_line)
                
                if match_aspire_arc:
                    part1 = match_aspire_arc.group(1)   
                    num_i = match_aspire_arc.group(2)   
                    num_j = match_aspire_arc.group(3)   
                    part_end = match_aspire_arc.group(4) 
                    
                    # Agregar ceros si faltan
                    if num_i.startswith('.'):
                        num_i = '0' + num_i
                    elif num_i.startswith('-.'):
                        num_i = '-0' + num_i[1:]
                    
                    if num_j.startswith('.'):
                        num_j = '0' + num_j
                    elif num_j.startswith('-.'):
                        num_j = '-0' + num_j[1:]
                    
                    output_line = f"{part1} I{num_i} J{num_j}{part_end}"
                
                # También cambiar R por CR
                output_line = re.sub(r"\bR(-?\.?\d+(\.\d+)?)", r"CR\1", output_line, flags=re.IGNORECASE)

            # REEMPLAZAR F EXISTENTES
            if re.search(r'\bF\d+(\.\d+)?', output_line, re.IGNORECASE):
                output_line = re.sub(r'\bF\d+(\.\d+)?', f'F{F}', output_line, flags=re.IGNORECASE)
            
            # Si no tiene F pero es movimiento G0/G1/G2/G3, agregar F
            if re.search(r'\bG[0123]\b', output_line, re.IGNORECASE) and not re.search(r'\bF\d+(\.\d+)?', output_line, re.IGNORECASE):
                output_line += f' F{F}'

            # Escribir solo si queda contenido
            if output_line.strip():
                output_file.write(f"N{sequence} {output_line}\n")
                sequence += SEQUENCE_STEP

        # FINAL DEL PROGRAMA
        output_file.write(f"N{sequence} M05\n")
        sequence += SEQUENCE_STEP
        output_file.write(f"N{sequence} M30\n")
