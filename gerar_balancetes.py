import streamlit as st
import pandas as pd
from io import BytesIO
import io  # IMPORTAÇÔES
import re
import zipfile


def run_gerar_balancetes_app():
    def mes_abreviado(mes):
        meses = [
            "JAN",
            "FEV",
            "MAR",
            "ABR",
            "MAI",
            "JUN",
            "JUL",
            "AGO",
            "SET",
            "OUT",
            "NOV",
            "DEZ",
        ]
        return meses[mes - 1]


    def gerar_sumario(df, mesInicial, mesFinal):
        # Colunas para agrupar e sumarizar
        colunas_sumarizacao = ["CONTA"]
        colunas_inclusao = ["CONTA", "DESCRIÇÃO", "tipo"]
        # Verifica se deve incluir a coluna 'RED'
        if "RED" in df.columns:
            colunas_inclusao.append("RED")
        # Adicionando colunas de saldo inicial, débito, crédito, movimento e saldo final
        colunas_saldo = ["SALDO INICIAL " + mes_abreviado(mesInicial)]
        colunas_saldo += [
            "DEBITO " + mes_abreviado(i) for i in range(mesInicial, mesFinal + 1)
        ]
        colunas_saldo += [
            "CREDITO " + mes_abreviado(i) for i in range(mesInicial, mesFinal + 1)
        ]
        colunas_saldo += [
            "MOVIMENTO " + mes_abreviado(i) for i in range(mesInicial, mesFinal + 1)
        ]
        colunas_saldo.append("SALDO FINAL " + mes_abreviado(mesFinal))
        # Configurando a agregação
        agregacoes = {col: "sum" for col in colunas_saldo}
        for col in colunas_inclusao:
            agregacoes[col] = "first"
        # Realizando a sumarização
        df_sumario = df.groupby(colunas_sumarizacao).agg(agregacoes)
        return df_sumario


    def adicionar_campo_variacao(df, mesInicial, mesSeguinte):
        mesInicialAbrev = mes_abreviado(mesInicial)
        mesSeguinteAbrev = mes_abreviado(mesSeguinte)
        # Nome do novo campo
        nome_campo_variacao = f"VAR_{mesInicialAbrev}"
        # Calculando a variação
        df[nome_campo_variacao] = df.apply(
            lambda row: 0
            if row[f"MOVIMENTO {mesInicialAbrev}"] == 0
            else (
                row[f"MOVIMENTO {mesInicialAbrev}"] - row[f"MOVIMENTO {mesSeguinteAbrev}"]
            )
            / row[f"MOVIMENTO {mesInicialAbrev}"],
            axis=1,
        )
        # Arredondando os valores para 2 casas decimais
        df[nome_campo_variacao] = df[nome_campo_variacao].round(2)


    def adicionar_campo_saldo_anual(df, mesInicial, mesFinal):
        # Inicializando a coluna de saldo anual
        df["SALDO_ANUAL"] = df[f"SALDO INICIAL {mes_abreviado(mesInicial)}"]
        # Somando os valores de movimento para cada mês
        for i in range(mesInicial, mesFinal + 1):
            mes_abrev = mes_abreviado(i)
            df["SALDO_ANUAL"] += df[f"MOVIMENTO {mes_abrev}"]
        # Arredondando os valores para 2 casas decimais
        df["SALDO_ANUAL"] = df["SALDO_ANUAL"].round(2)


    def adicionar_campo_conferencia_auditoria(df, mesFinal):
        mesFinalAbrev = mes_abreviado(mesFinal)

        # Calculando a conferência de auditoria
        df["CONFERÊNCIA_AUDITORIA"] = df["SALDO_ANUAL"] - df[f"SALDO FINAL {mesFinalAbrev}"]

        # Arredondando os valores para 2 casas decimais
        df["CONFERÊNCIA_AUDITORIA"] = df["CONFERÊNCIA_AUDITORIA"].round(2)


    def main():
        st.title("Gerar Balancetes")

        # Upload de múltiplos arquivos
        uploaded_files = st.file_uploader(
            "Escolha os arquivos dos balancetes (JAN a DEZ)",
            accept_multiple_files=True,
            type=["xlsx"],
        )

        # Seleção do intervalo de meses
        numMesUm, numUltimoMes = st.slider("Selecione o intervalo de meses", 1, 12, (1, 12))

        if st.button("Gerar Balancete"):
            if uploaded_files:
                dfs = []
                for uploaded_file in uploaded_files:
                    try:
                        # Lê cada arquivo Excel
                        xls = pd.ExcelFile(uploaded_file)

                        # Iterar sobre as sheets no intervalo de meses selecionado
                        for i in range(numMesUm, numUltimoMes + 1):
                            mes = xls.sheet_names[i - 1]
                            df = pd.read_excel(xls, sheet_name=mes)
                            # Processamento específico para cada sheet/mês
                            dfs.append(df)
                    except Exception as e:
                        st.error(f"Erro ao ler o arquivo: {e}")

                if dfs:
                    # Combina os DataFrames de cada mês em um único DataFrame
                    df_combinado = pd.concat(dfs)

                    # Processamento dos dados
                    df_sumario = gerar_sumario(df_combinado, numMesUm, numUltimoMes)
                    for i in range(numMesUm, numUltimoMes):
                        adicionar_campo_variacao(df_sumario, i, i + 1)
                    adicionar_campo_saldo_anual(df_sumario, numMesUm, numUltimoMes)
                    adicionar_campo_conferencia_auditoria(df_sumario, numUltimoMes)

                    # Reordenando as colunas (implemente de acordo com suas necessidades)
                    colunas_dinamicas = []
                    for i in range(numMesUm, numUltimoMes + 1):
                        mes_abrev = mes_abreviado(i)
                        colunas_dinamicas += [
                            f"SALDO INICIAL {mes_abrev}",
                            f"DEBITO {mes_abrev}",
                            f"CREDITO {mes_abrev}",
                            f"MOVIMENTO {mes_abrev}",
                        ]
                        if i < numUltimoMes:  # Para adicionar VAR_ apenas entre meses consecutivos
                            colunas_dinamicas.append(f"VAR_{mes_abrev}")

                    # Adicionar Saldo Anual, Saldo Final e Conferência de Auditoria para o mês final
                    colunas_dinamicas += [
                        "SALDO_ANUAL",
                        f"SALDO FINAL {mes_abreviado(numUltimoMes)}",
                        "CONFERÊNCIA_AUDITORIA",
                    ]

                    # Definição da Ordem Desejada com Base nas Colunas Dinâmicas
                    desired_order = ["tipo", "CONTA", "RED", "DESCRIÇÃO"] + colunas_dinamicas

                    # Filtrar a lista para incluir apenas colunas existentes no DataFrame
                    filtered_order = [col for col in desired_order if col in df_sumario.columns]

                    # Reordenando as colunas
                    try:
                        df_sumario = df_sumario[filtered_order]
                    except KeyError as e:
                        st.error(f"Erro ao reordenar as colunas: {e}")

                    # Botão para baixar o resultado
                output = io.BytesIO()
                df_sumario.to_excel(output, index=False)
                output.seek(0)  # Voltar ao início do stream
                st.download_button(
                    label="Baixar Balancete Final Modificado",
                    data=output,
                    file_name="Balancete_Final_Modificado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.error("Nenhum dado foi carregado dos arquivos.")
        else:
            st.warning(
                "Por favor, carregue os arquivos dos balancetes antes de gerar o relatório."
            )
    main()
