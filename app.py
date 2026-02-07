import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Sgt Wanderson Busca de Mandados - MG", layout="wide")
st.title("🔎 Busca de Mandados - MG")

# 2. Função de Leitura e Limpeza dos Dados
@st.cache_data
def carregar_dados_selecionados():
    arquivo = 'relatorio.csv'
    dados = []
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                # Usa "Pendente de Cumprimento" para dividir a linha em duas partes seguras
                if "Pendente de Cumprimento" in linha:
                    partes = linha.split("Pendente de Cumprimento")
                    
                    # --- PARTE 1: Dados Pessoais (Antes da situação) ---
                    prefixo_bruto = partes[0].strip(',')
                    
                    # Separa a Data de Nascimento do resto (último campo do prefixo)
                    if ',' in prefixo_bruto:
                        resto_dados, _ = prefixo_bruto.rsplit(',', 1)
                    else:
                        resto_dados = prefixo_bruto
                    
                    # Divide os dados restantes por vírgula
                    campos = resto_dados.split(',')
                    
                    # Mapeamento das Colunas (considerando possíveis deslocamentos leves)
                    # Coluna 2 (Índice 1): Nome
                    nome = campos[1].strip().replace('"', '') if len(campos) > 1 else "N/A"
                    
                    # Coluna 3 (Índice 2): Alcunha
                    alcunha = campos[2].strip().replace('"', '') if len(campos) > 2 else ""
                    
                    # Coluna 4 (Índice 3): Nome da Mãe (NOVO)
                    nome_mae = campos[3].strip().replace('"', '') if len(campos) > 3 else ""
                    
                    # --- PARTE 2: Dados do Processo (Depois da situação) ---
                    sufixo = partes[1].strip(',')
                    
                    if ',' in sufixo:
                        partes_sufixo = sufixo.split(',', 1)
                        data_mandado = partes_sufixo[0]  # Coluna 8
                        orgao = partes_sufixo[1]         # Coluna 9
                    else:
                        data_mandado = sufixo
                        orgao = ""
                    
                    # Adiciona as colunas desejadas (2, 3, 4, 8 e 9)
                    dados.append({
                        'Nome': nome,
                        'Alcunha': alcunha,
                        'Nome da Mãe': nome_mae,  # Adicionado
                        'Data do Mandado': data_mandado,
                        'Órgão Expedidor': orgao
                    })
                    
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{arquivo}' não foi encontrado!")
        return pd.DataFrame()
    
    return pd.DataFrame(dados)

# 3. Carrega os dados
df = carregar_dados_selecionados()

if not df.empty:
    # --- PROCESSAMENTO EXTRA ---
    
    # Lógica para extrair a cidade (para o filtro)
    def extrair_cidade(texto):
        texto = str(texto).upper()
        if "COMARCA DE" in texto:
            return texto.split("COMARCA DE")[1].split(',')[0].strip()
        return "Cidade Não Localizada"

    df['Cidade_Filtro'] = df['Órgão Expedidor'].apply(extrair_cidade)
    
    # Converter datas
    df['Data do Mandado'] = pd.to_datetime(df['Data do Mandado'], dayfirst=True, errors='coerce')
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Cidade
    lista_cidades = sorted(df['Cidade_Filtro'].unique())
    cidade = st.sidebar.selectbox("Selecione a Cidade:", ["Todas"] + lista_cidades)
    
    # Filtro de Data
    df_datas_validas = df.dropna(subset=['Data do Mandado'])
    if not df_datas_validas.empty:
        data_min = df_datas_validas['Data do Mandado'].min().date()
        data_max = df_datas_validas['Data do Mandado'].max().date()
        
        st.sidebar.markdown("---")
        data_inicio = st.sidebar.date_input("De:", data_min)
        data_fim = st.sidebar.date_input("Até:", data_max)
    else:
        data_inicio, data_fim = None, None

    # --- APLICAR FILTROS ---
    df_filtrado = df.copy()
    
    if cidade != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Cidade_Filtro'] == cidade]
        
    if data_inicio and data_fim:
        df_filtrado = df_filtrado[
            (df_filtrado['Data do Mandado'].dt.date >= data_inicio) & 
            (df_filtrado['Data do Mandado'].dt.date <= data_fim)
        ]

    # Ordenação (Mais recente primeiro)
    df_filtrado = df_filtrado.sort_values(by='Data do Mandado', ascending=False)

    # --- EXIBIÇÃO ---
    st.success(f"Encontrados **{len(df_filtrado)}** registros.")
    
    # Formata a data para texto
    df_filtrado['Data do Mandado'] = df_filtrado['Data do Mandado'].dt.strftime('%d/%m/%Y')
    
    # Define as colunas finais para exibição (Incluindo Nome da Mãe)
    colunas_finais = ['Nome', 'Alcunha', 'Nome da Mãe', 'Data do Mandado', 'Órgão Expedidor']
    st.dataframe(df_filtrado[colunas_finais], use_container_width=True, hide_index=True)

else:

    st.warning("Nenhum dado carregado.")

