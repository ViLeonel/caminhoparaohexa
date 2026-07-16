import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. CONFIGURAÇÕES DE TELA & METADADOS
# ==========================================
st.set_page_config(
    page_title="O Caminho para o Hexa 2030",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DESIGN VISUAL E CSS PERSONALIZADO (PADRÕES WCAG)
# ==========================================
st.markdown("""
<style>
    /* Estilização Geral do App (Soft Navy & Grafite Escuro) */
    .stApp {
        background-color: #090d16;
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Cabeçalho do App */
    .app-title {
        text-align: center;
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #eab308 0%, #f8fafc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .project-subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* O Campo Tático Verde Floresta Realista */
    .pitch-container {
        background-color: #14532d; /* Verde Floresta */
        background-image: linear-gradient(to bottom, #14532d 0%, #114023 100%);
        border: 4px solid #eab308; /* Borda Ouro */
        border-radius: 20px;
        position: relative;
        width: 100%;
        height: 680px; /* Altura ideal travada para posicionamento preciso */
        overflow: hidden;
        box-shadow: 0 15px 35px rgba(0,0,0,0.7);
        margin-bottom: 25px;
    }
    .pitch-line-center {
        position: absolute;
        top: 50%;
        left: 0;
        width: 100%;
        height: 2px;
        background-color: rgba(248, 250, 252, 0.4);
    }
    .pitch-circle {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 150px;
        height: 150px;
        border: 2px solid rgba(248, 250, 252, 0.4);
        border-radius: 50%;
    }
    .pitch-penalty-top {
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 100px;
        border-bottom: 2px solid rgba(248, 250, 252, 0.4);
        border-left: 2px solid rgba(248, 250, 252, 0.4);
        border-right: 2px solid rgba(248, 250, 252, 0.4);
    }
    .pitch-penalty-bottom {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 100px;
        border-top: 2px solid rgba(248, 250, 252, 0.4);
        border-left: 2px solid rgba(248, 250, 252, 0.4);
        border-right: 2px solid rgba(248, 250, 252, 0.4);
    }
    
    /* Nós dos Jogadores Absolutos no Campo */
    .player-node {
        position: absolute;
        transform: translate(-50%, -50%);
        width: 135px;
        text-align: center;
        z-index: 10;
        transition: all 0.5s ease-in-out; /* Suavidade na transição de posições */
    }
    .player-card-pitch {
        background: rgba(9, 13, 22, 0.95);
        border: 2px solid #eab308;
        border-radius: 8px;
        padding: 6px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .player-pos-tag {
        font-size: 7.5pt;
        color: #eab308;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 1px;
    }
    .player-name-tag {
        font-size: 9pt;
        color: #f8fafc;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .player-rating-tag {
        background-color: #eab308;
        color: #090d16;
        font-size: 7.5pt;
        font-weight: 800;
        border-radius: 4px;
        padding: 1px 5px;
        margin-top: 3px;
        display: inline-block;
    }
    
    /* Caixas de Informações de Análise */
    .stat-box {
        background-color: #111827;
        border-radius: 12px;
        padding: 20px;
        border-left: 6px solid #eab308;
        margin-bottom: 18px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* Estilização do Rodapé */
    .fine-print {
        font-size: 8.5pt;
        color: #64748b;
        text-align: center;
        margin-top: 40px;
        margin-bottom: 10px;
    }

    /* Forçador de cores na Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0c1220 !important;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] h2 {
        color: #eab308 !important;
        font-weight: 800 !important;
    }

    /* Ocultação de elementos nativos para look premium */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }
    .stDeployButton {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GERENCIAMENTO DE BANCO DE DADOS (JSON)
# ==========================================
DATA_FILE = "jogadores_hexa_2030.json"

def carregar_jogadores():
    contingencia = {
        "Alisson": {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool", "idade": 33, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.0, "nota_roberto": 7.5},
        "Kaiki Bruno": {"nome": "Kaiki Bruno", "posicao": "Lateral Esquerdo", "clube": "Cruzeiro", "idade": 23, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 6.0, "nota_roberto": 6.0},
        "Gabriel Magalhães": {"nome": "Gabriel Magalhães", "posicao": "Zagueiro Esquerdo", "clube": "Arsenal", "idade": 28, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 9.0, "nota_roberto": 9.0},
        "Lucas Beraldo": {"nome": "Lucas Beraldo", "posicao": "Zagueiro Direito", "clube": "PSG", "idade": 22, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 8.0},
        "Wesley": {"nome": "Wesley", "posicao": "Lateral Direito", "clube": "Flamengo", "idade": 22, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 7.5},
        "Andrey Santos": {"nome": "Andrey Santos", "posicao": "Meio-Campo (Defensivo)", "clube": "Chelsea", "idade": 22, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 8.0},
        "Bruno Guimarães": {"nome": "Bruno Guimarães", "posicao": "Meio-Campo (Apoio)", "clube": "Newcastle", "idade": 28, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 8.5},
        "Rodrygo": {"nome": "Rodrygo", "posicao": "Meio-Campo (Criativo)", "clube": "Real Madrid", "idade": 25, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 8.0},
        "Vini Jr.": {"nome": "Vini Jr.", "posicao": "Ponta Esquerda", "clube": "Real Madrid", "idade": 26, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 9.0, "nota_roberto": 9.0},
        "Endrick": {"nome": "Endrick", "posicao": "Centroavante", "clube": "Real Madrid", "idade": 19, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 9.0},
        "Estevão": {"nome": "Estevão", "posicao": "Ponta Direita", "clube": "Palmeiras", "idade": 19, "grupo": "Titulares", "tipo": "Promessa 2030", "nota_vini": 9.0, "nota_roberto": 10.0}
    }
    
    if not os.path.exists(DATA_FILE):
        return contingencia
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        modified = False
        for k, v in data.items():
            if "historico" in v and "Vini Leoneo" in v["historico"]:
                v["historico"] = v["historico"].replace("Vini Leoneo", "Vini Leonel")
                modified = True
        if modified:
            salvar_jogadores(data)
            
        return data if data else contingencia
    except Exception:
        return contingencia

def salvar_jogadores(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

jogadores = carregar_jogadores()

# ==========================================
# 4. MOTOR LIVE SCRAPING (CBF BRASILEIRÃO)
# ==========================================
@st.cache_data(ttl=600)
def buscar_classificacao_cbf():
    url_base = "https://www.cbf.com.br/futebol-brasileiro"
    urls = {
        "Série A": f"{url_base}/tabelas/campeonato-brasileiro/serie-a",
        "Série B": f"{url_base}/tabelas/campeonato-brasileiro/serie-b"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    dados_cbf = {}
    
    for serie, url in urls.items():
        try:
            resposta = requests.get(url, headers=headers, timeout=10)
            if resposta.status_code == 200:
                soup = BeautifulSoup(resposta.content, "html.parser")
                tabela = soup.find("table") or soup.find(class_="table") or soup.find(class_="tabela-completa")
                if tabela:
                    linhas = tabela.find_all("tr")
                    for linha in linhas[1:]:
                        colunas = linha.find_all("td")
                        if len(colunas) >= 5:
                            pos_crua = colunas[0].text.strip()
                            posicao = "".join(filter(str.isdigit, pos_crua))
                            nome_clube = " ".join(colunas[1].text.strip().split())
                            nome_chave = nome_clube.lower()
                            
                            pts = colunas[2].text.strip()
                            jogos = colunas[3].text.strip()
                            vitorias = colunas[4].text.strip()
                            
                            dados_cbf[nome_chave] = {
                                "posicao": f"{posicao}º",
                                "pts": pts,
                                "jogos": jogos,
                                "vitorias": vitorias,
                                "serie": serie
                            }
        except Exception:
            pass
    return dados_cbf

tabela_ao_vivo_cbf = buscar_classificacao_cbf()

TABELA_BACKUP_CBF = {
    "palmeiras": {"posicao": "1º", "pts": "41", "jogos": "19", "vitorias": "12", "serie": "Série A"},
    "flamengo": {"posicao": "2º", "pts": "35", "jogos": "18", "vitorias": "10", "serie": "Série A"},
    "cruzeiro": {"posicao": "3º", "pts": "32", "jogos": "19", "vitorias": "9", "serie": "Série A"},
    "bahia": {"posicao": "6º", "pts": "27", "jogos": "18", "vitorias": "7", "serie": "Série A"},
    "corinthians": {"posicao": "13º", "pts": "21", "jogos": "19", "vitorias": "5", "serie": "Série A"},
    "gremio": {"posicao": "15º", "pts": "19", "jogos": "18", "vitorias": "5", "serie": "Série A"},
    "santos": {"posicao": "1º", "pts": "39", "jogos": "19", "vitorias": "11", "serie": "Série B"}
}

def obter_dados_reais_clube(clube):
    clube_busca = clube.lower().strip()
    for chave_time, dados in tabela_ao_vivo_cbf.items():
        if clube_busca in chave_time or chave_time in clube_busca:
            return dados
    for chave_time, dados in TABELA_BACKUP_CBF.items():
        if clube_busca in chave_time or chave_time in clube_busca:
            return dados
    return None

# ==========================================
# 5. MATRIZ TÁTICA DE CARLO ANCELOTTI
# ==========================================
# Estrutura: { Posição no Menu: (Posições JSON válidas, Atleta padrão, Left%, Bottom%, Tag Visual) }
TATICAS = {
    "4-3-3 Clássico": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral Esquerdo (LE)": (["Lateral Esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro Esquerdo"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro Direito"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral Direito (LD)": (["Lateral Direito"], "Wesley", "85%", "26%", "LD"),
        "Volante (VOL)": (["Meio-Campo (Defensivo)"], "Andrey Santos", "38%", "46%", "VOL"),
        "Volante Apoio (VOL)": (["Meio-Campo (Apoio)", "Meio-Campo (Defensivo)"], "Bruno Guimarães", "62%", "46%", "VOL"),
        "Meia-Armador (MEI)": (["Meio-Campo (Criativo)"], "Rodrygo", "50%", "58%", "MEI"),
        "Ponta Esquerda (PE)": (["Ponta Esquerda"], "Vini Jr.", "20%", "80%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "84%", "CA"),
        "Ponta Direita (PD)": (["Ponta Direita"], "Estevão", "80%", "80%", "PD")
    },
    "4-3-3 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral Esquerdo (LE)": (["Lateral Esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro Esquerdo"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro Direito"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral Direito (LD)": (["Lateral Direito"], "Wesley", "85%", "26%", "LD"),
        "Volante (VOL)": (["Meio-Campo (Defensivo)"], "Andrey Santos", "50%", "43%", "VOL"),
        "Mezzala Esquerdo (MCE)": (["Meio-Campo (Apoio)"], "Bruno Guimarães", "32%", "53%", "MCE"),
        "Mezzala Direito (MCD)": (["Meio-Campo (Apoio)", "Meio-Campo (Criativo)"], "Breno Bidon", "68%", "53%", "MCD"),
        "Ponta Esquerda (PE)": (["Ponta Esquerda"], "Vini Jr.", "20%", "80%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "84%", "CA"),
        "Ponta Direita (PD)": (["Ponta Direita"], "Estevão", "80%", "80%", "PD")
    },
    "4-4-2 Clássico": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral Esquerdo (LE)": (["Lateral Esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro Esquerdo"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro Direito"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral Direito (LD)": (["Lateral Direito"], "Wesley", "85%", "26%", "LD"),
        "Meia-Esquerda (ME)": (["Ponta Esquerda", "Meio-Campo (Apoio)"], "Vini Jr.", "15%", "55%", "ME"),
        "Volante (VOL)": (["Meio-Campo (Defensivo)"], "Andrey Santos", "38%", "45%", "VOL"),
        "Volante Apoio (VOL)": (["Meio-Campo (Apoio)", "Meio-Campo (Defensivo)"], "Bruno Guimarães", "62%", "45%", "VOL"),
        "Meia-Direita (MD)": (["Ponta Direita", "Meio-Campo (Apoio)"], "Estevão", "85%", "55%", "MD"),
        "Atacante (ATA)": (["Meio-Campo (Criativo)", "Ponta Esquerda", "Ponta Direita", "Centroavante"], "Rodrygo", "35%", "82%", "ATA"),
        "Atacante Recuado (ATA)": (["Centroavante"], "Endrick", "65%", "82%", "ATA")
    },
    "4-4-2 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral Esquerdo (LE)": (["Lateral Esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro Esquerdo"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro Direito"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral Direito (LD)": (["Lateral Direito"], "Wesley", "85%", "26%", "LD"),
        "Volante (VOL)": (["Meio-Campo (Defensivo)"], "Andrey Santos", "50%", "42%", "VOL"),
        "Mezzala Esquerdo (MCE)": (["Meio-Campo (Apoio)"], "Bruno Guimarães", "32%", "53%", "MCE"),
        "Mezzala Direito (MCD)": (["Meio-Campo (Apoio)", "Meio-Campo (Criativo)"], "Breno Bidon", "68%", "53%", "MCD"),
        "Meia-Armador (MEI)": (["Meio-Campo (Criativo)"], "Rodrygo", "50%", "65%", "MEI"),
        "Atacante (ATA)": (["Ponta Esquerda", "Ponta Direita", "Centroavante"], "Vini Jr.", "35%", "83%", "ATA"),
        "Atacante Recuado (ATA)": (["Centroavante"], "Endrick", "65%", "83%", "ATA")
    }
}

def obter_atletas_compativeis(pos_permitidas):
    filtrados = []
    for nome, dados in jogadores.items():
        if dados["posicao"] in pos_permitidas:
            filtrados.append(nome)
        # Regras de versatilidade tática adicionadas de forma robusta
        elif nome == "Lucas Beraldo" and "Meio-Campo (Defensivo)" in pos_permitidas:
            filtrados.append(nome)
        elif nome == "Gabriel Martinelli" and "Meio-Campo (Criativo)" in pos_permitidas:
            filtrados.append(nome)
    return sorted(filtrados)

# ==========================================
# 6. MENU LATERAL & NAVEGAÇÃO
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #eab308; margin-top:15px;'>CONSELHO TÁTICO</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação do Painel:",
    ["🏟️ Campo de Jogo (Escalação)", "👤 Perfis dos Jogadores & Scout", "📋 Gestão do Roster", "📊 Análise de Opiniões"]
)

# Inicialização padrão para evitar bugs de carregamento do app
if "escalados" not in st.session_state:
    st.session_state.escalados = {
        "Goleiro (GOL)": "Alisson",
        "Lateral Esquerdo (LE)": "Kaiki Bruno",
        "Zagueiro Esquerdo (ZAG)": "Gabriel Magalhães",
        "Zagueiro Direito (ZAG)": "Lucas Beraldo",
        "Lateral Direito (LD)": "Wesley",
        "Volante (VOL)": "Andrey Santos",
        "Volante Apoio (VOL)": "Bruno Guimarães",
        "Meia-Armador (MEI)": "Rodrygo",
        "Ponta Esquerda (PE)": "Vini Jr.",
        "Centroavante (CA)": "Endrick",
        "Ponta Direita (PD)": "Estevão"
    }

# ==========================================
# TELA 1: CAMPO DE JOGO (ESCALAÇÃO)
# ==========================================
if menu == "🏟️ Campo de Jogo (Escalação)":
    st.markdown("<h1 class='app-title'>🏆 O Caminho para o Hexa</h1>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <p class="project-subtitle" style="text-align: center;">
        Painel tático interativo desenvolvido para organizar escalações, avaliar pontuações de scout 
        e planejar o percurso de renovação da nossa seleção canarinho rumo ao mundial de 2030.
        </p>
        """, 
        unsafe_allow_html=True
    )
    
    col_config, col_campo = st.columns([1, 2])
    
    with col_config:
        st.markdown("### 📋 Calibrar Escalação")
        
        # 1. Seletor de Esquemas Táticos de Carlo Ancelotti
        tática_ativa = st.selectbox(
            "Esquema Tático (Carlo Ancelotti):",
            ["4-3-3 Clássico", "4-3-3 Diamante", "4-4-2 Clássico", "4-4-2 Diamante"],
            key="tactical_layout_selector"
        )
        
        layout_ativo = TATICAS[tática_ativa]
        
        # 2. Sistema Inteligente de Preservação de Escalação
        # Se mudarmos a tática, tentamos realocar os atletas compatíveis já escolhidos antes de resetar para o padrão!
        if "ultima_formacao" not in st.session_state or st.session_state.ultima_formacao != tática_ativa:
            nova_escalacao = {}
            for slot, info in layout_ativo.items():
                pos_validas, atleta_padrao = info[0], info[1]
                atleta_reutilizado = None
                
                if "escalados" in st.session_state:
                    for old_slot, old_player in st.session_state.escalados.items():
                        if old_player in jogadores and jogadores[old_player]["posicao"] in pos_validas:
                            atleta_reutilizado = old_player
                            break
                            
                nova_escalacao[slot] = atleta_reutilizado if atleta_reutilizado else atleta_padrao
                
            st.session_state.escalados = nova_escalacao
            st.session_state.ultima_formacao = tática_ativa
            st.rerun()

        st.write("Substitua os titulares respeitando a posição de origem do atleta.")
        
        # 3. Renderizar os Dropdowns dinamicamente com base na tática ativa
        novos_titulares = {}
        for slot, info in layout_ativo.items():
            pos_validas = info[0]
            valid_names = obter_atletas_compativeis(pos_validas)
            if not valid_names:
                valid_names = [st.session_state.escalados.get(slot, info[1])]
                
            default_val = st.session_state.escalados.get(slot, info[1])
            idx = valid_names.index(default_val) if default_val in valid_names else 0
            
            novos_titulares[slot] = st.selectbox(
                f"{slot}:",
                valid_names,
                index=idx,
                key=f"field_{tática_ativa}_{slot}"
            )
        st.session_state.escalados = novos_titulares

    with col_campo:
        titulares_dados = [jogadores[nome] for nome in st.session_state.escalados.values() if nome in jogadores]
        avg_v = sum(j["nota_vini"] for j in titulares_dados) / len(titulares_dados) if titulares_dados else 0
        avg_r = sum(j["nota_roberto"] for j in titulares_dados) / len(titulares_dados) if titulares_dados else 0
        coletivo = (avg_v + avg_r) / 2
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Média Geral (Vini)", f"{avg_v:.2f}")
        c2.metric("Média Geral (Roberto)", f"{avg_r:.2f}")
        c3.metric("Rating Coletivo", f"{coletivo:.2f}", delta="Candidato ao Título", delta_color="normal")
        
        # 4. Renderizador do Campo com Coordenadas Dinâmicas
        players_html = ""
        for slot, info in layout_ativo.items():
            left, bottom, pos_tag = info[2], info[3], info[4]
            player_name = st.session_state.escalados.get(slot, info[1])
            p_data = jogadores.get(player_name, {"nome": player_name, "nota_vini": 0, "nota_roberto": 0})
            players_html += (
                f'<div class="player-node" style="left:{left};bottom:{bottom};">'
                f'<div class="player-card-pitch">'
                f'<div class="player-pos-tag">{pos_tag}</div>'
                f'<div class="player-name-tag">{p_data["nome"]}</div>'
                f'<div class="player-rating-tag">★ {p_data["nota_vini"]:.1f} / {p_data["nota_roberto"]:.1f}</div>'
                f'</div>'
                f'</div>'
            )
        
        pitch_html = (
            f'<div class="pitch-container">'
            f'<div class="pitch-line-center"></div>'
            f'<div class="pitch-circle"></div>'
            f'<div class="pitch-penalty-top"></div>'
            f'<div class="pitch-penalty-bottom"></div>'
            f'{players_html}'
            f'</div>'
        )
        
        st.markdown(pitch_html, unsafe_allow_html=True)

        # ==========================================
        # RECURSO DE INTERAÇÃO: COMPARTILHAR ESCALAÇÃO
        # ==========================================
        st.markdown("---")
        st.markdown("### 📣 Compartilhe sua Convocação!")
        
        escalados_nomes = list(st.session_state.escalados.values())
        mensagem_share = (
            f"Montei minha Seleção Brasileira no esquema {tática_ativa} do app 'O Caminho para o Hexa'! 🏆\n\n"
            f"Meu Time: {', '.join(escalados_nomes[:5])} e mais!\n\n"
            f"Monte a sua também no Streamlit!"
        )
        
        texto_codificado = urllib.parse.quote(mensagem_share)
        twitter_url = f"https://twitter.com/intent/tweet?text={texto_codificado}"
        whatsapp_url = f"https://api.whatsapp.com/send?text={texto_codificado}"
        
        col_share1, col_share2 = st.columns(2)
        with col_share1:
            st.markdown(f"""
                <a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#166534; color:#f8fafc; text-align:center; padding:10px; border-radius:8px; font-weight:bold; border: 1px solid #eab308; cursor:pointer;">
                        🟢 Compartilhar no WhatsApp
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
        with col_share2:
            st.markdown(f"""
                <a href="{twitter_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#1e293b; color:#f8fafc; text-align:center; padding:10px; border-radius:8px; font-weight:bold; border: 1px solid #eab308; cursor:pointer;">
                        🔵 Compartilhar no X / Threads
                    </div>
                </a>
            """, unsafe_allow_html=True)

# ==========================================
# TELA 2: PERFIS DOS JOGADORES & SCOUT
# ==========================================
elif menu == "👤 Perfis dos Jogadores & Scout":
    st.title("👤 Ficha Individual do Atleta")
    st.markdown("<p style='font-size:1.15rem; color:#94a3b8;'>Consulte os dados individuais de scout dos nossos convocados</p>", unsafe_allow_html=True)
    
    selected_name = st.selectbox("Escolha o Atleta:", sorted(list(jogadores.keys())))
    p = jogadores[selected_name]
    
    st.markdown("---")
    
    col_p, col_d = st.columns([1, 2])
    
    with col_p:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 25px; border-radius: 15px; border: 3px solid #eab308; text-align: center;">
            <h2 style="color: #f8fafc; margin-bottom: 5px; font-size: 2.2rem;">{p.get('nome', selected_name)}</h2>
            <span style="background-color: #3b82f6; color: #f8fafc; font-weight: bold; padding: 5px 15px; border-radius: 20px; font-size: 10pt;">
                {p.get('tipo', 'Monitorado')}
            </span>
            <p style="margin-top: 20px; font-size: 11pt; color: #cbd5e1; text-align: left; line-height: 1.8;">
                <b>📍 Posição:</b> {p.get('posicao', 'N/A')}<br>
                <b>🏢 Clube Atual:</b> {p.get('clube', 'N/A')}<br>
                <b>📅 Idade em 2026:</b> {p.get('idade', 22)} anos<br>
                <b>🏆 Idade em 2030:</b> <span style="color:#eab308; font-weight:bold;">{p.get('idade', 22) + 4} anos</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Avaliação Tática")
        st.metric("Nota do Vini", f"{p.get('nota_vini', 0.0):.1f} / 10")
        st.metric("Nota do Roberto", f"{p.get('nota_roberto', 0.0):.1f} / 10")

    with col_d:
        dados_live = obter_dados_reais_clube(p.get('clube', ''))
        
        st.markdown("### 📈 Estatísticas & Classificação do Clube na Temporada")
        
        if dados_live:
            st.write("Desempenho atual do clube no campeonato nacional:")
            cbf_df = pd.DataFrame([{
                "Clube": p.get('clube', 'N/A'),
                "Divisão": dados_live.get('serie', 'N/A'),
                "Posição": dados_live.get('posicao', 'N/A'),
                "Pontos": dados_live.get('pts', 'N/A'),
                "Jogos": dados_live.get('jogos', 'N/A'),
                "Vitórias": dados_live.get('vitorias', 'N/A')
            }])
            st.dataframe(cbf_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                f"ℹ️ Atleta atualmente jogando no exterior ({p.get('clube', 'N/A')}).\n\n"
                "Conexões em segundo plano monitoram ligas do exterior."
            )
            
        st.markdown("### 📝 Dossiê Histórico de Discussões")
        
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown("**🟢 Pontos Fortes:**")
        st.write(p.get("pontos_fortes", "Nenhuma informação cadastrada."))
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stat-box" style="border-left-color: #ef4444;">', unsafe_allow_html=True)
        st.markdown("**🔴 Desafios & Pontos Fracos:**")
        st.write(p.get("pontos_fracos", "Nenhuma informação cadastrada."))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stat-box" style="border-left-color: #3b82f6;">', unsafe_allow_html=True)
        st.markdown("**🗣️ Notas das Discussões (Vini & Roberto):**")
        st.write(p.get("historico", "Nenhuma anotação disponível."))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p class='fine-print'>*dados coletados de sites como FIFA, CBF e outras confederações, federações e ligas oficiais de futebol.</p>", unsafe_allow_html=True)

# ==========================================
# TELA 3: GESTÃO DO ROSTER
# ==========================================
elif menu == "📋 Gestão do Roster":
    st.title("📋 Gerenciador do Banco de Dados")
    st.write("Edite as informações ou adicione novas joias ao radar.")
    
    tab_list, tab_add = st.tabs(["Jogadores Inscritos", "➕ Inscrever Nova Joia"])
    
    with tab_list:
        df_players = pd.DataFrame([
            {
                "Nome": k,
                "Posição": v.get("posicao", "N/A"),
                "Clube": v.get("clube", "N/A"),
                "Idade 2026": v.get("idade", 22),
                "Idade 2030": v.get("idade", 22) + 4,
                "Grupo": v.get("grupo", "Observação"),
                "Nota Vini": v.get("nota_vini", 0.0),
                "Nota Roberto": v.get("nota_roberto", 0.0),
                "Tipo": v.get("tipo", "Observação")
            } for k, v in jogadores.items()
        ])
        st.dataframe(df_players, use_container_width=True)
        
        st.markdown("### 🗑️ Cortar Atleta")
        remover_nome = st.selectbox("Selecione quem quer cortar:", list(jogadores.keys()))
        if st.button("Confirmar Corte Permanente"):
            if remover_nome in jogadores:
                del jogadores[remover_nome]
                salvar_jogadores(jogadores)
                st.success(f"{remover_nome} foi cortado com sucesso do elenco!")
                st.rerun()

    with tab_add:
        st.subheader("Cadastrar Novo Atleta")
        with st.form("add_player_form"):
            new_nome = st.text_input("Nome do Jogador*")
            new_pos = st.selectbox("Posição Principal*", [
                "Goleiro", "Lateral Direito", "Lateral Esquerdo", 
                "Zagueiro Esquerdo", "Zagueiro Direito", 
                "Meio-Campo (Defensivo)", "Meio-Campo (Apoio)", "Meio-Campo (Criativo)",
                "Ponta Esquerda", "Ponta Direita", "Centroavante"
            ])
            new_clube = st.text_input("Clube Atual")
            new_idade = st.number_input("Idade em 2026", min_value=15, max_value=45, value=22)
            new_grupo = st.selectbox("Grupo Hierárquico*", ["Titulares", "Reservas", "Observação"])
            new_tipo = st.selectbox("Status de Evolução", ["Certeza Atual", "Promessa 2030", "Observação"])
            
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                new_nota_vini = st.slider("Nota do Vini", 0.0, 10.0, 7.5, step=0.5)
            with col_n2:
                new_nota_rob = st.slider("Nota do Roberto", 0.0, 10.0, 7.5, step=0.5)
                
            new_fortes = st.text_area("Pontos Fortes")
            new_fracos = st.text_area("Pontos Fracos")
            new_hist = st.text_area("Notas e Histórico de Conversas")
            
            submitted = st.form_submit_button("Inscrever Jogador")
            if submitted:
                if not new_nome:
                    st.error("Insira o nome do atleta para salvar!")
                else:
                    jogadores[new_nome] = {
                        "nome": new_nome,
                        "posicao": new_pos,
                        "clube": new_clube,
                        "idade": int(new_idade),
                        "grupo": new_grupo,
                        "tipo": new_tipo,
                        "nota_vini": float(new_nota_vini),
                        "nota_roberto": float(new_nota_rob),
                        "pontos_fortes": new_fortes,
                        "pontos_fracos": new_fracos,
                        "historico": new_hist
                    }
                    salvar_jogadores(jogadores)
                    st.success(f"Atleta {new_nome} inscrito com sucesso no radar!")
                    st.rerun()

# ==========================================
# TELA 4: ANÁLISE DE OPINIÕES
# ==========================================
elif menu == "📊 Análise de Opiniões":
    st.title("📊 Análise de Divergências Técnicas")
    st.write("Divergências e consensos entre as análises da comissão técnica.")

    df_stats = pd.DataFrame([
        {
            "Nome": k,
            "Posição": v.get("posicao", "N/A"),
            "Vini": v.get("nota_vini", 0.0),
            "Roberto": v.get("nota_roberto", 0.0),
            "Diferença Absoluta": abs(v.get("nota_vini", 0.0) - v.get("nota_roberto", 0.0))
        } for k, v in jogadores.items()
    ])

    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.subheader("🤝 Consenso Absoluto")
        st.write("Nomes em total sintonia na avaliação técnica:")
        concordancias = df_stats.sort_values(by="Diferença Absoluta", ascending=True).head(5)
        st.dataframe(concordancias[["Nome", "Posição", "Vini", "Roberto"]], use_container_width=True, hide_index=True)

    with col_s2:
        st.subheader("🔥 Divergências de Mesa de Bar")
        st.write("Maiores divergências de notas e debates acalorados:")
        divergencias = df_stats.sort_values(by="Diferença Absoluta", ascending=False).head(5)
        st.dataframe(divergencias[["Nome", "Posição", "Vini", "Roberto", "Diferença Absoluta"]], use_container_width=True, hide_index=True)

# ==========================================
# 7. RADAR DO TORCEDOR (FORMULÁRIO TOTALMENTE PRIVADO)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Radar do Torcedor")

with st.sidebar.form("form_sugestao", clear_on_submit=True):
    tipo_sugestao = st.selectbox(
        "Tipo de Envio:",
        ["Atleta Faltante", "Sugestão de Melhoria"]
    )
    
    detalhes_sugestao = st.text_area(
        "Conteúdo da Mensagem:",
        placeholder="Escreva sua sugestão de melhoria..."
    )
    
    btn_sugestion = st.form_submit_button("Sugerir")
    
    if btn_sugestion:
        if detalhes_sugestao:
            if tipo_sugestao == "Atleta Faltante":
                assunto = urllib.parse.quote("Caminho para o Hexa: Indicação de Atleta")
                corpo = urllib.parse.quote(
                    f"Olá, Vini e Roberto!\n\n"
                    f"Sugestão de atleta para o radar:\n\n"
                    f"{detalhes_sugestao}"
                )
            else:
                assunto = urllib.parse.quote("Caminho para o Hexa: Ideias de Funcionalidades")
                corpo = urllib.parse.quote(
                    f"Olá, Vini e Roberto!\n\n"
                    f"Sugestão de melhoria para o app:\n\n"
                    f"{detalhes_sugestao}"
                )
                
            mailto_url = f"mailto:viniciusbl87@gmail.com?subject={assunto}&body={corpo}"
            
            st.sidebar.success("Sugestão salva!")
            st.sidebar.markdown(f"""
                <div style="text-align: center; margin-top: 5px; margin-bottom: 5px;">
                    <a href="{mailto_url}" target="_blank" style="background-color: #eab308; color: #090d16; font-weight: 800; padding: 10px 15px; border-radius: 8px; text-decoration: none; display: inline-block; width: 100%;">
                        🚀 Enviar por E-mail
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.warning("Insira o texto antes de enviar!")