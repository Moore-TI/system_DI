import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO
import base64
import zipfile
import tempfile

def run_relatorios_app():
    def determinar_status1(dias):
        return "Vencido" if dias > 0 else "A Vencer"

    # Função para determinar o Status 2
    def determinar_status2(dias):
        if dias <= 30 and dias >= -30:
            return "1- De 01 a 30 dias"
        elif dias <= 60 and dias > 30 or dias <= -31 and dias >= -60:
            return "2- De 31 a 60 dias"
        elif dias <= 90 and dias > 60 or dias <= -61 and dias >= -90:
            return "3- De 61 a 90 dias"
        elif dias <= 120 and dias > 90 or dias <= -91 and dias >= -120:
            return "4- De 91 a 120 dias"
        elif dias <= 150 and dias > 120 or dias <= -121 and dias >= -150:
            return "5- De 121 a 150 dias"
        elif dias <= 180 and dias > 150 or dias <= -151 and dias >= -180:
            return "6- De 151 a 180 dias"
        elif dias <= 365 and dias > 180 or dias <= -181 and dias >= -365:
            return "7- De 181 a 365 dias"
        elif dias > 365:
            return "8- A mais de 365 dias"
        else:  # para dias menores que -365
            return "8- A mais de 365 dias Vencido"

    def to_excel(df, nome):
        # Modificação para salvar em um arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        writer = pd.ExcelWriter(temp_file.name, engine="xlsxwriter")
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        writer.close()
        return temp_file.name

    def get_table_download_link_zip(zip_file_path):
        # Função para criar um link de download do arquivo ZIP
        with open(zip_file_path, "rb") as f:
            bytes_data = f.read()
        b64 = base64.b64encode(bytes_data)
        return f'<a href="data:application/zip;base64,{b64.decode()}" download="relatorios.zip">Download Zip File</a>'

    st.title("Sistema Relatórios Financeiros")

    opcao = st.sidebar.selectbox(
        "Escolha a opção desejada:", ("Aging", "Maiores", "PEC")
    )

    if opcao == "Aging":
        st.header("Aging")

        uploaded_files = st.file_uploader(
            "Escolha os arquivos Excel para Aging",
            type=["xlsx"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            temp_df = pd.read_excel(uploaded_files[0])
            colunas = temp_df.columns

            coluna_valor = st.selectbox("Selecione a coluna de valor", colunas, key="coluna_valor")
            coluna_vencimento = st.selectbox("Selecione a coluna de data de vencimento", colunas, key="coluna_vencimento")
            calcular_prazo_medio = st.checkbox("Calcular o Prazo Médio de Recebimento", key="calcular_prazo_medio")
            
            coluna_emissao = None
            if calcular_prazo_medio:
                coluna_emissao = st.selectbox("Selecione a coluna de data de emissão", colunas, key="coluna_emissao")
            
            data_base = st.date_input("Escolha a data base", datetime.today(), key="data_base")

            processar = st.button("Processar Arquivos")

            if processar:
                zip_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                with zipfile.ZipFile(zip_temp_file.name, "w") as zipf:
                    for uploaded_file in uploaded_files:
                        df = pd.read_excel(uploaded_file)

                        # Aplicar os cálculos de Aging aqui
                        
                        df[coluna_vencimento] = pd.to_datetime(df[coluna_vencimento], format="%d/%m/%Y")

                        data_base = pd.Timestamp(data_base)
                        df["Dias em Aberto"] = (data_base - df[coluna_vencimento]).dt.days
                        df["Status 1"] = df["Dias em Aberto"].apply(determinar_status1)
                        df["Status 2"] = df["Dias em Aberto"].apply(determinar_status2)

                        if calcular_prazo_medio and coluna_emissao:
                            df[coluna_emissao] = pd.to_datetime(df[coluna_emissao])
                            df["Prazo Médio de Recebimento"] = (df[coluna_vencimento] - df[coluna_emissao]).dt.days
                        
                        df["Circulante"] = df.apply(lambda x: x[coluna_valor] if x["Dias em Aberto"] >= -365 else 0, axis=1)
                        df["Não Circulante"] = df[coluna_valor] - df["Circulante"]

                        # Salvar o DataFrame processado em um arquivo Excel temporário e adicionar ao ZIP
                        temp_excel_file = to_excel(df, f"aging_{uploaded_file.name}")
                        zipf.write(temp_excel_file, arcname=uploaded_file.name)

                # Mostrar o link de download do arquivo ZIP
                st.markdown(get_table_download_link_zip(zip_temp_file.name), unsafe_allow_html=True)

    elif opcao == "Maiores":
        st.header("Análise dos Maiores Valores")

        # Upload de múltiplos arquivos para Maiores
        uploaded_files = st.file_uploader(
            "Escolha os arquivos Excel para 'Maiores'",
            type=["xlsx"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            # Carregar um arquivo temporário para obter as colunas
            temp_df = pd.read_excel(uploaded_files[0])
            colunas = temp_df.columns

            # Configuração dos parâmetros de processamento
            campo_agrupamento_principal = st.selectbox(
                "Selecione o campo principal para agrupar",
                colunas,
                key="campo_agrupamento_principal_maiores",
            )
            campo_valor = st.selectbox(
                "Selecione o campo de valor para sumarizar",
                colunas,
                key="campo_valor_maiores",
            )

        
            incluir_campo_adicional = st.checkbox(
                "Incluir um campo adicional no sumário?",
                key="incluir_campo_adicional_maiores",
            )
            campo_adicional = None
            if incluir_campo_adicional:
                campo_adicional = st.selectbox(
                    "Selecione o campo adicional",
                    colunas,
                    key="campo_adicional_maiores",
                )

            processar = st.button("Processar Arquivos")

            if processar:
                zip_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                with zipfile.ZipFile(zip_temp_file.name, "w") as zipf:
                    for uploaded_file in uploaded_files:
                        df = pd.read_excel(uploaded_file)

                        # Aplicar processamento Maiores com as configurações definidas
                        valor_total = df[campo_valor].sum()
                        if incluir_campo_adicional and campo_adicional:
                            df_agrupado = (
                                df.groupby(
                                    [campo_agrupamento_principal, campo_adicional]
                                )[campo_valor]
                                .sum()
                                .reset_index()
                            )
                        else:
                            df_agrupado = (
                                df.groupby(campo_agrupamento_principal)[campo_valor]
                                .sum()
                                .reset_index()
                            )

                        df_agrupado["Porcentagem"] = (
                            df_agrupado[campo_valor] / valor_total
                        )
                        df_agrupado = df_agrupado.sort_values(
                            by=campo_valor, ascending=False
                        )
                        df_agrupado["Acumulado"] = df_agrupado["Porcentagem"].cumsum()

                        # Salvar o DataFrame processado em um arquivo Excel temporário
                        temp_excel_file = to_excel(
                            df_agrupado, f"maiores_{uploaded_file.name}"
                        )
                        # Adicionar o arquivo Excel ao arquivo ZIP
                        zipf.write(temp_excel_file, arcname=uploaded_file.name)

                # Mostrar o link de download do arquivo ZIP
                st.markdown(
                    get_table_download_link_zip(zip_temp_file.name),
                    unsafe_allow_html=True,
                )

    elif opcao == "PEC":
        st.header("Análise PEC")

        def faixa_dias(vencimento, valor, data_base):
            # Converter data_base para pandas.Timestamp
            print(data_base, vencimento)
            data_base = pd.to_datetime(data_base)
            vencimento = pd.to_datetime(vencimento)
            delta = data_base - vencimento
            dias = delta.days

            # Considerar somente os valores de dias acima de 0
            if dias > 0:
                if dias <= 30:
                    return "até 30 dias", valor
                elif dias <= 60:
                    return "de 31 a 60", valor
                elif dias <= 90:
                    return "de 61 a 90", valor
                elif dias <= 120:
                    return "de 91 a 120", valor
                elif dias <= 150:
                    return "de 121 a 150", valor
                elif dias <= 180:
                    return "de 151 a 180", valor
                else:
                    return "acima de 180", valor
            else:
                return "não vencido", 0

        # Upload de múltiplos arquivos para PEC
        uploaded_files = st.file_uploader(
            "Escolha os arquivos Excel para PEC",
            type=["xlsx"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            # Carregar um arquivo temporário para obter as colunas
            temp_df = pd.read_excel(uploaded_files[0])
            colunas = temp_df.columns

            # Configuração dos parâmetros de processamento
            campo_principal = st.selectbox(
                "Selecione o campo principal", colunas, key="campo_principal_pe"
            )
            campo_secundario = st.selectbox(
                "Selecione o campo secundário (opcional)",
                ["Nenhum"] + list(colunas),
                key="campo_secundario_pe",
            )
            campo_valor = st.selectbox(
                "Selecione o campo de Valor em aberto", colunas, key="campo_valor_pe"
            )
            campo_vencimento = st.selectbox(
                "Selecione o campo de Vencimento", colunas, key="campo_vencimento_pe"
            )
            data_base = st.date_input(
                "Escolha a data base", datetime.today(), key="data_base_pe"
            )

            processar = st.button("Processar Arquivos")

            if processar:
                zip_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                with zipfile.ZipFile(zip_temp_file.name, "w") as zipf:
                    for uploaded_file in uploaded_files:
                        dados_clientes = pd.read_excel(uploaded_file)

                        # Processamento dos dados
                        transformados = []
                        for _, row in dados_clientes.iterrows():
                            novo_registro = {
                                campo_principal: row[campo_principal],
                                "Valor": row[campo_valor],
                                "até 30 dias": 0,
                                "de 31 a 60": 0,
                                "de 61 a 90": 0,
                                "de 91 a 120": 0,
                                "de 121 a 150": 0,
                                "de 151 a 180": 0,
                                "acima de 180": 0,
                                "Arrasto": 0,
                            }
                            if campo_secundario != "Nenhum":
                                novo_registro[campo_secundario] = row[campo_secundario]

                            faixa, valor = faixa_dias(
                                row[campo_vencimento], row[campo_valor], data_base
                            )
                            novo_registro[faixa] = valor
                            transformados.append(novo_registro)

                        dados_transformados = pd.DataFrame(transformados)

                        # Agrupamento e exibição dos dados
                        campos_agrupamento = [campo_principal]
                        if campo_secundario != "Nenhum":
                            campos_agrupamento.append(campo_secundario)

                        dados_agrupados = (
                            dados_transformados.groupby(campos_agrupamento)
                            .agg(
                                {
                                    "Valor": "sum",
                                    "até 30 dias": "sum",
                                    "de 31 a 60": "sum",
                                    "de 61 a 90": "sum",
                                    "de 91 a 120": "sum",
                                    "de 121 a 150": "sum",
                                    "de 151 a 180": "sum",
                                    "acima de 180": "sum",
                                }
                            )
                            .reset_index()
                        )

                        # Atualização da coluna "Arrasto"
                        dados_agrupados["Arrasto"] = dados_agrupados.apply(
                            lambda row: row["Valor"] if row["acima de 180"] > 0 else 0,
                            axis=1,
                        )

                        # Salvar o DataFrame processado em um arquivo Excel temporário
                        temp_excel_file = to_excel(
                            dados_agrupados, f"PEC_{uploaded_file.name}"
                        )
                        # Adicionar o arquivo Excel ao arquivo ZIP
                        zipf.write(temp_excel_file, arcname=uploaded_file.name)

                # Mostrar o link de download do arquivo ZIP
                st.markdown(
                    get_table_download_link_zip(zip_temp_file.name),
                    unsafe_allow_html=True,
                )
