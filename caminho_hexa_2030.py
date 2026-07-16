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
        transition: all 0.5s ease-in-out;
    }
    .player-card-pitch {
        background: rgba(9, 13, 22, 0.95);
        border: 2px solid #eab308; /* Fallback padrão */
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
# 3. DICIONÁRIOS DE TRADUÇÃO DE POSIÇÕES
# ==========================================
ABREVIACOES = {
    "Goleiro": "GOL",
    "Lateral-esquerdo": "LE",
    "Zagueiro": "ZAG",
    "Lateral-direito": "LD",
    "Volante": "VOL",
    "Mezzala esquerdo": "MCE",
    "Mezzala direito": "MCD",
    "Meia-armador": "MEI",
    "Ponta-esquerda": "PE",
    "Ponta-direita": "PD",
    "Segundo atacante": "SA",
    "Centroavante": "CA"
}

# ==========================================
# 4. GERENCIAMENTO DE BANCO DE DADOS (JSON)
# ==========================================
DATA_FILE = "jogadores_hexa_2030.json"

def normalizar_banco_dados(data):
    if "Vini Jr." in data:
        data["Vinicius Junior"] = data.pop("Vini Jr.")
        data["Vinicius Junior"]["nome"] = "Vinicius Junior"
        
    if "Wesley" in data and "Wesley França" not in data:
        data["Wesley França"] = data.pop("Wesley")
        data["Wesley França"]["nome"] = "Wesley França"

    atualizacoes_obrigatorias = {
        "Wesley França": {
            "posicao": "Lateral-direito",
            "posicoes_multiplas": ["Lateral-direito", "Lateral-esquerdo"],
            "clube": "Roma"
        },
        "Denner": {
            "posicao": "Lateral-esquerdo",
            "posicoes_multiplas": ["Lateral-esquerdo"],
            "clube": "Chelsea"
        },
        "Luciano Juba": {
            "posicao": "Lateral-esquerdo",
            "posicoes_multiplas": ["Lateral-esquerdo", "Mezzala esquerdo"],
            "clube": "Bahia"
        },
        "Lucas Beraldo": {
            "posicao": "Zagueiro",
            "posicoes_multiplas": ["Zagueiro", "Lateral-esquerdo"],
            "clube": "Paris Saint-Germain"
        },
        "Andrey Santos": {
            "posicao": "Volante",
            "posicoes_multiplas": ["Volante", "Mezzala esquerdo", "Mezzala direito", "Lateral-esquerdo"],
            "clube": "Chelsea"
        },
        "Bruno Guimarães": {
            "posicao": "Mezzala esquerdo",
            "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"],
            "clube": "Newcastle"
        },
        "Rodrygo": {
            "posicao": "Ponta-direita",
            "posicoes_multiplas": ["Ponta-direita", "Ponta-esquerda", "Meia-armador", "Segundo atacante", "Centroavante"],
            "clube": "Real Madrid"
        },
        "Breno Bidon": {
            "posicao": "Mezzala esquerdo",
            "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante", "Meia-armador"],
            "clube": "Corinthians"
        },
        "Gabriel Mec": {
            "posicao": "Meia-armador",
            "posicoes_multiplas": ["Meia-armador", "Ponta-esquerda", "Segundo atacante"],
            "clube": "Grêmio"
        },
        "Vinicius Junior": {
            "posicao": "Ponta-esquerda",
            "posicoes_multiplas": ["Ponta-esquerda", "Segundo atacante", "Centroavante"],
            "clube": "Real Madrid"
        },
        "Estevão": {
            "posicao": "Ponta-direita",
            "posicoes_multiplas": ["Ponta-direita", "Meia-armador"],
            "clube": "Palmeiras"
        },
        "Gabriel Martinelli": {
            "posicao": "Ponta-esquerda",
            "posicoes_multiplas": ["Ponta-esquerda", "Meia-armador", "Mezzala esquerdo"],
            "clube": "Arsenal"
        }
    }

    for jogador, campos in atualizacoes_obrigatorias.items():
        if jogador in data:
            for campo, valor in campos.items():
                data[jogador][campo] = valor

    pos_map_limpeza = {
        "Goleiro": "Goleiro",
        "Lateral Esquerdo": "Lateral-esquerdo",
        "Lateral-esquerdo": "Lateral-esquerdo",
        "Lateral Direito": "Lateral-direito",
        "Lateral-direito": "Lateral-direito",
        "Zagueiro Esquerdo": "Zagueiro",
        "Zagueiro Direito": "Zagueiro",
        "Zagueiro": "Zagueiro",
        "Meio-Campo (Defensivo)": "Volante",
        "Volante": "Volante",
        "Meio-Campo (Apoio)": "Mezzala esquerdo",
        "Meio-Campo (Criativo)": "Meia-armador",
        "Ponta Esquerda": "Ponta-esquerda",
        "Ponta-esquerda": "Ponta-esquerda",
        "Ponta Direita": "Ponta-alta",
        "Ponta-direita": "Ponta-alta",
        "Centroavante": "Centroavante"
    }

    for jogador, info in data.items():
        curr_pos = info.get("posicao")
        if curr_pos in pos_map_limpeza:
            info["posicao"] = pos_map_limpeza[curr_pos]
            
        if "posicoes_multiplas" not in info or not info["posicoes_multiplas"]:
            info["posicoes_multiplas"] = [info.get("posicao", "Observação")]

    return data

def carregar_jogadores():
    contingencia = {
        "Alisson": {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool", "idade": 33, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.0, "nota_roberto": 7.5, "posicoes_multiplas": ["Goleiro"]},
        "Kaiki Bruno": {"nome": "Kaiki Bruno", "posicao": "Lateral-esquerdo", "clube": "Cruzeiro", "idade": 23, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 6.0, "nota_roberto": 6.0, "posicoes_multiplas": ["Lateral-esquerdo"]},
        "Gabriel Magalhães": {"nome": "Gabriel Magalhães", "posicao": "Zagueiro", "clube": "Arsenal", "idade": 28, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 9.0, "nota_roberto": 9.0, "posicoes_multiplas": ["Zagueiro"]},
        "Lucas Beraldo": {"nome": "Lucas Beraldo", "posicao": "Zagueiro", "clube": "Paris Saint-Germain", "idade": 22, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 8.0, "posicoes_multiplas": ["Zagueiro", "Lateral-esquerdo"]},
        "Wesley França": {"nome": "Wesley França", "posicao": "Lateral-direito", "clube": "Roma", "idade": 22, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 7.5, "posicoes_multiplas": ["Lateral-direito", "Lateral-esquerdo"]},
        "Andrey Santos": {"nome": "Andrey Santos", "posicao": "Volante", "clube": "Chelsea", "idade": 22, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 8.0, "posicoes_multiplas": ["Volante", "Mezzala esquerdo", "Mezzala direito", "Lateral-esquerdo"]},
        "Bruno Guimarães": {"nome": "Bruno Guimarães", "posicao": "Mezzala esquerdo", "clube": "Newcastle", "idade": 28, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 8.5, "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"]},
        "Rodrygo": {"nome": "Rodrygo", "posicao": "Ponta-direito", "clube": "Real Madrid", "idade": 25, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 8.0, "posicoes_multiplas": ["Ponta-direito", "Ponta-esquerda", "Meia-armador", "Segundo atacante", "Centroavante"]},
        "Vinicius Junior": {"nome": "Vinicius Junior", "posicao": "Ponta-esquerda", "clube": "Real Madrid", "idade": 26, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 9.0, "nota_roberto": 9.0, "posicoes_multiplas": ["Ponta-esquerda", "Segundo atacante", "Centroavante"]},
        "Endrick": {"nome": "Endrick", "posicao": "Centroavante", "clube": "Real Madrid", "idade": 19, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 8.0, "nota_roberto": 9.0, "posicoes_multiplas": ["Centroavante"]},
        "Estevão": {"nome": "Estevão", "posicao": "Ponta-direita", "clube": "Palmeiras", "idade": 19, "grupo": "Titulares", "tipo": "Promessa 2030", "nota_vini": 9.0, "nota_roberto": 10.0, "posicoes_multiplas": ["Ponta-direita", "Meia-armador"]},
        "Denner": {"nome": "Denner", "posicao": "Lateral-esquerdo", "clube": "Chelsea", "idade": 18, "grupo": "Reservas", "tipo": "Promessa 2030", "nota_vini": 7.0, "nota_roberto": 8.0, "posicoes_multiplas": ["Lateral-esquerdo"]},
        "Luciano Juba": {"nome": "Luciano Juba", "posicao": "Lateral-esquerdo", "clube": "Bahia", "idade": 26, "grupo": "Observação", "nota_vini": 6.5, "nota_roberto": 7.0, "posicoes_multiplas": ["Lateral-esquerdo", "Mezzala esquerdo"]},
        "Breno Bidon": {"nome": "Breno Bidon", "posicao": "Mezzala esquerdo", "clube": "Corinthians", "idade": 21, "grupo": "Reservas", "tipo": "Promessa 2030", "nota_vini": 7.0, "nota_roberto": 8.0, "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante", "Meia-armador"]},
        "Gabriel Mec": {"nome": "Gabriel Mec", "posicao": "Meia-armador", "clube": "Grêmio", "idade": 18, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.5, "nota_roberto": 7.5, "posicoes_multiplas": ["Meia-armador", "Ponta-esquerda", "Segundo atacante"]},
        "Gabriel Martinelli": {"nome": "Gabriel Martinelli", "posicao": "Ponta-esquerda", "clube": "Arsenal", "idade": 25, "grupo": "Reservas", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 8.0, "posicoes_multiplas": ["Ponta-esquerda", "Meia-armador", "Mezzala esquerdo"]}
    }
    
    if not os.path.exists(DATA_FILE):
        salvar_jogadores(contingencia)
        return contingencia
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data = normalizar_banco_dados(data)
        
        modified = False
        for k, v in data.items():
            if "historico" in v and "Vini Leoneo" in v["historico"]:
                v["historico"] = v["historico"].replace("Vini Leoneo", "Vini Leonel")
                modified = True
        
        salvar_jogadores(data)
        return data if data else contingencia
    except Exception:
        return contingencia

def salvar_jogadores(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

jogadores = carregar_jogadores()

# ==========================================
# 5. MOTOR LIVE SCRAPING (CBF BRASILEIRÃO)
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
                        colunas = merge = linha.find_all("td")
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
# 6. MATRIZ TÁTICA DO CARLO ANCELOTTI
# ==========================================
TATICAS = {
    "4-3-3 Clássico": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "26%", "LD"),
        "Volante (VOL)": (["Volante"], "Andrey Santos", "38%", "46%", "VOL"),
        "Volante Apoio (VOL)": (["Volante", "Mezzala esquerdo", "Mezzala direito"], "Bruno Guimarães", "62%", "46%", "VOL"),
        "Meia-Armador (MEI)": (["Meia-armador"], "Rodrygo", "50%", "58%", "MEI"),
        "Ponta-esquerda (PE)": (["Ponta-esquerda"], "Vinicius Junior", "20%", "80%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "84%", "CA"),
        "Ponta-direita (PD)": (["Ponta-direita"], "Estevão", "80%", "80%", "PD")
    },
    "4-3-3 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "26%", "LD"),
        "Volante (VOL)": (["Volante"], "Andrey Santos", "50%", "43%", "VOL"),
        "Mezzala Esquerdo (MCE)": (["Mezzala esquerdo"], "Bruno Guimarães", "32%", "53%", "MCE"),
        "Mezzala Direito (MCD)": (["Mezzala direito", "Mezzala esquerdo", "Meia-armador"], "Breno Bidon", "68%", "53%", "MCD"),
        "Ponta-esquerda (PE)": (["Ponta-esquerda"], "Vinicius Junior", "20%", "80%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "84%", "CA"),
        "Ponta-direita (PD)": (["Ponta-direita"], "Estevão", "80%", "80%", "PD")
    },
    "4-4-2 Clássico": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "26%", "LD"),
        "Meia-Esquerda (ME)": (["Ponta-esquerda", "Mezzala esquerdo", "Lateral-esquerdo"], "Vinicius Junior", "15%", "55%", "ME"),
        "Volante (VOL)": (["Volante"], "Andrey Santos", "38%", "45%", "VOL"),
        "Volante Apoio (VOL)": (["Volante", "Mezzala esquerdo", "Mezzala direito"], "Bruno Guimarães", "62%", "45%", "VOL"),
        "Meia-Direita (MD)": (["Ponta-direita", "Lateral-direito"], "Estevão", "85%", "55%", "MD"),
        "Segundo Atacante (SA)": (["Segundo atacante", "Ponta-esquerda", "Ponta-direito", "Meia-armador"], "Rodrygo", "35%", "82%", "SA"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "65%", "82%", "CA")
    },
    "4-4-2 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "23%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "26%", "LD"),
        "Volante (VOL)": (["Volante"], "Andrey Santos", "50%", "42%", "VOL"),
        "Mezzala Esquerdo (MCE)": (["Mezzala esquerdo"], "Bruno Guimarães", "32%", "53%", "MCE"),
        "Mezzala Direito (MCD)": (["Mezzala direito", "Mezzala esquerdo", "Meia-armador"], "Breno Bidon", "68%", "53%", "MCD"),
        "Meia-Armador (MEI)": (["Meia-armador"], "Rodrygo", "50%", "65%", "MEI"),
        "Segundo Atacante (SA)": (["Ponta-esquerda", "Ponta-direito", "Segundo atacante", "Centroavante"], "Vinicius Junior", "35%", "83%", "SA"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "65%", "83%", "CA")
    }
}

def obter_atletas_compativeis(pos_permitidas):
    filtrados = []
    for nome, dados in jogadores.items():
        pos_do_atleta = dados.get("posicoes_multiplas", [dados.get("posicao")])
        if any(pos in pos_permitidas for pos in pos_do_atleta):
            filtrados.append(nome)
    return sorted(filtrados)

def formatar_jogador_com_posicao(nome):
    p = jogadores.get(nome)
    if not p:
        return nome
    pos_list = p.get("posicoes_multiplas", [p.get("posicao", "OBS")])
    abrevs = [ABREVIACOES.get(pos, "OBS") for pos in pos_list]
    abrevs_clean = []
    for a in abrevs:
        if a not in abrevs_clean:
            abrevs_clean.append(a)
    abrev_str = "/".join(abrevs_clean)
    return f"{nome} ({abrev_str})"

# ==========================================
# 7. MENU LATERAL & NAVEGAÇÃO UNIVERSAL
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #eab308; margin-top:15px;'>CONSELHO TÁTICO</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação do Painel:",
    ["🏟️ Campo de Jogo (Escalação)", "👤 Perfis dos Jogadores & Scout", "📋 Gestão do Roster", "📊 Análise de Opiniões"]
)

# Inicialização padrão dos dados de sessão
if "escalados" not in st.session_state:
    st.session_state.escalados = {
        "Goleiro (GOL)": "Alisson",
        "Lateral-esquerdo (LE)": "Kaiki Bruno",
        "Zagueiro Esquerdo (ZAG)": "Gabriel Magalhães",
        "Zagueiro Direito (ZAG)": "Lucas Beraldo",
        "Lateral-direito (LD)": "Wesley França",
        "Volante (VOL)": "Andrey Santos",
        "Volante Apoio (VOL)": "Bruno Guimarães",
        "Meia-Armador (MEI)": "Rodrygo",
        "Ponta-esquerda (PE)": "Vinicius Junior",
        "Centroavante (CA)": "Endrick",
        "Ponta-direito (PD)": "Estevão"
    }

# ==========================================
# 8. TELA 1: CAMPO DE JOGO (ESCALAÇÃO)
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
        
        tática_ativa = st.selectbox(
            "Esquema Tático (Carlo Ancelotti):",
            ["4-3-3 Clássico", "4-3-3 Diamante", "4-4-2 Clássico", "4-4-2 Diamante"],
            key="tactical_layout_selector"
        )
        
        layout_ativo = TATICAS[tática_ativa]
        
        if "ultima_formacao" not in st.session_state or st.session_state.ultima_formacao != tática_ativa:
            nova_escalacao = {}
            for slot, info in layout_ativo.items():
                pos_validas, atleta_padrao = info[0], info[1]
                atleta_reutilizado = None
                
                if "escalados" in st.session_state:
                    for old_slot, old_player in st.session_state.escalados.items():
                        if old_player in jogadores:
                            pos_do_atleta = jogadores[old_player].get("posicoes_multiplas", [jogadores[old_player]["posicao"]])
                            if any(pos in pos_validas for pos in pos_do_atleta):
                                if old_player not in nova_escalacao.values():
                                    atleta_reutilizado = old_player
                                    break
                            
                nova_escalacao[slot] = atleta_reutilizado if atleta_reutilizado else atleta_padrao
                
            st.session_state.escalados = nova_escalacao
            st.session_state.ultima_formacao = tática_ativa
            st.rerun()

        st.write("Substitua os titulares respeitando a posição de origem do atleta.")
        
        novos_titulares = {}
        for slot, info in layout_ativo.items():
            pos_validas = info[0]
            valid_names = obter_atletas_compativeis(pos_validas)
            
            selecionados_outros = list(novos_titulares.values())
            available_choices = [name for name in valid_names if name not in selecionados_outros]
            
            if not available_choices:
                available_choices = valid_names
            
            default_val = st.session_state.escalados.get(slot, info[1])
            
            if default_val in selecionados_outros:
                if available_choices:
                    default_val = available_choices[0]
                else:
                    default_val = info[1]
            
            if default_val not in available_choices:
                available_choices.append(default_val)
            
            available_choices = sorted(list(set(available_choices)))
            idx = available_choices.index(default_val) if default_val in available_choices else 0
            
            escolha_selecionada = st.selectbox(
                f"{slot}:",
                available_choices,
                index=idx,
                format_func=formatar_jogador_com_posicao,
                key=f"field_{tática_ativa}_{slot}"
            )
            novos_titulares[slot] = escolha_selecionada
            
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
        
        # Renderização do campo de futebol responsivo com bordas dinâmicas
        players_html = ""
        for slot, info in layout_ativo.items():
            pos_validas, left, bottom, pos_tag = info[0], info[2], info[3], info[4]
            player_name = st.session_state.escalados.get(slot, info[1])
            p_data = jogadores.get(player_name, {"nome": player_name, "nota_vini": 0, "nota_roberto": 0})
            
            # --- ALGORITMO DE COR DE BORDA POR PRIORIDADE DE FUNÇÃO ---
            player_multi_pos = p_data.get("posicoes_multiplas", [p_data.get("posicao")])
            
            match_index = -1
            for idx, p_pos in enumerate(player_multi_pos):
                if p_pos in pos_validas:
                    match_index = idx
                    break
            
            # Atribuição estrita de cores (Verde Claro, Amarelo Matte ou Laranja)
            if match_index == 0:
                border_color = "#22c55e"  # Verde Claro (Primária)
            elif match_index == 1:
                border_color = "#eab308"  # Amarelo Matte (Secundária)
            elif match_index >= 2:
                border_color = "#f97316"  # Laranja (Terciária)
            else:
                border_color = "#eab308"  # Fallback seguro
            
            players_html += (
                f'<div class="player-node" style="left:{left};bottom:{bottom};">'
                f'<div class="player-card-pitch" style="border-color: {border_color} !important;">'
                f'<div class="player-pos-tag">{pos_tag}</div>'  # Apenas a tag original da tática!
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
        
        # --- LEGENDA DE ADAPTABILIDADE DINÂMICA ---
        st.markdown("""
        <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-top: -10px; margin-bottom: 25px; background-color: #0b0f19; padding: 12px; border-radius: 10px; border: 1px solid #1e293b;">
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #f8fafc;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: #22c55e; border-radius: 50%;"></span>
                <b>Linha Verde:</b> Função Primária (Posição principal do atleta)
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #f8fafc;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: #eab308; border-radius: 50%;"></span>
                <b>Linha Amarela:</b> Função Secundária (Atleta adaptado no setor)
            </div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #f8fafc;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: #f97316; border-radius: 50%;"></span>
                <b>Linha Laranja:</b> Função Terciária (Opção emergencial de elenco)
            </div>
        </div>
        """, unsafe_allow_html=True)

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
        pos_list = p.get("posicoes_multiplas", [p.get("posicao")])
        abrevs = [ABREVIACOES.get(pos, "OBS") for pos in pos_list]
        abrevs_clean = []
        for a in abrevs:
            if a not in abrevs_clean:
                abrevs_clean.append(a)
        abrev_str = "/".join(abrevs_clean)

        st.markdown(f"""
        <div style="background-color: #111827; padding: 25px; border-radius: 15px; border: 3px solid #eab308; text-align: center;">
            <h2 style="color: #f8fafc; margin-bottom: 5px; font-size: 2.2rem;">{p.get('nome', selected_name)}</h2>
            <span style="background-color: #3b82f6; color: #f8fafc; font-weight: bold; padding: 5px 15px; border-radius: 20px; font-size: 10pt;">
                {p.get('tipo', 'Monitorado')}
            </span>
            <p style="margin-top: 20px; font-size: 11pt; color: #cbd5e1; text-align: left; line-height: 1.8;">
                <b>📍 Posições:</b> {abrev_str}<br>
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
                "Goleiro", "Lateral-direito", "Lateral-esquerdo", 
                "Zagueiro", "Volante", "Mezzala esquerdo", "Mezzala direito", "Meia-armador",
                "Ponta-esquerda", "Ponta-direita", "Centroavante"
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
                        "historico": new_hist,
                        "posicoes_multiplas": [new_pos]
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
# 9. RADAR DO TORCEDOR (FORMULÁRIO TOTALMENTE PRIVADO)
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