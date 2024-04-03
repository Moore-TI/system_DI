# app_principal.py
import streamlit as st
from speds import run_sped_app
from relatorios_financeiros import run_relatorios_app
from selecoes import run_selecoes_app
from tratar_balancetes import run_tratar_balancetes_app
from gerar_balancetes import run_gerar_balancetes_app
from streamlit_option_menu import option_menu
from streamlit_extras.app_logo import add_logo


# A chamada para set_page_config deve ser a primeira
st.set_page_config(page_title="Sistema DI", layout="wide")


def main():
    # Sidebar para seleção da aplicação
    with st.sidebar:
        st.image("img_logo.jfif", width=100)    
        st.sidebar.title("Menu")
        app_choice = option_menu(
            "Menu",
            [
                "Home",
                "SPEDs",
                "Relatorios Financeiros",
                "Seleções Aleatórias",
                "Balancetes",
            ],
            icons=["house", "gear", "bank", "infinity", "cash-coin"],
            menu_icon="cast",
            default_index=1,
        )

    # Executar a aplicação selecionada
    if app_choice == "Home":
        st.title("Sistema DI")
        st.divider()  # 👈 Draws a horizontal rule

        st.write("Bem-vindo ao Sistema do Departamento Interno!")
    elif app_choice == "SPEDs":
        run_sped_app()
    elif app_choice == "Relatorios Financeiros":
        run_relatorios_app()
    elif app_choice == "Seleções Aleatórias":
        run_selecoes_app()
    elif app_choice == "Balancetes":
        balancetes_choice = st.sidebar.selectbox(
            "Escolha a aplicação",
            [
                "Tratar Balancetes",
                "Gerar Balancetes",
            ],
        )
        if balancetes_choice == "Tratar Balancetes":
            run_tratar_balancetes_app()
        elif balancetes_choice == "Gerar Balancetes":
            run_gerar_balancetes_app()


if __name__ == "__main__":
    main()
