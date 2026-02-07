import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Busca de Mandados - MG", layout="wide")
st.title("🔎 Busca de Mandados - Minas Gerais")

# 2. Função Inteligente de Leitura (Resolve o problema das vírgulas extras)
@st.cache_data
def carregar_dados():
    arquivo = 'relatorio.csv'
    dados_limpos = []
    
    try:
        # Tenta ler o arquivo linha por linha para corrigir erros manuais
        with open(arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
            
        if not linhas:
            return pd.DataFrame()

        # Pega o cabeçalho (primeira linha)
        header = linhas[0].strip().split(',')
        
        # Processa cada linha
        for linha in linhas[1:]:
            partes = linha.strip().split(',')
            if len(partes) < 10: continue # Pula linhas quebradas
            
            # Reconstrói a linha:
            # Colunas 0 a 7 são fixas. A última (-1) é fixa.
            # O "recheio" (Órgão Expedidor) é tudo que sobrou no meio.
            primeira_parte = partes[:8]
            ultima_parte = [partes[-1]]
            meio = [",".join(partes[8:-1]).replace('"', '')] 
            
            dados_limpos.append(primeira_parte + meio + ultima_parte)
            
        return pd.DataFrame(dados_limpos, columns=header)
        
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{arquivo}' não foi encontrado na pasta!")
        return pd.DataFrame()

# 3. Carrega os dados
df = carregar_dados()

if not df.empty:
    # --- LÓGICA DE EXTRAÇÃO DA CIDADE ---
    def extrair_cidade(texto):
        texto = str(texto).upper()
        if "COMARCA DE" in texto:
            # Pega o que vem DEPOIS de "COMARCA DE"
            return texto.split("COMARCA DE")[1].strip()
        return "Cidade Não Localizada"

    # Aplica a lógica em todas as linhas
    df['Cidade_Filtro'] = df['Órgão Expedidor'].apply(extrair_cidade)
    
    # Converte a coluna Data para formato de tempo (dia/mês/ano)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Cidade
    lista_cidades = sorted(df['Cidade_Filtro'].unique())
    cidade = st.sidebar.selectbox("Selecione a Cidade:", ["Todas"] + lista_cidades)
    
    # Filtro de Data
    data_min = df['Data'].min().date()
    data_max = df['Data'].max().date()
    
    data_inicio = st.sidebar.date_input("Data Início", data_min)
    data_fim = st.sidebar.date_input("Data Fim", data_max)

    # --- APLICAR FILTROS ---
    df_filtrado = df.copy()
    
    if cidade != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Cidade_Filtro'] == cidade]
        
    # Filtra por data (ignora onde a data está vazia/NaT)
    df_filtrado = df_filtrado[
        (df_filtrado['Data'].dt.date >= data_inicio) & 
        (df_filtrado['Data'].dt.date <= data_fim)
    ]

    # --- RESULTADO FINAL ---
    st.success(f"Encontrados **{len(df_filtrado)}** registros.")
    
    # Mostra a tabela (escondemos algumas colunas pra ficar mais limpo)
    colunas_visiveis = ['Nome', 'Data', 'Cidade_Filtro', 'Órgão Expedidor', 'Situação']
    st.dataframe(df_filtrado[colunas_visiveis], use_container_width=True)

else:
    st.warning("Nenhum dado carregado. Verifique o arquivo CSV.")