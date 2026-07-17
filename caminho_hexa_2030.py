import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
import requests
import re
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
# 3. DICIONÁRIOS E FUNÇÕES DE LIMPEZA MATEMÁTICA
# ==========================================
ABREVIACOES = {
    "Goleiro": "GOL", "Lateral-esquerdo": "LE", "Zagueiro": "ZAG", "Lateral-direito": "LD",
    "Volante": "VOL", "Mezzala esquerdo": "MCE", "Mezzala direito": "MCD", "Meia-armador": "MEI",
    "Ponta-esquerda": "PE", "Ponta-direita": "PD", "Segundo atacante": "SA", "Centroavante": "CA"
}

def extrair_numero(valor_texto, padrao=0.0):
    """
    Extrai o valor numérico. Converte 'mil' para a escala de milhões (M).
    Ex: '175 mil €' -> 0.175 M | '20,00 M. €' -> 20.0 M
    """
    if not valor_texto or valor_texto == "N/A":
        return padrao
    texto_min = str(valor_texto).lower()
    numeros = re.findall(r'[0-9]+(?:[.,][0-9]+)?', texto_min)
    if numeros:
        try:
            valor = float(numeros[0].replace(',', '.'))
            if 'mil' in texto_min:
                valor = valor / 1000.0
            return valor
        except:
            return padrao
    return padrao

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

    # Atualizações estritas (Rodrygo, Martinelli e bases táticas da comissão)
    atualizacoes_obrigatorias = {
        "Yan Couto": {"posicao": "Lateral-direito", "posicoes_multiplas": ["Lateral-direito", "Mezzala direito"], "clube": "Borussia Dortmund", "tm_nascimento": "03/06/2002", "tm_naturalidade": "Curitiba, Brasil", "tm_altura": "1,68 m", "tm_pe": "direito", "tm_empresario": "CAA Stellar", "tm_contrato": "30/06/2030", "tm_valor_mercado": "17,00 M. €"},
        "Andrey Santos": {"posicao": "Volante", "posicoes_multiplas": ["Volante", "Mezzala esquerdo", "Mezzala direito", "Lateral-esquerdo"], "clube": "Manchester United FC", "tm_nascimento": "03/05/2004", "tm_naturalidade": "Rio de Janeiro, Brasil", "tm_altura": "1,80 m", "tm_pe": "direito", "tm_empresario": "Bertolucci Sports", "tm_contrato": "30/06/2031", "tm_equipador": "adidas", "tm_valor_mercado": "40,00 M. €"},
        "Estevão": {"posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita", "Meia-armador"], "clube": "Chelsea FC", "tm_nascimento": "24/04/2007", "tm_naturalidade": "Franca, Brasil", "tm_altura": "1,78 m", "tm_pe": "esquerdo", "tm_empresario": "LINK SPORTS", "tm_contrato": "30/06/2033", "tm_equipador": "Nike", "tm_valor_mercado": "80,00 M. €"},
        "Vinicius Junior": {"posicao": "Ponta-esquerda", "posicoes_multiplas": ["Ponta-esquerda", "Segundo atacante", "Centroavante"], "clube": "Real Madrid CF", "tm_nascimento": "12/07/2000", "tm_naturalidade": "São Gonçalo, Brasil", "tm_altura": "1,76 m", "tm_pe": "direito", "tm_empresario": "Roc Nation Sports", "tm_contrato": "30/06/2027", "tm_equipador": "Nike", "tm_valor_mercado": "140,00 M. €"},
        "Endrick": {"posicao": "Centroavante", "posicoes_multiplas": ["Centroavante", "Segundo atacante", "Ponta-direita"], "clube": "Real Madrid CF", "tm_nascimento": "21/07/2006", "tm_naturalidade": "Taguatinga, Brasil", "tm_altura": "1,72 m", "tm_pe": "esquerdo", "tm_empresario": "Roc Nation Sports", "tm_contrato": "30/06/2030", "tm_equipador": "New Balance", "tm_valor_mercado": "40,00 M. €"},
        "Gabriel Magalhães": {"posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro"], "clube": "FC Arsenal", "tm_nascimento": "19/12/1997", "tm_naturalidade": "São Paulo, Brasil", "tm_altura": "1,90 m", "tm_pe": "esquerdo", "tm_empresario": "Bertolucci Sports", "tm_contrato": "30/06/2029", "tm_equipador": "N/A", "tm_valor_mercado": "75,00 M. €"},
        "Rodrygo": {"posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita", "Ponta-esquerda", "Meia-armador", "Segundo atacante", "Centroavante"], "clube": "Real Madrid CF", "tm_nascimento": "09/01/2001", "tm_naturalidade": "Osasco, Brasil", "tm_altura": "1,74 m", "tm_pe": "direito", "tm_empresario": "Familiar", "tm_contrato": "30/06/2028", "tm_equipador": "adidas", "tm_valor_mercado": "45,00 M. €"},
        "Gabriel Martinelli": {"posicao": "Ponta-esquerda", "posicoes_multiplas": ["Ponta-esquerda", "Meia-armador", "Mezzala esquerdo"], "clube": "FC Arsenal", "tm_nascimento": "18/06/2001", "tm_naturalidade": "Guarulhos, Brasil", "tm_altura": "1,78 m", "tm_pe": "direito", "tm_empresario": "Roc Nation Sports", "tm_contrato": "30/06/2027", "tm_equipador": "adidas", "tm_valor_mercado": "45,00 M. €"},
        "Wesley França": {"posicao": "Lateral-direito", "posicoes_multiplas": ["Lateral-direito", "Lateral-esquerdo"], "clube": "AS Roma", "tm_nascimento": "06/09/2003", "tm_naturalidade": "Açailândia, Brasil", "tm_altura": "1,78 m", "tm_pe": "direito", "tm_empresario": "MCL Agency", "tm_contrato": "30/06/2030", "tm_equipador": "Nike", "tm_valor_mercado": "40,00 M. €"},
        "André": {"posicao": "Mezzala esquerdo", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"]},
        "Matheus Cunha": {"posicao": "Centroavante", "posicoes_multiplas": ["Centroavante", "Segundo atacante", "Meia-armador"]},
        "Lucas Beraldo": {"posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro", "Lateral-esquerdo"]},
        "Bruno Guimarães": {"posicao": "Mezzala esquerdo", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"]},
        "Breno Bidon": {"posicao": "Mezzala esquerdo", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante", "Meia-armador"]},
        "Gabriel Mec": {"posicao": "Meia-armador", "posicoes_multiplas": ["Meia-armador", "Ponta-esquerda", "Segundo atacante"]}
    }

    for jogador, campos in atualizacoes_obrigatorias.items():
        if jogador in data:
            for campo, valor in campos.items():
                data[jogador][campo] = valor

    # Dicionário com todas as novas joias mapeadas do Transfermarkt
    novos_atletas = {
        "Allan": {
            "nome": "Allan", "nome_completo": "Allan Andrade Elias", "posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita", "Meia-armador", "Mezzala direito"],
            "clube": "SE Palmeiras", "idade": 22, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.0, "nota_roberto": 7.5,
            "pontos_fortes": "Dinâmica veloz na ponta e grande controle de bola colada no pé.", "pontos_fracos": "Oscilações de rendimento contra defesas de forte contato físico.", "historico": "Excelente promessa com margem para crescimento na ala ofensiva.",
            "tm_nascimento": "19/04/2004", "tm_naturalidade": "Florianópolis, Brasil", "tm_altura": "1,74 m", "tm_pe": "esquerdo", "tm_empresario": "Talents Sports", "tm_contrato": "31/12/2029", "tm_equipador": "N/A", "tm_valor_mercado": "20,00 M. €"
        },
        "Diego Callai": {
            "nome": "Diego Callai", "nome_completo": "Diego Callai Silva", "posicao": "Goleiro", "posicoes_multiplas": ["Goleiro"],
            "clube": "Sporting CP B", "idade": 22, "grupo": "Observação", "tipo": "Observação", "nota_vini": 6.5, "nota_roberto": 6.5,
            "pontos_fortes": "Boa envergadura e vivência tática na escola portuguesa de goleiros.", "pontos_fracos": "Necessita de vitrine em ligas primárias para ser testado no alto nível.", "historico": "Guarda-redes monitorado por atuar na escola europeia.",
            "tm_nascimento": "18/07/2004", "tm_naturalidade": "Caxias do Sul, Brasil", "tm_altura": "1,92 m", "tm_pe": "direito", "tm_empresario": "AS1", "tm_contrato": "30/06/2030", "tm_equipador": "N/A", "tm_valor_mercado": "1,50 M. €"
        },
        "Luis Gustavo": {
            "nome": "Luis Gustavo", "nome_completo": "Luis Gustavo Roncholeta Benedetti", "posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro"],
            "clube": "SE Palmeiras", "idade": 20, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.0, "nota_roberto": 7.0,
            "pontos_fortes": "Estatura raríssima e imponente (1,97 m) garantindo domínio aéreo total.", "pontos_fracos": "Fase inicial de adaptação no nível de exigência do time principal.", "historico": "Zagueiro canhoto gigante, aposta de altíssimo teto.",
            "tm_nascimento": "07/06/2006", "tm_naturalidade": "Bauru, Brasil", "tm_altura": "1,97 m", "tm_pe": "esquerdo", "tm_empresario": "Bertolucci Sports", "tm_contrato": "31/12/2029", "tm_equipador": "N/A", "tm_valor_mercado": "4,00 M. €"
        },
        "Guilherme Garutti": {
            "nome": "Guilherme Garutti", "nome_completo": "Guilherme Gomes Garutti", "posicao": "Zagueiro", "posicoes_multiplas": ["Zagueiro"],
            "clube": "ACSC FC Arges", "idade": 32, "grupo": "Observação", "tipo": "Certeza Atual", "nota_vini": 6.0, "nota_roberto": 6.5,
            "pontos_fortes": "Boa altura e rodagem internacional, trazendo segurança física e tática.", "pontos_fracos": "Idade avançada (36 na Copa 2030) diminui apelo para o ciclo longo.", "historico": "Anotado para conhecimento geral de peças rodando no leste europeu.",
            "tm_nascimento": "08/03/1994", "tm_naturalidade": "N/A, Brasil", "tm_altura": "1,94 m", "tm_pe": "direito", "tm_empresario": "FGA", "tm_contrato": "N/A", "tm_equipador": "N/A", "tm_valor_mercado": "175 mil €"
        },
        "Luis Felipe": {
            "nome": "Luis Felipe", "nome_completo": "Luis Felipe Pacheco da Costa", "posicao": "Volante", "posicoes_multiplas": ["Volante", "Mezzala direito", "Mezzala esquerdo"],
            "clube": "SE Palmeiras Sub-20", "idade": 18, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 6.5, "nota_roberto": 7.0,
            "pontos_fortes": "Dinamismo na marcação, bom controle de espaço e versatilidade na meia cancha.", "pontos_fracos": "Ainda em processo de maturação nas categorias de base.", "historico": "Peça a ser observada no desenvolvimento da base.",
            "tm_nascimento": "02/02/2008", "tm_naturalidade": "Lajeado, Brasil", "tm_altura": "1,80 m", "tm_pe": "direito", "tm_empresario": "GlobalSportsLtda", "tm_contrato": "31/12/2029", "tm_equipador": "adidas", "tm_valor_mercado": "500 mil €"
        },
        "Jhuan": {
            "nome": "Jhuan", "nome_completo": "Jhuan Nunes Coelho", "posicao": "Ponta-direita", "posicoes_multiplas": ["Ponta-direita"],
            "clube": "RB Bragantino Sub-20", "idade": 19, "grupo": "Observação", "tipo": "Observação", "nota_vini": 6.0, "nota_roberto": 6.5,
            "pontos_fortes": "Arrancada forte e agressividade nas ações pelo flanco ofensivo.", "pontos_fracos": "Necessita refinar a tomada de decisão no último terço do campo.", "historico": "Monitorado como projeto futuro na base do Bragantino.",
            "tm_nascimento": "03/06/2007", "tm_naturalidade": "N/A, Brasil", "tm_altura": "N/A", "tm_pe": "esquerdo", "tm_empresario": "Roc Nation Sports", "tm_contrato": "N/A", "tm_equipador": "N/A", "tm_valor_mercado": "N/A"
        },
        "Carlos Miguel": {
            "nome": "Carlos Miguel", "nome_completo": "Carlos Miguel dos Santos Pereira", "posicao": "Goleiro", "posicoes_multiplas": ["Goleiro"],
            "clube": "SE Palmeiras", "idade": 27, "grupo": "Observação", "tipo": "Certeza Atual", "nota_vini": 7.0, "nota_roberto": 7.0,
            "pontos_fortes": "Estatura monumental (2,04m), excelente envergadura e bom reflexo sob as traves.", "pontos_fracos": "Tempo de reação rasteiro devido à sua alta estatura.", "historico": "Ótima opção de segurança no gol com presença física imponente.",
            "tm_nascimento": "09/10/1998", "tm_naturalidade": "Rio das Ostras, Brasil", "tm_altura": "2,04 m", "tm_pe": "esquerdo", "tm_empresario": "Bertolucci Sports", "tm_contrato": "31/07/2030", "tm_equipador": "Nike", "tm_valor_mercado": "7,00 M. €"
        },
        "Leonardo Nannetti": {
            "nome": "Leonardo Nannetti", "nome_completo": "Leonardo Nannetti Lopes", "posicao": "Goleiro", "posicoes_multiplas": ["Goleiro"],
            "clube": "CR Flamengo Sub-20", "idade": 18, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 6.5, "nota_roberto": 7.0,
            "pontos_fortes": "Altíssimo potencial, excelente base formativa rubro-negra e perfil europeu.", "pontos_fracos": "Ainda em processo final de transição para o profissional de elite.", "historico": "Goleiro com dupla nacionalidade, requer monitoramento do nosso scout antes de ser assediado.",
            "tm_nascimento": "21/08/2007", "tm_naturalidade": "Rio de Janeiro, Brasil", "tm_altura": "1,96 m", "tm_pe": "esquerdo", "tm_empresario": "SportsMaxi", "tm_contrato": "31/12/2029", "tm_equipador": "N/A", "tm_valor_mercado": "N/A"
        },
        "Hugo Souza": {
            "nome": "Hugo Souza", "nome_completo": "Hugo de Souza Nogueira", "posicao": "Goleiro", "posicoes_multiplas": ["Goleiro"],
            "clube": "SC Corinthians", "idade": 27, "grupo": "Reservas", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 7.5,
            "pontos_fortes": "Envergadura formidável (1,99m), agilidade felina sob as traves e recuperação mental após retorno ao Brasil.", "pontos_fracos": "Jogo com os pés em pressão alta exige refino tático.", "historico": "Recuperou a confiança técnica e exibe totais condições de disputar posição no ciclo.",
            "tm_nascimento": "31/01/1999", "tm_naturalidade": "Duque de Caxias, Brasil", "tm_altura": "1,99 m", "tm_pe": "direito", "tm_empresario": "OTB Sports", "tm_contrato": "31/12/2030", "tm_equipador": "adidas", "tm_valor_mercado": "11,00 M. €"
        },
        "Igor Jesus": {
            "nome": "Igor Jesus", "nome_completo": "Igor Jesus Maciel da Cruz", "posicao": "Centroavante", "posicoes_multiplas": ["Centroavante"],
            "clube": "Nottingham Forest", "idade": 25, "grupo": "Reservas", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 8.0,
            "pontos_fortes": "Força física impressionante, pivô dominante, presença de área invejável e cabeceio de elite.", "pontos_fracos": "Menor mobilidade fora da área em esquemas estritos de transição rápida.", "historico": "Atacante letal perfeito para perfurar defesas em blocos extremamente baixos.",
            "tm_nascimento": "25/02/2001", "tm_naturalidade": "Cuiabá, Brasil", "tm_altura": "1,79 m", "tm_pe": "direito", "tm_empresario": "JBSports", "tm_contrato": "30/06/2029", "tm_equipador": "N/A", "tm_valor_mercado": "25,00 M. €"
        },
        "Kauã Elias": {
            "nome": "Kauã Elias", "nome_completo": "Kauã Elias Nogueira", "posicao": "Centroavante", "posicoes_multiplas": ["Centroavante", "Segundo atacante"],
            "clube": "Shakhtar Donetsk", "idade": 20, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.5, "nota_roberto": 8.0,
            "pontos_fortes": "Faro de gol artilheiro, explosão muscular precoce fantástica e ótima mobilidade no terço final.", "pontos_fracos": "Precisa continuar maturando seu jogo associativo de costas para a baliza.", "historico": "É a principal aposta da base brasileira para ser a sombra direta do Endrick rumo a 2030.",
            "tm_nascimento": "28/03/2006", "tm_naturalidade": "Uberlândia, Brasil", "tm_altura": "1,81 m", "tm_pe": "direito", "tm_empresario": "LINK SPORTS", "tm_contrato": "31/12/2029", "tm_equipador": "N/A", "tm_valor_mercado": "15,00 M. €"
        }
    }

    # Mescla Segura dos Atletas
    for nome, dados in novos_atletas.items():
        if nome not in data:
            data[nome] = dados
        else:
            for k, v in dados.items():
                if k.startswith('tm_') or k == "nome_completo" or k == "clube":
                    data[nome][k] = v

    # Faxina Final de Padronização WCAG/Arquitetura
    pos_map_limpeza = {
        "Lateral Esquerdo": "Lateral-esquerdo", "Lateral Direito": "Lateral-direito",
        "Zagueiro Esquerdo": "Zagueiro", "Zagueiro Direito": "Zagueiro", "Zagueiro": "Zagueiro",
        "Meio-Campo (Defensivo)": "Volante", "Meio-Campo (Apoio)": "Mezzala esquerdo",
        "Meio-Campo (Criativo)": "Meia-armador", "Ponta Esquerda": "Ponta-esquerda",
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
        "Alisson": {"nome": "Alisson", "posicao": "Goleiro", "clube": "Liverpool", "idade": 33, "posicoes_multiplas": ["Goleiro"]}
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
    urls = {"Série A": f"{url_base}/tabelas/campeonato-brasileiro/serie-a", "Série B": f"{url_base}/tabelas/campeonato-brasileiro/serie-b"}
    headers = {"User-Agent": "Mozilla/5.0"}
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
                            nome_chave = " ".join(colunas[1].text.strip().split()).lower()
                            dados_cbf[nome_chave] = {
                                "posicao": f"{posicao}º", "pts": colunas[2].text.strip(),
                                "jogos": colunas[3].text.strip(), "vitorias": colunas[4].text.strip(), "serie": serie
                            }
        except Exception:
            pass
    return dados_cbf

tabela_ao_vivo_cbf = buscar_classificacao_cbf()

def obter_dados_reais_clube(clube):
    clube_busca = clube.lower().strip()
    for chave_time, dados in tabela_ao_vivo_cbf.items():
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
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Vitor Reis", "63%", "23%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "26%", "LD"),
        "Volante (VOL)": (["Volante"], "André", "38%", "46%", "VOL"),
        "Volante Apoio (VOL)": (["Volante", "Mezzala esquerdo", "Mezzala direito"], "Bruno Guimarães", "62%", "46%", "VOL"),
        "Meia-Armador (MEI)": (["Meia-armador"], "Rodrygo", "50%", "58%", "MEI"),
        "Ponta-esquerda (PE)": (["Ponta-esquerda"], "Vinicius Junior", "20%", "80%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "84%", "CA"),
        "Ponta-direita (PD)": (["Ponta-direita"], "Estevão", "80%", "80%", "PD")
    },
    "4-4-2 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "26%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "23%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Vitor Reis", "63%", "23%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "26%", "LD"),
        "Volante (VOL)": (["Volante"], "André", "50%", "42%", "VOL"),
        "Mezzala Esquerdo (MCE)": (["Mezzala esquerdo"], "Bruno Guimarães", "32%", "53%", "MCE"),
        "Mezzala Direito (MCD)": (["Mezzala direito", "Mezzala esquerdo", "Meia-armador"], "Danilo", "68%", "53%", "MCD"),
        "Meia-Armador (MEI)": (["Meia-armador"], "Rodrygo", "50%", "65%", "MEI"),
        "Segundo Atacante (SA)": (["Segundo atacante", "Ponta-esquerda", "Ponta-direita", "Centroavante"], "Vinicius Junior", "35%", "83%", "SA"),
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
    if not p: return nome
    pos_list = p.get("posicoes_multiplas", [p.get("posicao", "OBS")])
    abrevs = [ABREVIACOES.get(pos, "OBS") for pos in pos_list]
    abrev_str = "/".join(list(dict.fromkeys(abrevs)))
    return f"{nome} ({abrev_str})"

# ==========================================
# 7. MENU LATERAL & NAVEGAÇÃO
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #EAB308; margin-top:15px;'>CONSELHO TÁTICO</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação do Painel:",
    ["🏟️ Campo de Jogo (Escalação)", "👤 Perfis dos Jogadores & Scout", "📋 Gestão do Roster", "📊 Análise de Opiniões"]
)

if "escalados" not in st.session_state:
    st.session_state.escalados = {
        "Goleiro (GOL)": "Alisson", "Lateral-esquerdo (LE)": "Kaiki Bruno",
        "Zagueiro Esquerdo (ZAG)": "Gabriel Magalhães", "Zagueiro Direito (ZAG)": "Vitor Reis",
        "Lateral-direito (LD)": "Wesley França", "Volante (VOL)": "André",
        "Volante Apoio (VOL)": "Bruno Guimarães", "Meia-Armador (MEI)": "Rodrygo",
        "Ponta-esquerda (PE)": "Vinicius Junior", "Centroavante (CA)": "Endrick",
        "Ponta-direita (PD)": "Estevão"
    }

# ==========================================
# 8. TELA 1: CAMPO DE JOGO E RAIO-X
# ==========================================
if menu == "🏟️ Campo de Jogo (Escalação)":
    st.markdown("<h1 class='app-title'>🏆 O Caminho para o Hexa</h1>", unsafe_allow_html=True)
    st.markdown("""<p class="project-subtitle" style="text-align: center;">Painel tático interativo voltado ao planejamento geracional da Seleção Brasileira para 2030.</p>""", unsafe_allow_html=True)
    
    col_config, col_campo = st.columns([1, 2])
    
    with col_config:
        st.markdown("### 📋 Calibrar Escalação")
        tática_ativa = st.selectbox("Esquema Tático (Carlo Ancelotti):", list(TATICAS.keys()), key="tactical_selector")
        layout_ativo = TATICAS[tática_ativa]
        
        if "ultima_formacao" not in st.session_state or st.session_state.ultima_formacao != tática_ativa:
            nova_escalacao = {}
            for slot, info in layout_ativo.items():
                pos_validas, atleta_padrao = info[0], info[1]
                atleta_reutilizado = None
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

        novos_titulares = {}
        for slot, info in layout_ativo.items():
            pos_validas = info[0]
            valid_names = obter_atletas_compativeis(pos_validas)
            selecionados = list(novos_titulares.values())
            available = [name for name in valid_names if name not in selecionados]
            if not available: available = valid_names
            
            default_val = st.session_state.escalados.get(slot, info[1])
            if default_val in selecionados: default_val = available[0] if available else info[1]
            if default_val not in available: available.append(default_val)
            
            available = sorted(list(set(available)))
            idx = available.index(default_val) if default_val in available else 0
            
            escolha = st.selectbox(f"{slot}:", available, index=idx, format_func=formatar_jogador_com_posicao, key=f"sel_{slot}")
            novos_titulares[slot] = escolha
            
        st.session_state.escalados = novos_titulares

    with col_campo:
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
            
            if match_index == 0:
                border_color = "#22C55E"
            elif match_index == 1:
                border_color = "#EAB308"
            elif match_index >= 2:
                border_color = "#F97316"
            else:
                border_color = "#EF4444"
            
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
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #F8FAFC;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #22C55E; border-radius: 50%;"></span><b>Linha Verde:</b> Função Primária</div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #F8FAFC;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #EAB308; border-radius: 50%;"></span><b>Linha Amarela:</b> Função Secundária</div>
            <div style="display: flex; align-items: center; gap: 8px; font-size: 9.5pt; color: #F8FAFC;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #F97316; border-radius: 50%;"></span><b>Linha Laranja:</b> Função Terciária (Emergencial)</div>
        </div>
        """, unsafe_allow_html=True)

        titulares_dados = [jogadores[n] for n in st.session_state.escalados.values() if n in jogadores]
        idades_26 = [j.get("idade", 22) for j in titulares_dados]
        alturas = [extrair_numero(j.get("tm_altura", "0")) for j in titulares_dados]
        pesos = [extrair_numero(j.get("tm_peso", "0")) for j in titulares_dados] 
        valores = [extrair_numero(j.get("tm_valor_mercado", "0")) for j in titulares_dados]

        media_id_26 = sum(idades_26) / len(idades_26) if idades_26 else 0
        media_id_30 = media_id_26 + 4
        
        alt_validas = [a for a in alturas if a > 0]
        media_alt = sum(alt_validas) / len(alt_validas) if alt_validas else 0
        
        peso_validas = [p for p in pesos if p > 0]
        media_peso = sum(peso_validas) / len(peso_validas) if peso_validas else 0
        
        val_validas = [v for v in valores if v > 0]
        total_valor = sum(val_validas)
        media_valor = total_valor / len(val_validas) if val_validas else 0
        
        st.markdown(f"""
        <div style="background-color: #020617; padding: 20px; border-radius: 15px; border-top: 4px solid #EAB308; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 25px;">
            <h3 style="color: #F8FAFC; text-align: center; margin-top: 0; margin-bottom: 20px; font-size: 1.2rem;">📊 Raio-X do Elenco Titular</h3>
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px; text-align: center;">
                <div style="flex: 1; min-width: 100px;">
                    <div style="color: #94A3B8; font-size: 8pt; text-transform: uppercase; font-weight: bold;">Idade Média (Hoje)</div>
                    <div style="color: #F8FAFC; font-size: 14pt; font-weight: 800;">{media_id_26:.1f}</div>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <div style="color: #94A3B8; font-size: 8pt; text-transform: uppercase; font-weight: bold;">Idade Média (2030)</div>
                    <div style="color: #EAB308; font-size: 14pt; font-weight: 800;">{media_id_30:.1f}</div>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <div style="color: #94A3B8; font-size: 8pt; text-transform: uppercase; font-weight: bold;">Altura Média</div>
                    <div style="color: #F8FAFC; font-size: 14pt; font-weight: 800;">{media_alt:.2f} m</div>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <div style="color: #94A3B8; font-size: 8pt; text-transform: uppercase; font-weight: bold;">Peso Médio</div>
                    <div style="color: #F8FAFC; font-size: 14pt; font-weight: 800;">{f'{media_peso:.1f} kg' if media_peso > 0 else 'N/A'}</div>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <div style="color: #94A3B8; font-size: 8pt; text-transform: uppercase; font-weight: bold;">Valor do Time</div>
                    <div style="color: #22C55E; font-size: 14pt; font-weight: 800;">€ {total_valor:.1f} M</div>
                </div>
                <div style="flex: 1; min-width: 100px;">
                    <div style="color: #94A3B8; font-size: 8pt; text-transform: uppercase; font-weight: bold;">Média/Atleta</div>
                    <div style="color: #22C55E; font-size: 14pt; font-weight: 800;">€ {media_valor:.1f} M</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        
        export_data = json.dumps(st.session_state.escalados, indent=4, ensure_ascii=False)
        st.download_button(
            label="📥 Baixar Escalação (JSON)",
            data=export_data,
            file_name=f"tática_{tática_ativa.replace(' ', '_').lower()}.json",
            mime="application/json",
            use_container_width=True
        )
            
        escalados_nomes = list(st.session_state.escalados.values())
        mensagem_share = f"Montei minha Seleção Brasileira no esquema {tática_ativa} do app 'O Caminho para o Hexa'! 🏆\\n\\nMeu Time: {', '.join(escalados_nomes[:5])} e mais!\\n\\nMonte a sua também!"
        texto_codificado = urllib.parse.quote(mensagem_share)
        
        st.markdown(f"""
        <div style="display: flex; gap: 12px; margin-top: 15px; flex-wrap: wrap;">
            <a href="https://api.whatsapp.com/send?text={texto_codificado}" target="_blank" style="flex: 1; min-width: 120px; background-color: #166534; color: #F8FAFC; text-align: center; padding: 12px; border-radius: 8px; font-weight: 800; text-decoration: none; border: 1px solid #22C55E; transition: 0.3s;">
                🟢 WhatsApp
            </a>
            <a href="https://www.instagram.com/" target="_blank" title="Dica: Copie o texto da sua escalação e cole nos seus Stories do Instagram!" style="flex: 1; min-width: 120px; background-color: #831843; color: #F8FAFC; text-align: center; padding: 12px; border-radius: 8px; font-weight: 800; text-decoration: none; border: 1px solid #F43F5E; transition: 0.3s;">
                📸 Instagram
            </a>
            <a href="https://threads.net/intent/post?text={texto_codificado}" target="_blank" style="flex: 1; min-width: 120px; background-color: #1E293B; color: #F8FAFC; text-align: center; padding: 12px; border-radius: 8px; font-weight: 800; text-decoration: none; border: 1px solid #94A3B8; transition: 0.3s;">
                🌀 Threads
            </a>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TELA 2: PERFIS DOS JOGADORES & SCOUT
# ==========================================
elif menu == "👤 Perfis dos Jogadores & Scout":
    st.title("👤 Ficha Individual do Atleta")
    selected_name = st.selectbox("Escolha o Atleta:", sorted(list(jogadores.keys())))
    p = jogadores[selected_name]
    
    st.markdown("---")
    
    col_p, col_d = st.columns([1, 2])
    
    with col_p:
        pos_list = p.get("posicoes_multiplas", [p.get("posicao")])
        abrev_str = "/".join(list(dict.fromkeys([ABREVIACOES.get(pos, "OBS") for pos in pos_list])))

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
        st.subheader("Avaliação Tática Interativa")
        
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
            
        st.markdown("### 📝 Dossiê Histórico de Discussões")
        st.markdown('<div class="stat-box">**🟢 Pontos Fortes:**<br>'+p.get("pontos_fortes", "Nenhuma informação cadastrada.")+'</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-box" style="border-left-color: #EF4444;">**🔴 Desafios & Pontos Fracos:**<br>'+p.get("pontos_fracos", "Nenhuma informação cadastrada.")+'</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-box" style="border-left-color: #3B82F6;">**🗣️ Notas das Discussões:**<br>'+p.get("historico", "Nenhuma anotação disponível.")+'</div>', unsafe_allow_html=True)

# ==========================================
# TELA 3: GESTÃO DO ROSTER
# ==========================================
elif menu == "📋 Gestão do Roster":
    st.title("📋 Gerenciador do Banco de Dados")
    
    tab_list, tab_add = st.tabs(["Jogadores Inscritos", "➕ Inscrever Nova Joia"])
    
    with tab_list:
        df_players = pd.DataFrame([{
            "Nome": k, "Posição": v.get("posicao", "N/A"), "Clube": v.get("clube", "N/A"),
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
        st.dataframe(df_stats.sort_values(by="Diferença", ascending=True).head(5)[["Nome", "Posição", "Vini", "Roberto"]], use_container_width=True, hide_index=True)

    with col_s2:
        st.markdown("### 🔥 Debates Acalorados")
        st.dataframe(df_stats.sort_values(by="Diferença", ascending=False).head(5)[["Nome", "Vini", "Roberto", "Diferença"]], use_container_width=True, hide_index=True)

# ==========================================
# 9. RADAR DO TORCEDOR (SIDEBAR PRIVADA)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Radar do Torcedor")

with st.sidebar.form("form_sugestao", clear_on_submit=True):
    tipo_sugestao = st.selectbox("Tipo de Envio:", ["Atleta Faltante", "Sugestão de Melhoria"])
    detalhes_sugestao = st.text_area("Conteúdo da Mensagem:", placeholder="Escreva sua sugestão...")
    
    if st.form_submit_button("Sugerir"):
        if detalhes_sugestao:
            assunto = urllib.parse.quote(f"Caminho para o Hexa: {tipo_sugestao}")
            corpo = urllib.parse.quote(f"Olá, Vini e Roberto!\n\nSugestão:\n\n{detalhes_sugestao}")
            mailto_url = f"mailto:viniciusbl87@gmail.com?subject={assunto}&body={corpo}"
            st.sidebar.success("Sugestão salva!")
            st.sidebar.markdown(f'<a href="{mailto_url}" target="_blank" style="background-color:#EAB308;color:#0F172A;font-weight:bold;padding:10px;border-radius:8px;text-align:center;display:block;text-decoration:none;">🚀 Enviar por E-mail</a>', unsafe_allow_html=True)
        else:
            st.sidebar.warning("Insira o texto antes de enviar!")