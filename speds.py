import streamlit as st
import os
import pandas as pd
import io

def run_sped_app():

    def extract_and_add_0000(file_path, record_type):
        """
        Extrai todos os registros C100 e C170 do arquivo SPED, adiciona o registro 0000 e renomeia as colunas conforme especificado.

        :param file_path: Caminho para o arquivo SPED.
        :return: Um DataFrame com dados combinados C100, C170 e 0000, com colunas renomeadas.
        """
        # Nomes das colunas para registros 0000, C100 e C170 conforme fornecido
        reg0000_columns = ["REG0000", "COD_VER", "COD_FIN", "DT_INI", "DT_FIN", "NOME", "CNPJ", "CPF", "UF", "IE", 
                        "COD_MUN", "IM", "SUFRAMA", "IND_PERFIL", "IND_ATIV"]
        c100_columns = ["REGC100", "IND_OPER", "IND_EMIT", "COD_PART", "COD_MOD", "COD_SIT", "SER", "NUM_DOC", "CHV_NFE", "DT_DOC", 
                        "DT_E_S", "VL_DOC", "IND_PGTO", "VL_DESC1", "VL_ABAT_NT1", "VL_MERC", "IND_FRT", "VL_FRT", "VL_SEG", "VL_OUT_DA", 
                        "VL_BC_ICMS1", "VL_ICMS1", "VL_BC_ICMS_ST1", "VL_ICMS_ST1", "VL_IPI1", "VL_PIS1", "VL_COFINS1", "VL_PIS_ST1", "VL_COFINS_ST"]
        c170_columns = ["REGC170", "NUM_ITEM", "COD_ITEM", "DESCR_COMPL", "QTD", "UNID", "VL_ITEM", "VL_DESC", "IND_MOV", "CST_ICMS", 
                        "CFOP", "COD_NAT", "VL_BC_ICMS", "ALIQ_ICMS", "VL_ICMS", "VL_BC_ICMS_ST", "ALIQ_ST", "VL_ICMS_ST", "IND_APUR", 
                        "CST_IPI", "COD_ENQ", "VL_BC_IPI", "ALIQ_IPI", "VL_IPI", "CST_PIS", "VL_BC_PIS", "ALIQ_PIS", "QUANT_BC_PIS", 
                        "ALIQ_PIS1", "VL_PIS", "CST_COFINS", "VL_BC_COFINS", "ALIQ_COFINS", "QUANT_BC_COFINS", "ALIQ_COFINS1", "VL_COFINS", 
                        "COD_CTA", "VL_ABAT_NT"]
        c190_columns = ["REGC190", "CST_ICMS", "CFOP", "ALIQ_ICMS", "VL_OPR", "VL_BC_ICMS", "VL_ICMS", "VL_BC_ICMS_ST", "VL_ICMS_ST", "VL_RED_BC", 
                        "VL_IPI", "COD_OBS"]

        # Inicializa um DataFrame vazio para armazenar os dados combinados
        combined_data = []

        # Lê as linhas do arquivo
        lines = file_content.split('\n')
        current_c100 = None

        for line in lines:
            if line.startswith('|0000|'):
                reg0000 = line.strip().split('|')[1:-1]
                if len(reg0000) < len(reg0000_columns):
                    reg0000 += [''] * (len(reg0000_columns) - len(reg0000))

            elif line.startswith('|C100|'):
                current_c100 = line.strip().split('|')[1:-1]
                if len(current_c100) < len(c100_columns):
                    current_c100 += [''] * (len(c100_columns) - len(current_c100))

            elif line.startswith(f'|{record_type}|') and current_c100:
                c_record = line.strip().split('|')[1:-1]
                c_columns = c170_columns if record_type == 'C170' else c190_columns
                if len(c_record) < len(c_columns):
                    c_record += [''] * (len(c_columns) - len(c_record))

                combined_record = reg0000 + current_c100 + c_record
                combined_data.append(combined_record)

        combined_df = pd.DataFrame(combined_data, columns=reg0000_columns + c100_columns + (c170_columns if record_type == 'C170' else c190_columns))

        return combined_df


    def create_pivot_table(df, rows, columns, values):
        df[values] = pd.to_numeric(df[values], errors='coerce')
        return df.pivot_table(index=rows, columns=columns, values=values, aggfunc='sum')

    def filter_cfop(df, cfop_type):
        if cfop_type == 'Entrada':
            return df[df['CFOP'].astype(str).str.startswith(('1', '2', '3'))]
        else:
            return df[df['CFOP'].astype(str).str.startswith(('5', '6', '7'))]

    def reset_state():
        for key in st.session_state.keys():
            if key not in ['record_type']:
                del st.session_state[key]

    # Streamlit app
    st.title('Processador de Arquivos SPED')

    if 'record_type' not in st.session_state:
        st.session_state['record_type'] = 'C170'

    new_record_type = st.sidebar.selectbox('Selecione o tipo de registro', ('C170', 'C190'))

    if new_record_type != st.session_state['record_type']:
        st.session_state['record_type'] = new_record_type
        reset_state()

    uploaded_files = st.file_uploader("Selecione os arquivos .txt:", type="txt", accept_multiple_files=True)

    if st.button('Processar Arquivos'):
        if uploaded_files:
            combined_df = pd.DataFrame()
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.getvalue().decode("iso-8859-1")
                data = extract_and_add_0000(file_content, st.session_state['record_type'])
                combined_df = pd.concat([combined_df, data])

            st.session_state['combined_df'] = combined_df
            st.session_state['data_processed'] = True

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                combined_df.to_excel(writer, index=False)

            output.seek(0)
            st.session_state['general_file'] = output

            st.success('Arquivos processados com sucesso!')

    if 'data_processed' in st.session_state and st.session_state['data_processed']:
        st.download_button(
            label="Baixar dados em Excel",
            data=st.session_state['general_file'],
            file_name="SPEDS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if 'combined_df' in st.session_state and not st.session_state['combined_df'].empty:
        if st.session_state['record_type'] == 'C170':
            st.subheader("Criar Resumo para C170")
            pivot_row = st.selectbox("Escolha a linha para a tabela pivot (C170)", st.session_state['combined_df'].columns)
            pivot_column = st.selectbox("Escolha a coluna para a tabela pivot (C170)", st.session_state['combined_df'].columns)
            pivot_values = st.selectbox("Escolha os valores para a tabela pivot (C170)", st.session_state['combined_df'].columns)

            if st.button('Gerar Tabela Pivot C170'):
                pivot_table = create_pivot_table(st.session_state['combined_df'], pivot_row, pivot_column, pivot_values)
                st.write(pivot_table)

                output_pivot = io.BytesIO()
                with pd.ExcelWriter(output_pivot, engine='xlsxwriter') as writer:
                    pivot_table.to_excel(writer, index=True)

                output_pivot.seek(0)

                st.download_button(
                    label="Baixar Tabela Pivot C170 em Excel",
                    data=output_pivot,
                    file_name="Pivot_Table_C170.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        elif st.session_state['record_type'] == 'C190':
            st.subheader("Criar Resumo para C190")
            cfop_type = st.radio("Selecione o tipo de CFOP (C190)", ('Entrada', 'Saída'))
            filtered_df = filter_cfop(st.session_state['combined_df'], cfop_type)

            pivot_row = st.selectbox("Escolha a linha para a tabela pivot (C190)", filtered_df.columns)
            pivot_column = st.selectbox("Escolha a coluna para a tabela pivot (C190)", filtered_df.columns)
            pivot_values = st.selectbox("Escolha os valores para a tabela pivot (C190)", filtered_df.columns)

            if st.button('Gerar Tabela Pivot C190'):
                pivot_table = create_pivot_table(filtered_df, pivot_row, pivot_column, pivot_values)
                st.write(pivot_table)

                output_pivot = io.BytesIO()
                with pd.ExcelWriter(output_pivot, engine='xlsxwriter') as writer:
                    pivot_table.to_excel(writer, index=True)

                output_pivot.seek(0)

                st.download_button(
                    label="Baixar Tabela Pivot C190 em Excel",
                    data=output_pivot,
                    file_name="Pivot_Table_C190.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )