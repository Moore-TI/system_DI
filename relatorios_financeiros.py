import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO
import base64


def run_relatorios_app():
    # Função para determinar o Status 1
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

    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        writer.close()
        processed_data = output.getvalue()
        return processed_data

    def get_table_download_link_excel(df, nome):
        val = to_excel(df)
        b64 = base64.b64encode(val)  # b64encode é necessário para codificação binária
        return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{nome}.xlsx">Download Excel File</a>'

    st.sidebar.title("Menu de escolha")
    # Adicionando uma sidebar com opções de navegação
    opcao = st.sidebar.selectbox(
        "Escolha a opção desejada:", ("Aging", "Maiores", "PECLD")
    )

    # Interface do Streamlit
    st.title("Sistema Relatórios Financeiros")
    # Interface do Streamlit

    # Ações baseadas na opção escolhida na sidebar
    if opcao == "Aging":
        st.header("Aging")

        # Todo o código relacionado ao processo de "Aging" deve ficar aqui dentro
        # Upload do arquivo Excel
        uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

        if uploaded_file is not None:
            # Carregamento dos dados do Excel
            df = pd.read_excel(uploaded_file)

            coluna_valor = st.selectbox("Selecione a coluna de valor", df.columns)

            # Seleção da coluna de data de vencimento
            coluna_vencimento = st.selectbox(
                "Selecione a coluna de data de vencimento", df.columns
            )

            # Opção para adicionar o cálculo do Prazo Médio de Recebimento
            calcular_prazo_medio = st.checkbox("Calcular o Prazo Médio de Recebimento")

            coluna_emissao = None
            if calcular_prazo_medio:
                # Seleção da coluna de data de emissão
                coluna_emissao = st.selectbox(
                    "Selecione a coluna de data de emissão", df.columns
                )

            # Entrada da data base
            data_base = st.date_input("Escolha a data base", datetime.today())

            if st.button("Classificar Datas"):
                # Convertendo a coluna de datas para o formato de data
                df[coluna_vencimento] = pd.to_datetime(df[coluna_vencimento])

                # Convertendo a data base para pd.Timestamp para compatibilidade
                data_base = pd.Timestamp(data_base)

                # Calculando 'Dias em Aberto'
                df["Dias em Aberto"] = (data_base - df[coluna_vencimento]).dt.days

                # Determinando 'Status 1' e 'Status 2'
                df["Status 1"] = df["Dias em Aberto"].apply(determinar_status1)
                df["Status 2"] = df["Dias em Aberto"].apply(determinar_status2)

                if calcular_prazo_medio and coluna_emissao:
                    # Convertendo a coluna de emissão para o formato de data
                    df[coluna_emissao] = pd.to_datetime(df[coluna_emissao])
                    # Calculando o Prazo Médio de Recebimento
                    df["Prazo Médio de Recebimento"] = (
                        df[coluna_vencimento] - df[coluna_emissao]
                    ).dt.days

                    # Calculando 'Circulante'
                df["Circulante"] = df.apply(
                    lambda x: x[coluna_valor] if x["Dias em Aberto"] >= -365 else 0,
                    axis=1,
                )

                # Calculando 'Não Circulante'
                df["Não Circulante"] = df[coluna_valor] - df["Circulante"]

                # Mostrando os resultados
                st.write(df)
                # Gerando o link para download em formato Excel
                if not df.empty:
                    st.markdown(
                        get_table_download_link_excel(df, "Aging"),
                        unsafe_allow_html=True,
                    )

    elif opcao == "Maiores":
        st.header("Análise dos Maiores Valores")

        # Upload do arquivo Excel para a opção "Maiores"
        uploaded_file = st.file_uploader(
            "Escolha um arquivo Excel para 'Maiores'", type=["xlsx"]
        )

        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)

            # Permitindo ao usuário selecionar o campo principal para agrupamento
            campo_agrupamento_principal = st.selectbox(
                "Selecione o campo principal para agrupar", df.columns
            )

            # Permitindo ao usuário selecionar o campo de valores para sumarização
            campo_valor = st.selectbox(
                "Selecione o campo de valor para sumarizar", df.columns
            )

            # Opção para adicionar um campo adicional no sumário
            incluir_campo_adicional = st.checkbox(
                "Incluir um campo adicional no sumário?"
            )
            campo_adicional = None
            if incluir_campo_adicional:
                campo_adicional = st.selectbox(
                    "Selecione o campo adicional", df.columns
                )

            if st.button("Gerar Sumário"):
                # Calculando o valor total
                valor_total = df[campo_valor].sum()

                # Agrupando e sumarizando os valores
                if incluir_campo_adicional and campo_adicional:
                    df_agrupado = (
                        df.groupby([campo_agrupamento_principal, campo_adicional])[
                            campo_valor
                        ]
                        .sum()
                        .reset_index()
                    )
                else:
                    df_agrupado = (
                        df.groupby(campo_agrupamento_principal)[campo_valor]
                        .sum()
                        .reset_index()
                    )

                # Calculando a porcentagem
                df_agrupado["Porcentagem"] = df_agrupado[campo_valor] / valor_total

                # Ordenando os valores sumarizados em ordem decrescente
                df_agrupado = df_agrupado.sort_values(by=campo_valor, ascending=False)

                # Calculando a soma cumulativa para a coluna 'Acumulado'
                df_agrupado["Acumulado"] = df_agrupado["Porcentagem"].cumsum()

                # Mostrando os resultados
                st.write(df_agrupado)

                # Gerando o link para download em formato Excel
                if not df_agrupado.empty:
                    st.markdown(
                        get_table_download_link_excel(df_agrupado, "Maiores"),
                        unsafe_allow_html=True,
                    )

    if opcao == "PECLD":
        # Função para determinar a faixa de dias baseada na data de vencimento
        def faixa_dias(vencimento, valor, data_base):
            # Converter data_base para pandas.Timestamp
            data_base = pd.to_datetime(data_base)

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

        st.header("Análise PECLD")

        # Upload de arquivo
        uploaded_file = st.file_uploader("Escolha um arquivo", type=["xlsx"])

        if uploaded_file is not None:
            dados_clientes = pd.read_excel(uploaded_file)

            # Seletores de coluna
            campo_principal = st.selectbox(
                "Selecione o campo principal", dados_clientes.columns
            )
            campo_secundario = st.selectbox(
                "Selecione o campo secundário (opcional)",
                ["Nenhum"] + list(dados_clientes.columns),
            )
            campo_valor = st.selectbox(
                "Selecione o campo de Valor em aberto", dados_clientes.columns
            )
            campo_vencimento = st.selectbox(
                "Selecione o campo de Vencimento", dados_clientes.columns
            )

            # Seletor de data base
            data_base = st.date_input("Escolha a data base", datetime.today())
            if st.button("Gerar PECLD"):
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
                    lambda row: row["Valor"] if row["acima de 180"] > 0 else 0, axis=1
                )

                # Exibição dos dados processados
                st.write("Dados Agrupados:", dados_agrupados)

                # Gerando o link para download em formato Excel
                if not dados_agrupados.empty:
                    st.markdown(
                        get_table_download_link_excel(dados_agrupados, "PECLD"),
                        unsafe_allow_html=True,
                    )
