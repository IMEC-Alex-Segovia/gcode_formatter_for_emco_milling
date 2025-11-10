import re

def skip_line_mastercam(line: str):
    upper_line = line.upper()
    skip_code = [
        "G54", "G90", "G91", "G20", "G21", "G70", "G71", "G4", "G04", "M03", "G28", 
        "M05", "M30", "G43", "G40", "G49", "G80", "G17", "O0000", "%", "G90", "G54"]

    for code in skip_code:
        if code in upper_line:
            return True
    
    return False

def emco_gcode_from_mastercam_gcode(mastercam_file: str, emco_file: str, S: int, F: int, units: str):
    
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
            
            # ELIMINAR CÓDIGOS ESPECÍFICOS QUE QUEREMOS QUITAR
            if "G0" in output_line and skip_line_mastercam(output_line): 
                output_line = re.sub(r'\bG90\b', '', output_line, flags=re.IGNORECASE)
                output_line = re.sub(r'\bG54\b', '', output_line, flags=re.IGNORECASE)
                output_line = re.sub(r'\bA0\.\s*', '', output_line, flags=re.IGNORECASE)  # Eliminar A0.
                output_line = re.sub(r'\bS\d+\b', '', output_line, flags=re.IGNORECASE)  # Eliminar S###
                output_line = re.sub(r'\bM3\b', '', output_line, flags=re.IGNORECASE)    # Eliminar M3
                output_line = re.sub(r'\bM03\b', '', output_line, flags=re.IGNORECASE)   # Eliminar M03

            if skip_line_mastercam(output_line):
                continue

            # Eliminar comentarios
            output_line = re.sub(r"\([^)]*\)", "", output_line)
            output_line = re.sub(r";.*", "", output_line)

            # LIMPIAR ESPACIOS MÚLTIPLES
            output_line = re.sub(r'\s+', ' ', output_line).strip()

            # DETECTAR SI LA LÍNEA TIENE CÓDIGO G
            current_g_match = re.search(r'\bG(\d+)\b', output_line, re.IGNORECASE)
            if current_g_match:
                # Actualizar el último código G usado
                last_g_code = int(current_g_match.group(1))
            elif last_g_code is not None and re.search(r'\b[XYZIJRF]', output_line):
                # Si no tiene código G pero tiene movimiento, agregar el último G
                output_line = f"G{last_g_code} " + output_line

            # SOLO AGREGAR CEROS FALTANTES EN VALORES I y J (mantener I y J)
            # Para valores como I.026 -> I0.026, J3. -> J3.0
            output_line = re.sub(r'\bI\.', 'I0.', output_line, flags=re.IGNORECASE)
            output_line = re.sub(r'\bJ\.', 'J0.', output_line, flags=re.IGNORECASE)
            output_line = re.sub(r'\bI-\.', 'I-0.', output_line, flags=re.IGNORECASE)
            output_line = re.sub(r'\bJ-\.', 'J-0.', output_line, flags=re.IGNORECASE)
            
            # Para valores como J3. -> J3.0 (sin decimales después del punto)
            output_line = re.sub(r'\bI(-?\d+)\.\s', r'I\1.0 ', output_line, flags=re.IGNORECASE)
            output_line = re.sub(r'\bJ(-?\d+)\.\s', r'J\1.0 ', output_line, flags=re.IGNORECASE)
            output_line = re.sub(r'\bI(-?\d+)\.$', r'I\1.0', output_line, flags=re.IGNORECASE)
            output_line = re.sub(r'\bJ(-?\d+)\.$', r'J\1.0', output_line, flags=re.IGNORECASE)

            # CONVERSIÓN DE G2/G3 - R A CR (pero mantener I y J)
            if re.search(r"\bG[23]\b", output_line, re.IGNORECASE):
                # Solo cambiar R por CR, mantener I y J
                output_line = re.sub(r"\bR(-?\.?\d+(\.\d+)?)", r"CR\1", output_line, flags=re.IGNORECASE)

            # REEMPLAZAR F EXISTENTES - MEJORADO PARA VALORES DECIMALES
            # Manejar F con valores decimales (ej: F100.0, F50.5, etc.)
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