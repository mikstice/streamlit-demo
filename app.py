import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def check_password():
    def password_entered():
        st.session_state["password_attempted"] = True
        if st.session_state["password"] == "mipass123":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if "password_attempted" not in st.session_state:
        st.session_state["password_attempted"] = False

    if not st.session_state["password_correct"]:
        st.text_input(
            "Ingrese contraseña:",
            type="password",
            key="password",
            on_change=password_entered
        )
        if st.session_state["password_attempted"] and not st.session_state["password_correct"]:
            st.error("Contraseña incorrecta")
        st.stop()
    return True


if check_password():
    print("ingresó correctamente la pass")
    #st.set_page_config(layout='wide')
    file_path = 'excel_softys.xlsx'
    sheet_name = 'Sheet1'
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=13, usecols='A:AN',dtype={'Soles Strategio': 'float64'})

    pd.set_option('display.float_format', '{:,.2f}'.format)

    non_day_columns = 6 
    day_columns = df.columns[non_day_columns : non_day_columns + 31]

    def color_celdas(val):
        if val == 1:
            return "background-color: turquoise"
        elif val == 2:
            return "background-color: orange"
        elif val == -1:
            return "background-color: red"
        elif val == 0:
            return "background-color: yellow"

    def asignar_zona(row):
        if row['Division'] == 'FARMACIA':
            return 'FARMACIA'
        return row['Zona']

    df['Zona_Reporte'] = df.apply(asignar_zona, axis=1)

    def contar_valores(df, col_dia_ref):
        conteo_1 = (df[col_dia_ref] == 1).sum()
        conteo_0 = (df[col_dia_ref] == 0).sum()
        conteo_2 = (df[col_dia_ref] == 2).sum()
        conteo_menos1 = (df[col_dia_ref] == -1).sum()
        return conteo_1, conteo_0, conteo_2, conteo_menos1


    #
    def get_previous_bussiness_day(ref_date):
        day_offset=1
        previous_day = ref_date - timedelta(days=day_offset)

        while True:
            if previous_day.weekday() <= 5:
                return previous_day
            day_offset += 1
            previous_day = ref_date - timedelta(days=day_offset)
    
    hoy = datetime.now()
    hoy2 = datetime(2025,5,1)
    fecha_ref = get_previous_bussiness_day(hoy)
    fecha_ant = get_previous_bussiness_day(fecha_ref)

    dia_ref = fecha_ref.day
    dia_ant = fecha_ant.day

    col_dia_ref = day_columns[dia_ref - 1]
    col_dia_ant = day_columns[dia_ant - 1] if dia_ant > 1 else None

    soles_t = df[df['Division'] == 'TRADICIONAL']['Soles Strategio'].sum()
    soles_f = df[df['Division'] == 'FARMACIA']['Soles Strategio'].sum()


    
    totales = df.groupby('Gerente')['Soles Strategio'].sum().to_dict()

    df['Peso'] = df.apply(
        lambda row: (row['Soles Strategio'] / totales[row['Gerente']]) * 100, axis=1
    )

    reporte_gerentes = df.groupby(['Gerente', 'Zona_Reporte']).agg(
        total=('Gerente', 'count'), 
        sin_desfase=pd.NamedAgg(column=col_dia_ref, aggfunc=lambda x: x.isin([0,1,2]).sum()),
        con_desfase=pd.NamedAgg(column=col_dia_ref, aggfunc=lambda x: (x == -1).sum()),
        peso_sin_desfase=pd.NamedAgg(column='Peso', aggfunc=lambda x: x[df.loc[x.index, col_dia_ref].isin([0,1,2])].sum()),
        peso_con_desfase=pd.NamedAgg(column='Peso', aggfunc=lambda x: x[df.loc[x.index, col_dia_ref] == -1].sum()),
        total_peso=('Peso','sum')
    ).reset_index()

    reporte_gerentes['%_exito'] = (reporte_gerentes['peso_sin_desfase'] / reporte_gerentes['total_peso'])
    reporte_gerentes['%_desfase'] = (reporte_gerentes['peso_con_desfase'] / reporte_gerentes['total_peso'])

    reporte_gerentes = reporte_gerentes.sort_values(by='%_exito', ascending=False)
    reporte_gerentes['%_exito'] = (reporte_gerentes['%_exito']*100).round(0).astype(int).astype(str) + '%'
    reporte_gerentes['%_desfase'] = (reporte_gerentes['%_desfase']*100).round(0).astype(int).astype(str) + '%'

    # Renombrar columnas para el reporte final
    reporte_final = reporte_gerentes.rename(columns={
        'Zona_Reporte': 'Zona',
        'total': 'Total Peso',
        'sin_desfase': 'Sin Desfase',
        'con_desfase': 'Con Desfase'
    })[['Zona', 'Gerente', 'Total Peso', 'Sin Desfase', 'Con Desfase', 
        '%_exito', '%_desfase']]
    
    day_columns = [str(i) for i in range(1,32)]

    ultimos_7_dias = [str(i) for i in range(dia_ref - 7, dia_ref + 1) if i >= 1]

    col_fijas = ["Distribuidor","Zona","Gerente"]
    
   

    st.title("Reporte Cumplimiento")

    st.subheader("Gerentes")
    st.dataframe(reporte_final)

    gerentes_disponibles = reporte_final['Gerente'].unique()
    gerente_seleccionado = st.selectbox("Selecciona un gerente para ver el detalle:", gerentes_disponibles)

    st.title("Detalle Gerente")
    df_filtrado = df[df['Gerente'] == gerente_seleccionado]

    estado = st.selectbox(
        "Filtrar según estado:",
        options=["Todas", "PENDIENTE", "REPROCESO", "OK"]
    )

    if estado == "PENDIENTE":
        df_filtrado = df_filtrado[df_filtrado[col_dia_ref] == -1]
    
    elif estado == "OK":
        df_filtrado = df_filtrado[df_filtrado[col_dia_ref] == 1]
    
    elif estado == "REPROCESO":
        df_filtrado = df_filtrado[df_filtrado[col_dia_ref] == 2]

    df_filtrado = df_filtrado[col_fijas + ultimos_7_dias]
    styled_df = df_filtrado.style.map(
        color_celdas,
        subset=ultimos_7_dias
    )
    st.dataframe(styled_df, use_container_width=True)




    tab1, tab2 = st.tabs(["Reporte Resumen", "Detalle por Gerente"])

    with tab1:
        st.subheader("Gerentes")
        st.dataframe(reporte_final)

    with tab2:
        gerente_seleccionado = st.selectbox("Selecciona un gerente:", reporte_final['Gerente'].unique())
        df_filtrado = df[df['Gerente'] == gerente_seleccionado]
        st.dataframe(df_filtrado)



