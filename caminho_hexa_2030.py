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
    /* Estilização Geral do App (Soft Navy) */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Cabeçalho do App */
    .app-title {
        text-align: center;
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #EAB308 0%, #F8FAFC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .project-subtitle {
        color: #94A3B8;
        font-size: 1.15rem;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    /* O Campo Tático Verde Floresta Responsivo */
    .pitch-container {
        background-color: #14532D; 
        background-image: linear-gradient(to bottom, #14532D 0%, #166534 100%);
        border: 4px solid #EAB308;
        border-radius: 20px;
        position: relative;
        width: 100%;
        height: 680px; 
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
        background-color: rgba(248, 250, 252, 0.3);
    }
    .pitch-circle {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 150px;
        height: 150px;
        border: 2px solid rgba(248, 250, 252, 0.3);
        border-radius: 50%;
    }
    .pitch-penalty-top {
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 100px;
        border-bottom: 2px solid rgba(248, 250, 252, 0.3);
        border-left: 2px solid rgba(248, 250, 252, 0.3);
        border-right: 2px solid rgba(248, 250, 252, 0.3);
    }
    .pitch-penalty-bottom {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 100px;
        border-top: 2px solid rgba(248, 250, 252, 0.3);
        border-left: 2px solid rgba(248, 250, 252, 0.3);
        border-right: 2px solid rgba(248, 250, 252, 0.3);
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
        background: rgba(2, 6, 23, 0.95);
        border: 2px solid #EAB308;
        border-radius: 8px;
        padding: 6px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .player-pos-tag {
        font-size: 7.5pt;
        color: #EAB308;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 1px;
    }
    .player-name-tag {
        font-size: 9pt;
        color: #F8FAFC;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .player-rating-tag {
        background-color: #EAB308;
        color: #020617;
        font-size: 7.5pt;
        font-weight: 800;
        border-radius: 4px;
        padding: 1px 5px;
        margin-top: 3px;
        display: inline-block;
    }
    
    /* Caixas de Informações de Análise */
    .stat-box {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        border-left: 6px solid #EAB308;
        margin-bottom: 18px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* Estilização do Rodapé */
    .fine-print {
        font-size: 8.5pt;
        color: #94A3B8;
        text-align: center;
        margin-top: 40px;
        margin-bottom: 10px;
    }

    /* Sidebar Forçando Cores WCAG */
    section[data-testid="stSidebar"] {
        background-color: #020617 !important;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] h2 {
        color: #EAB308 !important;
        font-weight: 800 !important;
    }

    /* Clean UI Customizations */
    header[data-testid="stHeader"], #MainMenu, footer, .stDeployButton {
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

    # Atualizações de dados estritos de correção
    atualizacoes_obrigatorias = {
        "André": {"posicao": "Mezzala esquerdo", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"]},
        "Matheus Cunha": {"posicao": "Centroavante", "posicoes_multiplas": ["Centroavante", "Segundo atacante", "Meia-armador"]},
        "Wesley França": {"posicao": "Lateral-direito", "posicoes_multiplas": ["Lateral-direito", "Lateral-esquerdo"], "clube": "Roma"},
        "Lucas Beraldo": {"posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro", "Lateral-esquerdo"], "clube": "Paris Saint-Germain"},
        "Andrey Santos": {"posicao": "Volante", "posicoes_multiplas": ["Volante", "Mezzala esquerdo", "Mezzala direito", "Lateral-esquerdo"], "clube": "Chelsea"},
        "Bruno Guimarães": {"posicao": "Mezzala esquerdo", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"], "clube": "Newcastle"},
        "Rodrygo": {"posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita", "Ponta-esquerda", "Meia-armador", "Segundo atacante", "Centroavante"], "clube": "Real Madrid"},
        "Breno Bidon": {"posicao": "Mezzala esquerdo", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante", "Meia-armador"], "clube": "Corinthians"},
        "Gabriel Mec": {"posicao": "Meia-armador", "posicoes_multiplas": ["Meia-armador", "Ponta-esquerda", "Segundo atacante"], "clube": "Grêmio"},
        "Vinicius Junior": {"posicao": "Ponta-esquerda", "posicoes_multiplas": ["Ponta-esquerda", "Segundo atacante", "Centroavante"], "clube": "Real Madrid"},
        "Estevão": {"posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita", "Meia-armador"], "clube": "Palmeiras"},
        "Gabriel Martinelli": {"posicao": "Ponta-esquerda", "posicoes_multiplas": ["Ponta-esquerda", "Meia-armador", "Mezzala esquerdo"], "clube": "Arsenal"}
    }

    for jogador, campos in atualizacoes_obrigatorias.items():
        if jogador in data:
            for campo, valor in campos.items():
                data[jogador][campo] = valor

    # Injeção e Sincronização dos Novos Talentos do Transfermarkt
    novos_atletas = {
        "Vitor Reis": {
            "nome": "Vitor Reis", "nome_completo": "Vitor de Oliveira Nunes dos Reis",
            "posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro"],
            "clube": "Manchester City FC", "idade": 20, "grupo": "Observação", "tipo": "Promessa 2030",
            "nota_vini": 7.5, "nota_roberto": 8.0,
            "pontos_fortes": "Excelente tempo de bola, imposição física na bola aérea e técnica apurada para iniciar transições da defesa.",
            "pontos_fracos": "Requer maior rodagem nos sistemas táticos complexos de alto nível do futebol europeu.",
            "historico": "Visto por Vini como o potencial grande zagueiro do futuro. Promessa real de titularidade para a Copa de 2030.",
            "tm_nascimento": "12/01/2006", "tm_naturalidade": "São José dos Campos, Brasil", "tm_altura": "1,86 m", 
            "tm_pe": "direito", "tm_empresario": "P&P Sport Management", "tm_contrato": "30/06/2029", "tm_equipador": "N/A", "tm_valor_mercado": "30,00 M. €"
        },
        "Danilo": {
            "nome": "Danilo", "nome_completo": "Danilo dos Santos de Oliveira",
            "posicao": "Volante", "posicoes_multiplas": ["Volante", "Mezzala esquerdo", "Mezzala direito", "Meia-armador"],
            "clube": "Botafogo FR", "idade": 25, "grupo": "Reservas", "tipo": "Certeza Atual",
            "nota_vini": 7.5, "nota_roberto": 7.5,
            "pontos_fortes": "Dinamismo impressionante como motor do meio-campo, passes precisos de quebra de linha e boa chegada ao ataque.",
            "pontos_fracos": "Oscilações ocasionais no ritmo defensivo em transições velozes adversárias.",
            "historico": "Roberto destaca sua versatilidade para rodar por todas as posições do setor de criação.",
            "tm_nascimento": "29/04/2001", "tm_naturalidade": "Salvador, Brasil", "tm_altura": "1,77 m", 
            "tm_pe": "esquerdo", "tm_empresario": "Bertolucci Sports", "tm_contrato": "30/06/2029", "tm_equipador": "Nike", "tm_valor_mercado": "32,00 M. €"
        },
        "Gabriel Moscardo": {
            "nome": "Gabriel Moscardo", "nome_completo": "Gabriel Silva Moscardo de Salles",
            "posicao": "Volante", "posicoes_multiplas": ["Volante"],
            "clube": "RCD Espanyol", "idade": 20, "grupo": "Observação", "tipo": "Promessa 2030",
            "nota_vini": 7.0, "nota_roberto": 7.5,
            "pontos_fortes": "Perfil de camisa 5 clássico, interceptações afiadas e excelente frieza no passe sob pressão.",
            "pontos_fracos": "Necessita ganhar mais volume físico (massa muscular) para os duelos diretos do futebol europeu.",
            "historico": "Anotado por Vini como o 'pitbull técnico' que pode assumir a contenção de longo prazo.",
            "tm_nascimento": "28/09/2005", "tm_naturalidade": "Taubaté, Brasil", "tm_altura": "1,85 m", 
            "tm_pe": "direito", "tm_empresario": "SportsMaxi", "tm_contrato": "30/06/2027", "tm_equipador": "adidas", "tm_valor_mercado": "7,00 M. €"
        },
        "Felipe": {
            "nome": "Felipe", "nome_completo": "Felipe de Morais Barbosa Penna dos Santos",
            "posicao": "Meia-armador", "posicoes_multiplas": ["Meia-armador", "Ponta-esquerda", "Ponta-direita"],
            "clube": "Cruzeiro EC Sub-20", "idade": 17, "grupo": "Observação", "tipo": "Observação",
            "nota_vini": 6.5, "nota_roberto": 7.0,
            "pontos_fortes": "Visão de jogo desequilibrante no terço final e condução da bola de altíssima velocidade técnica.",
            "pontos_fracos": "Processo de maturação física recém iniciado, requer paciência no desenvolvimento.",
            "historico": "Uma verdadeira joia oculta rastreada por Roberto para o longo prazo. Driblador nato.",
            "tm_nascimento": "29/08/2008", "tm_naturalidade": "Conselheiro Lafaiete, Brasil", "tm_altura": "1,73 m", 
            "tm_pe": "direito", "tm_empresario": "Talents Sports", "tm_contrato": "31/03/2029", "tm_equipador": "N/A", "tm_valor_mercado": "N/A"
        },
        "Luiz Henrique": {
            "nome": "Luiz Henrique", "nome_completo": "Luiz Henrique André Rosa da Silva",
            "posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita", "Ponta-esquerda", "Centroavante"],
            "clube": "Zenit São Petersburgo", "idade": 25, "grupo": "Observação", "tipo": "Certeza Atual",
            "nota_vini": 7.5, "nota_roberto": 7.5,
            "pontos_fortes": "Imposição física fantástica na ala, condução vertical poderosa e drible desequilibrante.",
            "pontos_fracos": "Fase de adaptação tática e leitura de jogo defensivo sem a bola precisam melhorar.",
            "historico": "Adicionado ao radar como uma excelente alternativa de força física e drible puro para o ataque.",
            "tm_nascimento": "02/01/2001", "tm_naturalidade": "Petrópolis, Brasil", "tm_altura": "1,82 m", 
            "tm_pe": "esquerdo", "tm_empresario": "REASON FOOTBALL...", "tm_contrato": "31/12/2028", "tm_equipador": "adidas", "tm_valor_mercado": "24,00 M. €"
        },
        "Sávio": {
            "nome": "Sávio", "nome_completo": "Sávio Moreira de Oliveira",
            "posicao": "Ponta-esquerda", "posicoes_multiplas": ["Ponta-esquerda", "Ponta-direita", "Meia-armador"],
            "clube": "Manchester City FC", "idade": 22, "grupo": "Reservas", "tipo": "Certeza Atual",
            "nota_vini": 8.0, "nota_roberto": 8.5,
            "pontos_fortes": "Capacidade insana no 1 contra 1, quebras de linha com dribles diagonais e velocidade letal.",
            "pontos_fracos": "Pode pecar no penúltimo passe quando muito cercado próximo à grande área.",
            "historico": "Vini enxerga Sávio como o ponta definitivo para inverter os lados e confundir marcações.",
            "tm_nascimento": "10/04/2004", "tm_naturalidade": "São Mateus, Brasil", "tm_altura": "1,76 m", 
            "tm_pe": "esquerdo", "tm_empresario": "Promanager", "tm_contrato": "30/06/2031", "tm_equipador": "Nike", "tm_valor_mercado": "35,00 M. €"
        },
        "João Pedro": {
            "nome": "João Pedro", "nome_completo": "João Pedro Junqueira de Jesus",
            "posicao": "Centroavante", "posicoes_multiplas": ["Centroavante", "Ponta-esquerda", "Segundo atacante"],
            "clube": "Chelsea FC", "idade": 24, "grupo": "Reservas", "tipo": "Certeza Atual",
            "nota_vini": 8.0, "nota_roberto": 8.0,
            "pontos_fortes": "Atacante extremamente móvel, exímio finalizador, frieza em pênaltis e inteligência associativa.",
            "pontos_fracos": "Sofre contra zagueiros que atuam exclusivamente em bloco baixo apostando no choque físico.",
            "historico": "Unanimidade na comissão como a sombra imediata para assumir a titularidade como camisa 9.",
            "tm_nascimento": "26/09/2001", "tm_naturalidade": "Ribeirão Preto, Brasil", "tm_altura": "1,86 m", 
            "tm_pe": "direito", "tm_empresario": "Promanager", "tm_contrato": "30/06/2033", "tm_equipador": "adidas", "tm_valor_mercado": "80,00 M. €"
        },
        "Kauã Prates": {
            "nome": "Kauã Prates", "nome_completo": "Kauã Prates de Almeida",
            "posicao": "Lateral-esquerdo", "posicoes_multiplas": ["Lateral-esquerdo", "Zagueiro"],
            "clube": "Borussia Dortmund", "idade": 17, "grupo": "Observação", "tipo": "Observação",
            "nota_vini": 7.0, "nota_roberto": 7.0,
            "pontos_fortes": "Excepcional no apoio, estrutura física privilegiada para a lateral e cruzamento venenoso.",
            "pontos_fracos": "Requer ajustes táticos na cobertura de fundo de campo.",
            "historico": "Anotado por Roberto com ressalvas positivas; grande contratação recente do Dortmund.",
            "tm_nascimento": "12/08/2008", "tm_naturalidade": "Montanha, Brasil", "tm_altura": "1,84 m", 
            "tm_pe": "esquerdo", "tm_empresario": "Trust Football", "tm_contrato": "31/12/2027", "tm_equipador": "adidas", "tm_valor_mercado": "10,00 M. €"
        },
        "Viery": {
            "nome": "Viery", "nome_completo": "Viery Fernandes Santos Lopes",
            "posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro", "Lateral-esquerdo"],
            "clube": "ACF Fiorentina", "idade": 21, "grupo": "Observação", "tipo": "Promessa 2030",
            "nota_vini": 7.0, "nota_roberto": 7.0,
            "pontos_fortes": "Zagueiro canhoto construtor com excelente visão de jogo para viradas de bola.",
            "pontos_fracos": "Experiência limitante no atual estágio competitivo das principais ligas.",
            "historico": "Atleta canhoto raro na zaga; monitorado de perto como possível curinga da defesa.",
            "tm_nascimento": "02/01/2005", "tm_naturalidade": "Ubá, Brasil", "tm_altura": "1,87 m", 
            "tm_pe": "esquerdo", "tm_empresario": "Prattes Group", "tm_contrato": "30/06/2031", "tm_equipador": "N/A", "tm_valor_mercado": "6,00 M. €"
        },
        "Alexsandro": {
            "nome": "Alexsandro", "nome_completo": "Alexsandro Victor de Souza Ribeiro",
            "posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro"],
            "clube": "LOSC Lille", "idade": 26, "grupo": "Observação", "tipo": "Certeza Atual",
            "nota_vini": 7.5, "nota_roberto": 7.5,
            "pontos_fortes": "Forte no jogo aéreo defensivo (1,91 m), desarme agressivo e poder de intimidação física.",
            "pontos_fracos": "Pode sofrer com a falta de agilidade no giro corporal contra atacantes de baixa estatura.",
            "historico": "Nome sólido consolidado na Ligue 1. Bom xerife para convocações emergenciais e de estabilidade.",
            "tm_nascimento": "09/08/1999", "tm_naturalidade": "Rio de Janeiro, Brasil", "tm_altura": "1,91 m", 
            "tm_pe": "ambos", "tm_empresario": "Roc Nation Sports", "tm_contrato": "30/06/2028", "tm_equipador": "N/A", "tm_valor_mercado": "15,00 M. €"
        }
    }

    for nome, dados in novos_atletas.items():
        if nome not in data:
            data[nome] = dados
        else:
            # Garante que as correções vitais não sejam sobrescritas em atualizações posteriores
            for k, v in dados.items():
                if k.startswith('tm_') or k == "nome_completo" or k == "clube":
                    data[nome][k] = v

    # Faxina Final de Padronização WCAG/Arquitetura
    pos_map_limpeza = {
        "Lateral Esquerdo": "Lateral-esquerdo",
        "Lateral Direito": "Lateral-direito",
        "Zagueiro Esquerdo": "Zagueiro",
        "Zagueiro Direito": "Zagueiro",
        "Meio-Campo (Defensivo)": "Volante",
        "Meio-Campo (Apoio)": "Mezzala esquerdo",
        "Meio-Campo (Criativo)": "Meia-armador",
        "Ponta Esquerda": "Ponta-esquerda",
        "Ponta Direita": "Ponta-direita"
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
        "Alisson": {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool", "idade": 33, "grupo": "Titulares", "tipo": "Certeza Atual", "nota_vini": 7.0, "nota_roberto": 7.5, "posicoes_multiplas": ["Goleiro"]}
    }
    
    if not os.path.exists(DATA_FILE):
        salvar_jogadores(contingencia)
        return contingencia
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data = normalizar_banco_dados(data)
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
                        colunas = linha.find_all("td")
                        if len(colunas) >= 5:
                            pos_crua = colunas[0].text.strip()
                            posicao = "".join(filter(str.isdigit, pos_crua))
                            nome_clube = " ".join(colunas[1].text.strip().split())
                            nome_chave = nome_clube.lower()
                            
                            dados_cbf[nome_chave] = {
                                "posicao": f"{posicao}º",
                                "pts": colunas[2].text.strip(),
                                "jogos": colunas[3].text.strip(),
                                "vitorias": colunas[4].text.strip(),
                                "serie": serie
                            }
        except Exception:
            pass
    return dados_cbf

tabela_ao_vivo_cbf = buscar_classificacao_cbf()

TABELA_BACKUP_CBF = {
    "palmeiras": {"posicao": "1º", "pts": "41", "jogos": "19", "vitorias": "12", "serie": "Série A"},
    "flamengo": {"posicao": "2º", "pts": "35", "jogos": "18", "vitorias": "10", "serie": "Série A"},
    "botafogo": {"posicao": "4º", "pts": "31", "jogos": "19", "vitorias": "9", "serie": "Série A"}
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
        "Segundo Atacante (SA)": (["Segundo atacante", "Ponta-esquerda", "Ponta-direita", "Meia-armador"], "Rodrygo", "35%", "82%", "SA"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "65%", "82%", "CA")
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
    abrevs_clean = list(dict.fromkeys(abrevs)) # Remove duplicidades mantendo ordem
    abrev_str = "/".join(abrevs_clean)
    return f"{nome} ({abrev_str})"

# ==========================================
# 7. MENU LATERAL & NAVEGAÇÃO UNIVERSAL
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #EAB308; margin-top:15px;'>CONSELHO TÁTICO</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação do Painel:",
    ["🏟️ Campo de Jogo (Escalação)", "👤 Perfis dos Jogadores & Scout", "📋 Gestão do Roster", "📊 Análise de Opiniões"]
)

# Inicialização padrão dos dados de sessão
if "escalados" not in st.session_state:
    st.session_state.escalados = {
        "Goleiro (GOL)": "Alisson", "Lateral-esquerdo (LE)": "Kaiki Bruno",
        "Zagueiro Esquerdo (ZAG)": "Gabriel Magalhães", "Zagueiro Direito (ZAG)": "Lucas Beraldo",
        "Lateral-direito (LD)": "Wesley França", "Volante (VOL)": "Andrey Santos",
        "Volante Apoio (VOL)": "Bruno Guimarães", "Meia-Armador (MEI)": "Rodrygo",
        "Ponta-esquerda (PE)": "Vinicius Junior", "Centroavante (CA)": "Endrick",
        "Ponta-direita (PD)": "Estevão"
    }

# ==========================================
# 8. TELA 1: CAMPO DE JOGO (ESCALAÇÃO)
# ==========================================
if menu == "🏟️ Campo de Jogo (Escalação)":
    st.markdown("<h1 class='app-title'>🏆 O Caminho para o Hexa</h1>", unsafe_allow_html=True)
    st.markdown(
        """<p class="project-subtitle" style="text-align: center;">Painel tático interativo desenvolvido para organizar escalações, avaliar pontuações de scout e planejar o percurso de renovação da nossa seleção canarinho rumo ao mundial de 2030.</p>""", 
        unsafe_allow_html=True
    )
    
    col_config, col_campo = st.columns([1, 2])
    
    with col_config:
        st.markdown("### 📋 Calibrar Escalação")
        tática_ativa = st.selectbox("Esquema Tático (Carlo Ancelotti):", list(TATICAS.keys()), key="tactical_layout_selector")
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
                            if any(pos in pos_validas for pos in pos_do_atleta) and old_player not in nova_escalacao.values():
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
            if not available_choices: available_choices = valid_names
            
            default_val = st.session_state.escalados.get(slot, info[1])
            if default_val in selecionados_outros: default_val = available_choices[0] if available_choices else info[1]
            if default_val not in available_choices: available_choices.append(default_val)
            
            available_choices = sorted(list(set(available_choices)))
            idx = available_choices.index(default_val) if default_val in available_choices else 0
            
            escolha_selecionada = st.selectbox(f"{slot}:", available_choices, index=idx, format_func=formatar_jogador_com_posicao, key=f"field_{tática_ativa}_{slot}")
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
        
        players_html = ""
        for slot, info in layout_ativo.items():
            pos_validas, left, bottom, pos_tag = info[0], info[2], info[3], info[4]
            player_name = st.session_state.escalados.get(slot, info[1])
            p_data = jogadores.get(player_name, {"nome": player_name, "nota_vini": 0, "nota_roberto": 0})
            
            player_multi_pos = p_data.get("posicoes_multiplas", [p_data.get("posicao")])
            match_index = -1
            for idx, p_pos in enumerate(player_multi_pos):
                if p_pos in pos_validas:
                    match_index = idx
                    break
            
            border_color = "#22C55E" if match_index == 0 else "#EAB308" if match_index == 1 else "#F97316"
            
            players_html += (
                f'<div class="player-node" style="left:{left};bottom:{bottom};">'
                f'<div class="player-card-pitch" style="border-color: {border_color} !important;">'
                f'<div class="player-pos-tag">{pos_tag}</div>'
                f'<div class="player-name-tag">{p_data["nome"]}</div>'
                f'<div class="player-rating-tag">★ {p_data.get("nota_vini", 0):.1f} / {p_data.get("nota_roberto", 0):.1f}</div>'
                f'</div></div>'
            )
        
        pitch_html = f'<div class="pitch-container"><div class="pitch-line-center"></div><div class="pitch-circle"></div><div class="pitch-penalty-top"></div><div class="pitch-penalty-bottom"></div>{players_html}</div>'
        st.markdown(pitch_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-top: -10px; margin-bottom: 25px; background-color: #020617; padding: 12px; border-radius: 10px; border: 1px solid #1E293B;">
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #F8FAFC;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #22C55E; border-radius: 50%;"></span><b>Linha Verde:</b> Função Primária (Posição principal do atleta)</div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #F8FAFC;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #EAB308; border-radius: 50%;"></span><b>Linha Amarela:</b> Função Secundária (Atleta adaptado no setor)</div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #F8FAFC;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #F97316; border-radius: 50%;"></span><b>Linha Laranja:</b> Função Terciária (Opção emergencial)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        
        # INTERATIVIDADE UX: Exportar e Compartilhar
        col_export, col_share1, col_share2 = st.columns([1, 1, 1])
        
        with col_export:
            export_data = json.dumps(st.session_state.escalados, indent=4, ensure_ascii=False)
            st.download_button(
                label="📥 Baixar Escalação (JSON)",
                data=export_data,
                file_name=f"tática_{tática_ativa.replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True
            )
            
        escalados_nomes = list(st.session_state.escalados.values())
        mensagem_share = f"Montei minha Seleção Brasileira no esquema {tática_ativa} do app 'O Caminho para o Hexa'! 🏆\\n\\nMeu Time: {', '.join(escalados_nomes[:5])} e mais!\\n\\nMonte a sua também no Streamlit!"
        texto_codificado = urllib.parse.quote(mensagem_share)
        
        with col_share1:
            st.markdown(f"""<a href="https://api.whatsapp.com/send?text={texto_codificado}" target="_blank" style="text-decoration:none;"><div style="background-color:#166534; color:#F8FAFC; text-align:center; padding:9px; border-radius:8px; font-weight:bold; border: 1px solid #EAB308; cursor:pointer;">🟢 WhatsApp</div></a>""", unsafe_allow_html=True)
        with col_share2:
            st.markdown(f"""<a href="https://twitter.com/intent/tweet?text={texto_codificado}" target="_blank" style="text-decoration:none;"><div style="background-color:#1E293B; color:#F8FAFC; text-align:center; padding:9px; border-radius:8px; font-weight:bold; border: 1px solid #EAB308; cursor:pointer;">🔵 X / Threads</div></a>""", unsafe_allow_html=True)

# ==========================================
# TELA 2: PERFIS DOS JOGADORES & SCOUT
# ==========================================
elif menu == "👤 Perfis dos Jogadores & Scout":
    st.title("👤 Ficha Individual do Atleta")
    st.markdown("<p style='font-size:1.15rem; color:#94A3B8;'>Consulte os dados individuais e interaja com o scout dos nossos convocados</p>", unsafe_allow_html=True)
    
    selected_name = st.selectbox("Escolha o Atleta:", sorted(list(jogadores.keys())))
    p = jogadores[selected_name]
    
    st.markdown("---")
    
    col_p, col_d = st.columns([1, 2])
    
    with col_p:
        pos_list = p.get("posicoes_multiplas", [p.get("posicao")])
        abrevs = [ABREVIACOES.get(pos, "OBS") for pos in pos_list]
        abrev_str = "/".join(list(dict.fromkeys(abrevs)))

        st.markdown(f"""
        <div style="background-color: #020617; padding: 25px; border-radius: 15px; border: 3px solid #EAB308; text-align: center;">
            <h2 style="color: #F8FAFC; margin-bottom: 5px; font-size: 2.2rem;">{p.get('nome', selected_name)}</h2>
            <span style="background-color: #1E293B; color: #EAB308; border: 1px solid #EAB308; font-weight: bold; padding: 5px 15px; border-radius: 20px; font-size: 10pt;">
                {p.get('tipo', 'Monitorado')}
            </span>
            <p style="margin-top: 20px; font-size: 11pt; color: #CBD5E1; text-align: left; line-height: 1.8;">
                <b>📍 Posições:</b> {abrev_str}<br>
                <b>🏢 Clube Atual:</b> {p.get('clube', 'N/A')}<br>
                <b>📅 Idade em 2026:</b> {p.get('idade', 22)} anos<br>
                <b>🏆 Idade em 2030:</b> <span style="color:#EAB308; font-weight:bold;">{p.get('idade', 22) + 4} anos</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # INTERATIVIDADE UX: Sliders Dinâmicos para Calibrar Notas de Scout
        st.subheader("Avaliação Tática Interativa")
        st.write("Ajuste os valores para atualizar o JSON em tempo real:")
        
        new_vini = st.slider("Nota do Vini", 0.0, 10.0, float(p.get('nota_vini', 0.0)), 0.1, key=f"sl_vini_{selected_name}")
        new_rob = st.slider("Nota do Roberto", 0.0, 10.0, float(p.get('nota_roberto', 0.0)), 0.1, key=f"sl_rob_{selected_name}")
        
        if new_vini != p.get('nota_vini') or new_rob != p.get('nota_roberto'):
            jogadores[selected_name]['nota_vini'] = new_vini
            jogadores[selected_name]['nota_roberto'] = new_rob
            salvar_jogadores(jogadores)
            st.success("✅ Notas atualizadas no banco de dados!")

    with col_d:
        dados_live = obter_dados_reais_clube(p.get('clube', ''))
        
        if p.get("tm_altura") or p.get("tm_contrato") or p.get("tm_valor_mercado"):
            st.markdown("### 📊 Dados Biométricos & Contratuais (Transfermarkt)")
            st.markdown(f"""
            <div style="background-color: #020617; padding: 18px; border-radius: 12px; border-left: 5px solid #EAB308; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <p style="color: #CBD5E1; font-size: 10.5pt; line-height: 1.8; margin: 0;">
                    <b style="color: #F8FAFC;">Nome Completo:</b> {p.get('nome_completo', p.get('nome'))}<br>
                    <b style="color: #F8FAFC;">Nascimento:</b> {p.get('tm_nascimento', 'N/A')} | <b style="color: #F8FAFC;">Naturalidade:</b> {p.get('tm_naturalidade', 'N/A')}<br>
                    <b style="color: #F8FAFC;">Altura:</b> {p.get('tm_altura', 'N/A')} | <b style="color: #F8FAFC;">Pé Preferencial:</b> {p.get('tm_pe', 'N/A')}<br>
                    <b style="color: #F8FAFC;">Agente:</b> {p.get('tm_empresario', 'N/A')} | <b style="color: #F8FAFC;">Fim do Contrato:</b> {p.get('tm_contrato', 'N/A')}<br>
                    <b style="color: #F8FAFC;">Valor de Mercado Atual:</b> <span style="color: #EAB308; font-weight: 800; font-size: 11.5pt;">{p.get('tm_valor_mercado', 'N/A')}</span><br>
                    <b style="color: #F8FAFC;">Patrocínio Desportivo:</b> {p.get('tm_equipador', 'N/A')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("### 📈 Estatísticas do Clube")
        
        if dados_live:
            cbf_df = pd.DataFrame([{
                "Clube": p.get('clube', 'N/A'), "Divisão": dados_live.get('serie', 'N/A'),
                "Posição": dados_live.get('posicao', 'N/A'), "Pontos": dados_live.get('pts', 'N/A'),
                "Jogos": dados_live.get('jogos', 'N/A'), "Vitórias": dados_live.get('vitorias', 'N/A')
            }])
            st.dataframe(cbf_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"ℹ️ Atleta atuando no {p.get('clube', 'N/A')}. Ligas do exterior monitoradas em background.")
            
        st.markdown("### 📝 Dossiê Histórico de Discussões")
        
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown("**🟢 Pontos Fortes:**")
        st.write(p.get("pontos_fortes", "Nenhuma informação cadastrada."))
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stat-box" style="border-left-color: #EF4444;">', unsafe_allow_html=True)
        st.markdown("**🔴 Desafios & Pontos Fracos:**")
        st.write(p.get("pontos_fracos", "Nenhuma informação cadastrada."))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stat-box" style="border-left-color: #3B82F6;">', unsafe_allow_html=True)
        st.markdown("**🗣️ Notas das Discussões (Vini & Roberto):**")
        st.write(p.get("historico", "Nenhuma anotação disponível."))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p class='fine-print'>*Dados mesclados de fontes oficiais (CBF, FIFA, Transfermarkt).</p>", unsafe_allow_html=True)

# ==========================================
# TELA 3: GESTÃO DO ROSTER
# ==========================================
elif menu == "📋 Gestão do Roster":
    st.title("📋 Gerenciador do Banco de Dados")
    
    tab_list, tab_add = st.tabs(["Jogadores Inscritos", "➕ Inscrever Nova Joia"])
    
    with tab_list:
        df_players = pd.DataFrame([{
            "Nome": k, "Posição": v.get("posicao", "N/A"), "Clube": v.get("clube", "N/A"),
            "Idade 2026": v.get("idade", 22), "Idade 2030": v.get("idade", 22) + 4,
            "Valor M.": v.get("tm_valor_mercado", "N/A"), "Vini": v.get("nota_vini", 0.0),
            "Roberto": v.get("nota_roberto", 0.0)
        } for k, v in jogadores.items()])
        st.dataframe(df_players, use_container_width=True)
        
        st.markdown("### 🗑️ Cortar Atleta")
        remover_nome = st.selectbox("Selecione quem quer cortar:", list(jogadores.keys()))
        if st.button("Confirmar Corte Permanente") and remover_nome in jogadores:
            del jogadores[remover_nome]
            salvar_jogadores(jogadores)
            st.success(f"{remover_nome} foi cortado com sucesso!")
            st.rerun()

    with tab_add:
        with st.form("add_player_form"):
            new_nome = st.text_input("Nome Curto (Ex: Neymar)*")
            new_full = st.text_input("Nome Completo")
            new_pos = st.selectbox("Posição Principal*", list(ABREVIACOES.keys()))
            new_clube = st.text_input("Clube Atual")
            new_idade = st.number_input("Idade em 2026", min_value=15, max_value=45, value=22)
            new_grupo = st.selectbox("Grupo Hierárquico*", ["Titulares", "Reservas", "Observação"])
            
            if st.form_submit_button("Inscrever Jogador") and new_nome:
                jogadores[new_nome] = {
                    "nome": new_nome, "nome_completo": new_full, "posicao": new_pos,
                    "clube": new_clube, "idade": int(new_idade), "grupo": new_grupo,
                    "posicoes_multiplas": [new_pos]
                }
                salvar_jogadores(jogadores)
                st.success("Atleta inscrito!")
                st.rerun()

# ==========================================
# TELA 4: ANÁLISE DE OPINIÕES
# ==========================================
elif menu == "📊 Análise de Opiniões":
    st.title("📊 Análise Coletiva de Scout")
    st.write("Divergências e consensos entre a comissão técnica para o mundial de 2030.")

    df_stats = pd.DataFrame([{
        "Nome": k, "Posição": v.get("posicao", "N/A"),
        "Vini": v.get("nota_vini", 0.0), "Roberto": v.get("nota_roberto", 0.0),
        "Diferença": abs(v.get("nota_vini", 0.0) - v.get("nota_roberto", 0.0))
    } for k, v in jogadores.items()])

    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.markdown("### 🤝 Consenso Absoluto")
        st.write("Nomes em sintonia técnica:")
        st.dataframe(df_stats.sort_values(by="Diferença", ascending=True).head(5)[["Nome", "Posição", "Vini", "Roberto"]], use_container_width=True, hide_index=True)

    with col_s2:
        st.markdown("### 🔥 Debates Acalorados")
        st.write("Maiores divergências de avaliação:")
        st.dataframe(df_stats.sort_values(by="Diferença", ascending=False).head(5)[["Nome", "Vini", "Roberto", "Diferença"]], use_container_width=True, hide_index=True)

# ==========================================
# 9. RADAR DO TORCEDOR (SIDEBAR PRIVADA)
# ==========================================
st.sidebar.markdown("---")
with st.sidebar.form("form_sugestao", clear_on_submit=True):
    tipo_sugestao = st.selectbox("Contato Rápido:", ["Indicar Atleta", "Sugerir Melhoria"])
    detalhes_sugestao = st.text_area("Mensagem:")
    if st.form_submit_button("Enviar (E-mail)"):
        mailto_url = f"mailto:viniciusbl87@gmail.com?subject=Radar Hexa2030&body={urllib.parse.quote(detalhes_sugestao)}"
        st.sidebar.markdown(f'<a href="{mailto_url}" target="_blank" style="background-color:#EAB308;color:#0F172A;font-weight:bold;padding:10px;border-radius:8px;text-align:center;display:block;text-decoration:none;">🚀 Confirmar Envio</a>', unsafe_allow_html=True)