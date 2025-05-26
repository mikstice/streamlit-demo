import streamlit as st
import pandas as pd
import matplotlib as plt


def check_password():
    def password_entered():
        if st.session_state["password"] == "mipass123":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Ingrese la contraseña", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Contraseña incorrecta. Intente de nuevo", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if check_password():

    df = pd.read_excel("datos_clientes.xlsx")

    st.title("Resumen - DEMO ALFA FAKE GA")

    st.subheader("♫♫ Datos Completos")
    st.dataframe(df)

    resumen = df.groupby("CLIENTE")["MONTO"].sum().sort_values(ascending=False).head(4).reset_index()
    resumen["♫♀ del total"] = (resumen["MONTO"] / df["MONTO"].sum() * 100).round(2)

    st.subheader("╣ Top 4 Clientes X Monto")
    st.dataframe(resumen)

    st.subheader("Representación Gráfica")

    fig, ax = plt.subplots()
    ax.pie(resumen["MONTO"], labels=resumen["CLIENTE"], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
