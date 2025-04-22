# -*- coding: utf-8 -*-
"""
Streamlit App: Expansión de Plan de Contratación

Este script toma un archivo Excel 'Plan_Contratacion.xlsx' con columnas:
- Horario
- Tipo de Contrato
- Día de Descanso
- Personal a Contratar
- (Opcional) Refrigerio

Genera un plan expandido por agente, día, jornada, break y refrigerio.
"""

import streamlit as st
import pandas as pd
import numpy as np
import math
time

st.set_page_config(page_title="Expansión Plan Contratación", layout="centered")
st.title("Expansión de Plan de Contratación")

# Paso 1: Subir el archivo de plan original
df_uploaded = st.file_uploader("Sube tu Plan_Contratacion.xlsx", type=["xlsx"]) 
if not df_uploaded:
    st.info("Por favor, sube el archivo de Plan_Contratacion.xlsx para continuar.")
    st.stop()

# Leer Plan_Contratacion.xlsx
df = pd.read_excel(df_uploaded)

# Definir shifts_coverage (debe coincidir con tu diccionario original)
# Ejemplo reducido:
shifts_coverage = {
    # "FT_17:00_3": [1,1,0,...],
    # ... añade el resto de tus turnos ...
}

dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']

@st.cache_data
def get_shift_details(name):
    cov = shifts_coverage.get(name, [0]*24)
    total = sum(cov)
    if total == 0:
        return "-", "-"
    # Duplicar para ventana circular
    ext = cov + cov
    best = None
    for start in range(24):
        ones = 0
        for end in range(start, start+24):
            if ext[end] == 1:
                ones += 1
            if ones == total:
                length = end - start + 1
                best = (length, start)
                break
        if best:
            break
    length, start = best
    sh = start % 24
    eh = (start + length) % 24
    # Buscar break interno
    brk = "-"
    for i in range(start, start + length - 1):
        if ext[i] == 1 and ext[i+1] == 0 and ext[i+2 if i+2 < len(ext) else (i+2)%24] == 1:
            gap = (i+1) % 24
            brk = f"{gap:02d}:00-{(gap+1)%24:02d}:00"
            break
    jornada = f"{sh:02d}:00-{eh:02d}:00"
    return jornada, brk

# Procesar plan y expandir filas
data = []
for _, row in df.iterrows():
    turno = row['Horario']
    contrato = row['Tipo de Contrato']
    dso = row['Día de Descanso']
    n_personal = int(row['Personal a Contratar'])
    ref = row.get('Refrigerio', '-') if contrato.startswith('Full Time') else '-'
    jornada, brk = get_shift_details(turno)
    for i in range(1, n_personal+1):
        agente = f"{turno}-{i}"
        for dia in dias:
            if dia == dso:
                data.append({
                    'Agente': agente,
                    'Turno': turno,
                    'Tipo Contrato': contrato,
                    'Día': dia,
                    'Jornada': 'DSO',
                    'Break': '-',
                    'Refrigerio': '-'
                })
            else:
                data.append({
                    'Agente': agente,
                    'Turno': turno,
                    'Tipo Contrato': contrato,
                    'Día': dia,
                    'Jornada': jornada,
                    'Break': brk if contrato.startswith('Full Time') else '-',
                    'Refrigerio': ref
                })

expanded_df = pd.DataFrame(data)
expanded_df['Jornada'] = expanded_df['Jornada'].str.replace('24:00','00:00')

st.success("Plan expandido generado exitosamente.")
st.dataframe(expanded_df)

# Botón de descarga
def convert_df(df):
    return df.to_excel(index=False)

output_name = f"plan_final_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"

excel_data = convert_df(expanded_df)
st.download_button(
    "Descargar plan final",
    data=excel_data,
    file_name=output_name,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
