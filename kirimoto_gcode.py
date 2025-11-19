import re
import math

def skip_line(line: str):
    upper_line = line.upper()
    skip_code = ["G54", "G90", "G91", "G20", "G21", "G70", "G71", "G4", "G04", "M03", "M05", "M30"]

    for code in skip_code:
        if code in upper_line:
            return True
    
    return False

def check_if_xy(line: str):
    return ("X" in line.upper()) or ("Y" in line.upper())

def emco_gcode_from_kirimoto_gcode(kiri_file: str, emco_file: str, S: int, F: int, units: str):
    
    SEQUENCE_STEP = 10
    sequence = SEQUENCE_STEP
    last_z = None
    z_milling = False
    xy_milling = False

    with open(kiri_file, 'r') as input_file, open(emco_file, 'w') as output_file:

        # CABECERA DEL PROGRAMA
        output_file.write(f"N{sequence} G90\n")
        sequence += SEQUENCE_STEP
        output_file.write(f"N{sequence} {'G71' if units == 'mm' else 'G70'}\n")
        sequence += SEQUENCE_STEP
        output_file.write(f"N{sequence} M03 S{S}\n")
        sequence += SEQUENCE_STEP
        
        for line in input_file:
            output_line = line.strip()
            
            if skip_line(output_line):
                continue

            # Eliminar comentarios
            output_line = re.sub(r"\([^)]*\)", "", output_line)
            output_line = re.sub(r";.*", "", output_line)

            line_contains_xy = check_if_xy(output_line)

            # DETECCIÓN DE MOVIMIENTOS EN Z
            match_z = re.search(r"Z(-?\d+(\.\d+)?)", output_line, re.IGNORECASE)
            if match_z:
                current_z = float(match_z.group(1))

                if last_z is not None:
                    if current_z < last_z:   # Bajando en Z
                        z_milling = True
                        output_line = re.sub(r"\bG0\b", "G1", output_line, flags=re.IGNORECASE)
                    elif current_z > last_z: # Subiendo en Z
                        z_milling = False
            
                last_z = current_z
            
            # CONVERTIR G0 A G1 CUANDO SE ESTÁ MAQUINANDO
            if "G0" in output_line.upper() and (z_milling or xy_milling) and line_contains_xy:
                output_line = re.sub(r"\bG0\b", "G1", output_line, flags=re.IGNORECASE)
                output_line = re.sub(r"\sF[0-9\.]+", "", output_line)
            
            # DETECCIÓN DE G2/G3 Y CONVERSIÓN DE I,J A CR O R A CR
            if re.search(r"\bG[23]\b", output_line, re.IGNORECASE):
                match_i = re.search(r"I(-?\d+(\.\d+)?)", output_line, re.IGNORECASE)
                match_j = re.search(r"J(-?\d+(\.\d+)?)", output_line, re.IGNORECASE)

                # Si tiene I y J, calcular R y convertir a CR
                if match_i and match_j:
                    i = float(match_i.group(1))
                    j = float(match_j.group(1))
                    r = math.sqrt(i**2 + j**2)

                    # Eliminar I y J
                    output_line = re.sub(r"\sI-?\d+(\.\d+)?", "", output_line, flags=re.IGNORECASE)
                    output_line = re.sub(r"\sJ-?\d+(\.\d+)?", "", output_line, flags=re.IGNORECASE)

                    # Agregar CR con 4 decimales
                    output_line += f" CR{r:.4f}"
                # Si ya tiene R, simplemente cambiar R por CR
                else:
                    output_line = re.sub(r"\bR(-?\d+(\.\d+)?)", r"CR\1", output_line, flags=re.IGNORECASE)

            xy_milling = line_contains_xy

            # AHORA SÍ REEMPLAZAR S y F EXISTENTES - DESPUÉS DE TODAS LAS CONVERSIONES
            if re.search(r'\bS\d+', output_line, re.IGNORECASE):
                output_line = re.sub(r'\bS\d+', f'S{S}', output_line, flags=re.IGNORECASE)
            
            if re.search(r'\bF\d+', output_line, re.IGNORECASE):
                output_line = re.sub(r'\bF\d+', f'F{F}', output_line, flags=re.IGNORECASE)
            
            # Si no tiene F pero es movimiento G1/G2/G3, agregar F
            if re.search(r'\bG[123]\b', output_line, re.IGNORECASE) and not re.search(r'\bF\d+', output_line, re.IGNORECASE):
                output_line += f' F{F}'

            # Escribir solo si queda contenido
            if output_line.strip():
                if "M6" in output_line:
                    output_file.write(f"N{sequence} M05\n")
                    sequence += SEQUENCE_STEP
                output_file.write(f"N{sequence} {output_line}\n")
                sequence += SEQUENCE_STEP
                if "M6" in output_line:
                    output_file.write(f"N{sequence} M03 S{S}\n")
                    sequence += SEQUENCE_STEP

        # FINAL DEL PROGRAMA
        output_file.write(f"N{sequence} M05\n")
        sequence += SEQUENCE_STEP
        output_file.write(f"N{sequence} M30\n")