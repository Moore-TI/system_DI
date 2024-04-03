import streamlit as st
import pandas as pd
import io
import re


def run_tratar_balancetes_app():
    def extrair_mes(nome_arquivo, nome_sheet):
        meses = meses_escritos = {
            "JAN": "jan",
            "FEV": "fev",
            "MAR": "mar",
            "ABR": "abr",
            "MAI": "mai",
            "JUN": "jun",
            "JUL": "jul",
            "AGO": "ago",
            "SET": "set",
            "OUT": "out",
            "NOV": "nov",
            "DEZ": "dez",
        }
        for chave, valor in meses.items():
            if (
                chave.lower() in nome_arquivo.lower()
                or chave.lower() in nome_sheet.lower()
            ):
                return valor
        return "mes_desconhecido"

    # Função para processar cada arquivo Excel
    def processar_arquivo(
        uploaded_file,
        colunas_selecionadas,
        tipo_conta,
        respostaUsuario,
        digitos_passivo_receita,
    ):
        nome_arquivo = uploaded_file.name
        excel_file = pd.ExcelFile(uploaded_file)
        dfs_processados = {}
        for sheet in excel_file.sheet_names:
            mes = extrair_mes(nome_arquivo, sheet)
            df = pd.read_excel(excel_file, sheet_name=sheet)
            df_processado = processar_sheet(
                df, mes, colunas_selecionadas, respostaUsuario, digitos_passivo_receita
            )
            df_processado = df_processado.dropna(axis=1, how="all")
            # Excluir linhas
            # df_processado = df_processado.loc[df_processado['CONTA'] != "Totais do Grupo:"]

            df_processado = df_processado.dropna(subset=["DESCRIÇÃO"])
            df_processado = classificar_tipo_conta(df_processado, "CONTA", tipo_conta)

            dfs_processados[mes] = df_processado

            st.write(f"Sheet: {sheet} - Mês: {mes.upper()}", df_processado)

        return dfs_processados

    def classificar_tipo_conta(df, coluna_conta, tipo_classificacao):

        if tipo_classificacao == "Maiores":

            # Calculando o comprimento de cada conta
            comprimentos = df["CONTA"].astype(str).apply(len)
            # Identificando o maior comprimento
            maior_comprimento = comprimentos.max()
            # Classificando como 'analítica' se o comprimento da conta for igual ao maior comprimento
            df["tipo"] = comprimentos.apply(
                lambda x: "A" if x == maior_comprimento else "S"
            )
        elif tipo_classificacao == "Dois últimos dígitos":
            # Removendo espaços e garantindo que a coluna é uma string
            df["CONTA"] = df[coluna_conta].astype(str).str.replace(" ", "", regex=False)
            # Classificando como 'analítica' se a conta termina com 0, caso contrário 'sintética'
            df["tipo"] = df["CONTA"].apply(lambda x: "A" if x.endswith("0") else "S")

        return df

    # Função para processar cada sheet do arquivo
    def processar_sheet(
        df, mes, colunas_selecionadas, respostaUsuario, digitos_passivo_receita
    ):
        # Função auxiliar para converter formato de número para float
        def converter_para_float(valor):
            if isinstance(valor, str):
                return pd.to_numeric(
                    valor.replace(".", "").replace(",", "."), errors="coerce"
                )
            return valor

        # Função para extrair dígito e valor, e aplicar a lógica de multiplicação
        def extrair_e_multiplicar(saldo):
            if isinstance(saldo, str):
                digito = saldo.strip()[-1]
                valor = converter_para_float(saldo[:-1])
                if (digito == "C" and valor > 0) or (digito == "D" and valor < 0):
                    valor *= -1
                return valor, digito
            return saldo, ""

        # Função para converter dígito em valor numérico
        def converter_digito(digito):
            try:
                return int(digito)
            except ValueError:
                return 1  # Se o dígito não for numérico, não multiplicar

        # Aplicando as seleções de colunas aos dados
        df = df.rename(
            columns={
                colunas_selecionadas["conta"]: f"CONTA",
                colunas_selecionadas["descricao"]: f"DESCRIÇÃO",
                colunas_selecionadas["saldo_inicial"]: f"SALDO INICIAL {mes.upper()}",
                colunas_selecionadas["saldo_final"]: f"SALDO FINAL {mes.upper()}",
                colunas_selecionadas["debito"]: f"DEBITO {mes.upper()}",
                colunas_selecionadas["credito"]: f"CREDITO {mes.upper()}",
            }
        )

        # Verificar e renomear a coluna RED, se existir
        if "red" in colunas_selecionadas:
            df = df.rename(columns={colunas_selecionadas["red"]: "RED"})

        # Aplicar tratamentos específicos conforme a resposta do usuário
        if respostaUsuario == "Extrair dígito do saldo e multiplicar":
            (
                df[f"SALDO INICIAL {mes.upper()}"],
                df[f"SALDO INICIAL {mes.upper()} DIGITO"],
            ) = zip(*df[f"SALDO INICIAL {mes.upper()}"].apply(extrair_e_multiplicar))
            (
                df[f"SALDO FINAL {mes.upper()}"],
                df[f"SALDO FINAL {mes.upper()} DIGITO"],
            ) = zip(*df[f"SALDO FINAL {mes.upper()}"].apply(extrair_e_multiplicar))

        elif respostaUsuario == "Multiplicar pelo dígito":
            # Converter colunas de dígito para string
            df[colunas_selecionadas["digito_inicial"]] = df[
                colunas_selecionadas["digito_inicial"]
            ].astype(str)
            df[colunas_selecionadas["digito_final"]] = df[
                colunas_selecionadas["digito_final"]
            ].astype(str)

            # Aplicar a lógica de multiplicação
            df[f"SALDO INICIAL {mes.upper()}"] = df.apply(
                lambda row: (
                    row[f"SALDO INICIAL {mes.upper()}"] * -1
                    if (
                        row[colunas_selecionadas["digito_inicial"]] == "C"
                        and row[f"SALDO INICIAL {mes.upper()}"] > 0
                    )
                    or (
                        row[colunas_selecionadas["digito_inicial"]] == "D"
                        and row[f"SALDO INICIAL {mes.upper()}"] < 0
                    )
                    else row[f"SALDO INICIAL {mes.upper()}"]
                ),
                axis=1,
            )

            df[f"SALDO FINAL {mes.upper()}"] = df.apply(
                lambda row: (
                    row[f"SALDO FINAL {mes.upper()}"] * -1
                    if (
                        row[colunas_selecionadas["digito_final"]] == "C"
                        and row[f"SALDO FINAL {mes.upper()}"] > 0
                    )
                    or (
                        row[colunas_selecionadas["digito_final"]] == "D"
                        and row[f"SALDO FINAL {mes.upper()}"] < 0
                    )
                    else row[f"SALDO FINAL {mes.upper()}"]
                ),
                axis=1,
            )

        elif respostaUsuario == "Contas passivo e receita multiplicados por -1":
            for digito in digitos_passivo_receita:
                df[f"SALDO INICIAL {mes.upper()}"] = df.apply(
                    lambda row: (
                        row[f"SALDO INICIAL {mes.upper()}"] * -1
                        if str(row["CONTA"]).startswith(digito.strip())
                        else row[f"SALDO INICIAL {mes.upper()}"]
                    ),
                    axis=1,
                )
                df[f"SALDO FINAL {mes.upper()}"] = df.apply(
                    lambda row: (
                        row[f"SALDO FINAL {mes.upper()}"] * -1
                        if str(row["CONTA"]).startswith(digito.strip())
                        else row[f"SALDO FINAL {mes.upper()}"]
                    ),
                    axis=1,
                )

        def ajustar_credito(valor):
            # Se o valor for negativo, torna-o positivo
            if valor < 0:
                return -valor
            return valor

        # Convertendo DEBITO e CREDITO para numérico
        df[f"DEBITO {mes.upper()}"] = df[f"DEBITO {mes.upper()}"].apply(
            converter_para_float
        )
        df[f"CREDITO {mes.upper()}"] = df[f"CREDITO {mes.upper()}"].apply(
            converter_para_float
        )

        # Aplicando a função ajustar_credito na coluna de crédito
        df[f"CREDITO {mes.upper()}"] = df[f"CREDITO {mes.upper()}"].apply(
            ajustar_credito
        )

        # Cálculo do movimento
        df[f"MOVIMENTO {mes.upper()}"] = (
            df[f"DEBITO {mes.upper()}"] - df[f"CREDITO {mes.upper()}"]
        )

        return df

    def main():
        st.title("Processador de Balancetes")

        uploaded_files = st.file_uploader(
            "Faça o upload dos balancetes", accept_multiple_files=True
        )

        if uploaded_files:

            def ler_arquivo(uploaded_file, delimiter=","):
                # Verificando a extensão do arquivo pelo nome
                file_name = uploaded_file.name
                if (
                    file_name.endswith(".XLSX")
                    or file_name.endswith(".xls")
                    or file_name.endswith(".xlsx")
                ):
                    return pd.read_excel(uploaded_file)

                elif file_name.endswith(".csv"):
                    for encoding in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]:
                        try:
                            buffer = io.StringIO(
                                uploaded_file.getvalue().decode(encoding)
                            )
                            return pd.read_csv(buffer, delimiter=delimiter)
                        except UnicodeDecodeError:
                            continue
                    raise ValueError(
                        "Não foi possível decodificar o arquivo com codificações comuns."
                    )

                else:
                    raise ValueError("Formato de arquivo não suportado")

            # Uso da função
            exemplo_df = ler_arquivo(
                uploaded_files[0], delimiter=";"
            )  # Exemplo com ponto e vírgula como delimitador
            colunas = exemplo_df.columns.tolist()

            # Coletando seleções de coluna
            colunas_selecionadas = {
                "Nome da Empresa": st.text_input("Digite o nome da empresa"),
                "conta": st.selectbox("Selecione a coluna para CONTA", colunas),
                "descricao": st.selectbox("Selecione a coluna para DESCRIÇÃO", colunas),
                "saldo_inicial": st.selectbox(
                    "Selecione a coluna para SALDO INICIAL", colunas
                ),
                "debito": st.selectbox("Selecione a coluna para DEBITO", colunas),
                "credito": st.selectbox("Selecione a coluna para CREDITO", colunas),
                "saldo_final": st.selectbox(
                    "Selecione a coluna para SALDO FINAL", colunas
                ),
            }

            empresa = colunas_selecionadas["Nome da Empresa"]

            coluna_red = st.selectbox(
                "Selecione a coluna para RED (opcional)", ["Nenhuma"] + colunas
            )
            if coluna_red != "Nenhuma":
                colunas_selecionadas["red"] = coluna_red

            respostaUsuario = st.selectbox(
                "Escolha uma opção:",
                (
                    "Sem tratamento de saldos",
                    "Contas passivo e receita multiplicados por -1",
                    "Multiplicar pelo dígito",
                    "Extrair dígito do saldo e multiplicar",
                    "Somar saldos",
                ),
            )

            if respostaUsuario == "Multiplicar pelo dígito":
                coluna_digito_inicial = st.selectbox(
                    "Selecione a coluna para DÍGITO INICIAL", colunas
                )
                coluna_digito_final = st.selectbox(
                    "Selecione a coluna para DÍGITO FINAL", colunas
                )
                colunas_selecionadas["digito_inicial"] = coluna_digito_inicial
                colunas_selecionadas["digito_final"] = coluna_digito_final

            digitos_passivo_receita = []
            if respostaUsuario == "Contas passivo e receita multiplicados por -1":
                digitos_passivo_receita = st.text_input(
                    "Digite os dígitos iniciais das contas de passivo e receita (separados por vírgula):"
                ).split(",")

            tipo_conta = st.selectbox(
                "Selecione a opção para classificação o Tipo",
                ["Maiores", "Digito Final"],
            )
            # Processando todos os arquivos com as seleções feitas
            for uploaded_file in uploaded_files:
                todos_dfs = {}
                for uploaded_file in uploaded_files:
                    dfs_processados = processar_arquivo(
                        uploaded_file,
                        colunas_selecionadas,
                        tipo_conta,
                        respostaUsuario,
                        digitos_passivo_receita,
                    )
                    todos_dfs.update(dfs_processados)

                # Escrever todos os DataFrames em um único arquivo Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    for mes, df in todos_dfs.items():
                        df.to_excel(writer, sheet_name=mes, index=False)

                st.download_button(
                    label="Download Excel",
                    data=output.getvalue(),
                    file_name=f"Balancetes_Processados_{empresa}.xlsx",
                    mime="application/vnd.ms-excel",
                )

    main()
