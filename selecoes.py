import streamlit as st
import pandas as pd
import random
import time
import io
import numpy as np
from datetime import datetime

def run_selecoes_app():

    def unique_selection(df, column, n_samples, seed):
        """ Seleciona amostras únicas baseadas em uma coluna específica. """
        unique_values = df[column].unique()
        random.seed(seed)
        selected_values = np.random.choice(unique_values, min(n_samples, len(unique_values)), replace=False)
        return df[df[column].isin(selected_values)].sample(n=n_samples, random_state=seed)

    def main():
        st.title("Aplicativo de Seleção Aleatória")

        if 'df_selected' not in st.session_state:
            st.session_state.df_selected = None
            st.session_state.largest_data = None
            st.session_state.sampled_data = None
            st.session_state.show_sampled_data = False

        uploaded_file = st.file_uploader("Escolha um arquivo")
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, sheet_name=None)
            sheet_options = list(df.keys())
            selected_sheet = st.selectbox("Escolha a sheet", sheet_options)
            st.session_state.df_selected = df[selected_sheet]

            filter_column = st.selectbox("Selecione a coluna para filtrar repetições", ['Nenhuma'] + list(st.session_state.df_selected.columns))
            allow_repetition = True if filter_column == 'Nenhuma' else st.checkbox("Permitir repetição na coluna selecionada?")

            # Seleção dos maiores valores com filtro
            select_largest = st.checkbox("Selecionar maiores valores?")
            if select_largest:
                column_to_sort = st.selectbox("Escolha a coluna para selecionar os maiores", st.session_state.df_selected.select_dtypes(include=[np.number]).columns.tolist())
                num_largest = st.number_input("Número de maiores valores", min_value=1, max_value=len(st.session_state.df_selected))
                if allow_repetition:
                    st.session_state.largest_data = st.session_state.df_selected.nlargest(num_largest, column_to_sort)
                else:
                    st.session_state.largest_data = unique_selection(st.session_state.df_selected.nlargest(num_largest * 3, column_to_sort), filter_column, num_largest, int(time.time()))
                st.write("Maiores valores selecionados:", st.session_state.largest_data)

            # Seleção aleatória com filtro
            num_samples = st.number_input("Quantidade de amostras", min_value=1, max_value=len(st.session_state.df_selected))
            check_reproducibility = st.checkbox("Verificar reproduzibilidade?")
            seed = int(time.time()) if not check_reproducibility else st.number_input("Digite a semente (para reprodução)", value=0)

            if st.button("Gerar Amostras"):
                if allow_repetition:
                    st.session_state.sampled_data = st.session_state.df_selected.sample(n=num_samples, random_state=seed)
                else:
                    st.session_state.sampled_data = unique_selection(st.session_state.df_selected, filter_column, num_samples, seed)
                st.session_state.show_sampled_data = True

        # Exibição dos resultados e botões de download
        if st.session_state.show_sampled_data and st.session_state.sampled_data is not None:
            st.write("Amostras selecionadas:", st.session_state.sampled_data)


        if st.session_state.largest_data is not None:
            towrite_largest = io.BytesIO()
            st.session_state.largest_data.to_excel(towrite_largest, index=False, engine='xlsxwriter')
            towrite_largest.seek(0)
            st.download_button(label="Download Maiores Valores", data=towrite_largest, file_name="maiores_valores.xlsx", mime="application/vnd.ms-excel")

        if st.session_state.sampled_data is not None:
            towrite_random = io.BytesIO()
            st.session_state.sampled_data.to_excel(towrite_random, index=False, engine='xlsxwriter')
            towrite_random.seek(0)
            st.download_button(label="Download Amostras Aleatórias", data=towrite_random, file_name="amostras_aleatorias.xlsx", mime="application/vnd.ms-excel")

            log = f"Semente usada: {seed}\nSheet selecionada: {selected_sheet}\n"
        # Capturando a data e hora atuais
            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y %H:%M:%S")

                # Criando log
            file_path = uploaded_file.name  # Nome do arquivo
            log = f"Data e Hora: {date_time}\nCaminho do Arquivo: {file_path}\nSemente usada: {seed}\nSheet selecionada: {selected_sheet}\n"
            if select_largest:
                log += f"Maiores valores da coluna '{column_to_sort}' selecionados:\n{st.session_state.largest_data}\n"
            log += f"Amostras selecionadas:\n{st.session_state.sampled_data}\n"
            st.download_button(label="Download Log", data=log, file_name="log_selecao.txt", mime="text/plain")




    main()