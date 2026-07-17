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
    "Meia-esquerda": "ME", "Meia-direita": "MD",
    "Ponta-esquerda": "PE", "Ponta-direita": "PD", "Segundo atacante": "SA", "Centroavante": "CA"
}

def extrair_numero(valor_texto, padrao=0.0):
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
# 4. GERENCIAMENTO DE BANCO DE DADOS (JSON) & SELF-HEALING
# ==========================================
DATA_FILE = "jogadores_hexa_2030.json"

# Injeção Completa da Base Histórica
BASE_HISTORICA_COMPLETA = {
    "Alisson": {"nome": "Alisson", "posicao": "Goleiro", "grupo": "Titulares", "nota_vini": 7.0, "nota_roberto": 7.5, "clube": "Liverpool", "idade": 33, "tipo": "Certeza Atual", "pontos_fortes": "Excelente posicionamento e carreira internacional sólida.", "pontos_fracos": "Idade avançada para o planejamento de longo prazo de 2030.", "historico": "Vini prefere sua liderança experiente, enquanto Roberto defende transição rápida.", "posicoes_multiplas": ["Goleiro"]},
    "Brazão": {"nome": "Brazão", "posicao": "Goleiro", "grupo": "Reservas", "nota_vini": 7.5, "nota_roberto": 7.5, "clube": "Santos", "idade": 25, "tipo": "Promessa 2030", "pontos_fortes": "Físico privilegiado e excelente potencial sob as traves.", "pontos_fracos": "Necessita de mais testes sob extrema pressão tática.", "historico": "Ambos concordam que ele reúne totais condições de disputar a titularidade.", "posicoes_multiplas": ["Goleiro"]},
    "Lucas Perri": {"nome": "Lucas Perri", "posicao": "Goleiro", "grupo": "Observação", "nota_vini": 6.5, "nota_roberto": 6.0, "clube": "Lyon", "idade": 28, "tipo": "Observação", "pontos_fortes": "Físico imponente e experiência recente em solo europeu.", "pontos_fracos": "Oscilações em momentos de alta carga decisiva.", "historico": "Visto como opção viável de elenco, mas sem garantias de liderar a meta.", "posicoes_multiplas": ["Goleiro"]},
    "Wesley França": {"nome": "Wesley França", "posicao": "Lateral-direito", "grupo": "Titulares", "nota_vini": 7.5, "nota_roberto": 7.5, "clube": "AS Roma", "idade": 22, "tipo": "Certeza Atual", "pontos_fortes": "Velocidade impressionante e excelente transição ofensiva.", "pontos_fracos": "Precisa calibrar o posicionamento defensivo nas coberturas.", "historico": "Roberto aposta em sua evolução máxima. Unanimidade no corredor direito.", "posicoes_multiplas": ["Lateral-direito", "Lateral-esquerdo"]},
    "Kaiki Bruno": {"nome": "Kaiki Bruno", "posicao": "Lateral-esquerdo", "grupo": "Titulares", "nota_vini": 6.0, "nota_roberto": 6.0, "clube": "Cruzeiro", "idade": 23, "tipo": "Certeza Atual", "pontos_fortes": "Apoio tático consistente e boa margem para evolução física.", "pontos_fracos": "Ainda inexperiente em confrontos internacionais de alto calibre.", "historico": "Aprovado por Roberto para iniciar a rodagem de testes devido ao gargalo do setor.", "posicoes_multiplas": ["Lateral-esquerdo"]},
    "Yan Couto": {"nome": "Yan Couto", "posicao": "Lateral-direito", "grupo": "Reservas", "nota_vini": 7.5, "nota_roberto": 7.0, "clube": "Borussia Dortmund", "idade": 24, "tipo": "Certeza Atual", "pontos_fortes": "Fácil associação no terço final e boa técnica de cruzamento.", "pontos_fracos": "Pode deixar o setor defensivo exposto ao subir constantemente.", "historico": "Grande opção de rotação para manter a intensidade do ataque lateral.", "posicoes_multiplas": ["Lateral-direito", "Mezzala direito"]},
    "Denner": {"nome": "Denner", "posicao": "Lateral-esquerdo", "grupo": "Reservas", "nota_vini": 7.0, "nota_roberto": 8.0, "clube": "Corinthians", "idade": 18, "tipo": "Promessa 2030", "pontos_fortes": "Capacidade técnica invejável e ótima leitura tática.", "pontos_fracos": "Muito jovem, precisa ser lapidado no time principal profissional.", "historico": "Roberto projeta teto competitivo muito elevado, similar a estrelas globais.", "posicoes_multiplas": ["Lateral-esquerdo"]},
    "Luciano Juba": {"nome": "Luciano Juba", "posicao": "Lateral-esquerdo", "grupo": "Observação", "nota_vini": 6.5, "nota_roberto": 7.0, "clube": "Bahia", "idade": 26, "tipo": "Observação", "pontos_fortes": "Excelente batida na bola e grande carisma com a torcida.", "pontos_fracos": "Dúvidas se suportaria o ritmo físico de pontas de elite na Copa.", "historico": "Roberto valoriza sua bola parada, enquanto Vini demonstra ressalvas táticas.", "posicoes_multiplas": ["Lateral-esquerdo"]},
    "Gabriel Magalhães": {"nome": "Gabriel Magalhães", "posicao": "Zagueiro", "grupo": "Titulares", "nota_vini": 9.0, "nota_roberto": 9.0, "clube": "FC Arsenal", "idade": 28, "tipo": "Certeza Atual", "pontos_fortes": "Combate aéreo imbatível, liderança nata e estabilidade de elite.", "pontos_fracos": "Nenhum ponto fraco relevante apontado no ciclo tático.", "historico": "Dono absoluto da posição e grande líder da defesa brasileira.", "posicoes_multiplas": ["Zagueiro"]},
    "Lucas Beraldo": {"nome": "Lucas Beraldo", "posicao": "Zagueiro", "grupo": "Titulares", "nota_vini": 8.0, "nota_roberto": 8.0, "clube": "Paris Saint-Germain", "idade": 22, "tipo": "Certeza Atual", "pontos_fortes": "Saída de bola primorosa e excelente senso de antecipação.", "pontos_fracos": "Pode sofrer contra atacantes de extrema imposição física direta.", "historico": "Cotado como curinga, podendo atuar também como primeiro homem de meio-campo.", "posicoes_multiplas": ["Zagueiro", "Lateral-esquerdo"]},
    "Murillo": {"nome": "Murillo", "posicao": "Zagueiro", "grupo": "Reservas", "nota_vini": 8.0, "nota_roberto": 8.0, "clube": "Nottingham Forest", "idade": 23, "tipo": "Certeza Atual", "pontos_fortes": "Força física impressionante nos duelos terrestres e ótimo passe longo.", "pontos_fracos": "Precisa ganhar mais minutos em jogos oficiais da seleção principal.", "historico": "Garante segurança total para qualquer alteração na dupla de zaga.", "posicoes_multiplas": ["Zagueiro"]},
    "Andrey Santos": {"nome": "Andrey Santos", "posicao": "Volante", "grupo": "Titulares", "nota_vini": 7.5, "nota_roberto": 8.0, "clube": "Chelsea FC", "idade": 22, "tipo": "Certeza Atual", "pontos_fortes": "Volante moderno de grande infiltração na área e pegada defensiva.", "pontos_fracos": "Precisa de estabilidade técnica como titular absoluto na Europa.", "historico": "Escolhido para ser a grande engrenagem de sustentação do meio-campo brasileiro.", "posicoes_multiplas": ["Volante", "Mezzala esquerdo", "Mezzala direito", "Lateral-esquerdo"]},
    "Bruno Guimarães": {"nome": "Bruno Guimarães", "posicao": "Mezzala esquerdo", "grupo": "Titulares", "nota_vini": 8.0, "nota_roberto": 8.5, "clube": "Newcastle", "idade": 28, "tipo": "Certeza Atual", "pontos_fortes": "Visão de jogo privilegiada e passes precisos que quebram linhas defensivas.", "pontos_fracos": "Desgaste em partidas que exijam excessiva cobertura de campo.", "historico": "Considerado indispensável para ditar o ritmo de posse de bola do time.", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante"]},
    "Rodrygo": {"nome": "Rodrygo", "posicao": "Meia-armador", "grupo": "Titulares", "nota_vini": 8.0, "nota_roberto": 8.0, "clube": "Real Madrid CF", "idade": 25, "tipo": "Certeza Atual", "pontos_fortes": "Técnica apurada, facilidade no drible e ótimo poder de decisão.", "pontos_fracos": "Não possui características naturais de cadência de jogo.", "historico": "Atua como o elo criativo dinâmico para dar verticalidade às jogadas táticas.", "posicoes_multiplas": ["Meia-armador", "Ponta-direita", "Ponta-esquerda", "Segundo atacante", "Centroavante"]},
    "Breno Bidon": {"nome": "Breno Bidon", "posicao": "Mezzala esquerdo", "grupo": "Reservas", "nota_vini": 7.0, "nota_roberto": 8.0, "clube": "Corinthians", "idade": 21, "tipo": "Promessa 2030", "pontos_fortes": "Controle refinado da bola e estilo tático clássico brasileiro.", "pontos_fracos": "Necessita adquirir maior massa física e experiência tática europeia.", "historico": "Identificado como potencial herdeiro técnico para as próximas competições.", "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante", "Meia-armador"]},
    "Gabriel Mec": {"nome": "Gabriel Mec", "posicao": "Meia-armador", "grupo": "Observação", "nota_vini": 7.5, "nota_roberto": 7.5, "clube": "Grêmio", "idade": 18, "tipo": "Promessa 2030", "pontos_fortes": "Passe cirúrgico, criatividade acima da média e inteligência.", "pontos_fracos": "Ainda em processo inicial de maturação física no esporte profissional.", "historico": "Vini acompanha de perto o garoto, vislumbrando um armador ideal para o futuro.", "posicoes_multiplas": ["Meia-armador", "Ponta-esquerda", "Segundo atacante"]},
    "Vinicius Junior": {"nome": "Vinicius Junior", "posicao": "Ponta-esquerda", "grupo": "Titulares", "nota_vini": 9.0, "nota_roberto": 9.0, "clube": "Real Madrid CF", "idade": 26, "tipo": "Certeza Atual", "pontos_fortes": "Melhor drible do planeta, aceleração letal e faro de gols em decisões.", "pontos_fracos": "Pode sofrer desgaste físico excessivo se isolado na ponta.", "historico": "A principal referência ofensiva e grande estrela do planejamento nacional.", "posicoes_multiplas": ["Ponta-esquerda", "Segundo atacante", "Centroavante", "Meia-esquerda"]},
    "Estevão": {"nome": "Estevão", "posicao": "Ponta-direita", "grupo": "Titulares", "nota_vini": 9.0, "nota_roberto": 10.0, "clube": "Chelsea FC", "idade": 19, "tipo": "Promessa 2030", "pontos_fortes": "Capacidade de drible genial, mentalidade vencedora e criatividade extrema.", "pontos_fracos": "Cuidados necessários com a carga física nesta transição inicial.", "historico": "Classificado com nota 10 por Roberto devido à sua genialidade sem precedentes.", "posicoes_multiplas": ["Ponta-direita", "Meia-armador", "Meia-direita"]},
    "Endrick": {"nome": "Endrick", "posicao": "Centroavante", "grupo": "Titulares", "nota_vini": 8.0, "nota_roberto": 9.0, "clube": "Real Madrid CF", "idade": 19, "tipo": "Certeza Atual", "pontos_fortes": "Explosão muscular fantástica, poder de chute e faro artilheiro.", "pontos_fracos": "Necessita de minutagem constante em competições de elite.", "historico": "O centroavante titular absoluto projetado para liderar o ataque em 2030.", "posicoes_multiplas": ["Centroavante", "Segundo atacante", "Ponta-direita"]},
    "Gabriel Martinelli": {"nome": "Gabriel Martinelli", "posicao": "Ponta-esquerda", "grupo": "Reservas", "nota_vini": 7.5, "nota_roberto": 8.0, "clube": "FC Arsenal", "idade": 25, "tipo": "Certeza Atual", "pontos_fortes": "Intensidade sem a bola, recomposição exemplar e poder de explosão.", "pontos_fracos": "Menor refino técnico se comparado aos titulares da ponta.", "historico": "Roberto destaca sua competitividade tática incomparável no elenco.", "posicoes_multiplas": ["Ponta-esquerda", "Meia-armador", "Mezzala esquerdo"]},
    "João Gomes": {"nome": "João Gomes", "nome_completo": "João Victor Gomes da Silva", "posicao": "Volante", "grupo": "Reservas", "nota_vini": 7.5, "nota_roberto": 8.0, "clube": "Wolverhampton Wanderers", "idade": 25, "tipo": "Certeza Atual", "pontos_fortes": "Combate defensivo agressivo de elite, alto índice de desarmes e fôlego interminável.", "pontos_fracos": "Controle disciplinar e passes longos de quebra de bloco.", "historico": "O verdadeiro cão de guarda do radar. Excelente para fechar a casinha.", "posicoes_multiplas": ["Volante", "Mezzala direito", "Mezzala esquerdo", "Meia-direita"]},
    "Allan": {"nome": "Allan", "posicao": "Ponta-direita", "clube": "SE Palmeiras", "idade": 22, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.0, "nota_roberto": 7.5, "pontos_fortes": "Dinâmica veloz na ponta e controle colado.", "posicoes_multiplas": ["Ponta-direita", "Meia-armador", "Mezzala direito"]},
    "Diego Callai": {"nome": "Diego Callai", "posicao": "Goleiro", "clube": "Sporting CP B", "idade": 22, "grupo": "Observação", "tipo": "Observação", "nota_vini": 6.5, "nota_roberto": 6.5, "posicoes_multiplas": ["Goleiro"]},
    "Luis Gustavo": {"nome": "Luis Gustavo", "posicao": "Zagueiro", "clube": "SE Palmeiras", "idade": 20, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.0, "nota_roberto": 7.0, "posicoes_multiplas": ["Zagueiro"]},
    "Guilherme Garutti": {"nome": "Guilherme Garutti", "posicao": "Zagueiro", "clube": "ACSC FC Arges", "idade": 32, "grupo": "Observação", "tipo": "Certeza Atual", "nota_vini": 6.0, "nota_roberto": 6.5, "posicoes_multiplas": ["Zagueiro"]},
    "Luis Felipe": {"nome": "Luis Felipe", "posicao": "Volante", "clube": "SE Palmeiras Sub-20", "idade": 18, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 6.5, "nota_roberto": 7.0, "posicoes_multiplas": ["Volante", "Mezzala direito", "Mezzala esquerdo"]},
    "Jhuan": {"nome": "Jhuan", "posicao": "Ponta-direita", "clube": "RB Bragantino Sub-20", "idade": 19, "grupo": "Observação", "tipo": "Observação", "nota_vini": 6.0, "nota_roberto": 6.5, "posicoes_multiplas": ["Ponta-direita"]},
    "Carlos Miguel": {"nome": "Carlos Miguel", "posicao": "Goleiro", "clube": "SE Palmeiras", "idade": 27, "grupo": "Observação", "tipo": "Certeza Atual", "nota_vini": 7.0, "nota_roberto": 7.0, "posicoes_multiplas": ["Goleiro"]},
    "Leonardo Nannetti": {"nome": "Leonardo Nannetti", "posicao": "Goleiro", "clube": "CR Flamengo Sub-20", "idade": 18, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 6.5, "nota_roberto": 7.0, "posicoes_multiplas": ["Goleiro"]},
    "Hugo Souza": {"nome": "Hugo Souza", "posicao": "Goleiro", "clube": "SC Corinthians", "idade": 27, "grupo": "Reservas", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 7.5, "posicoes_multiplas": ["Goleiro"]},
    "Igor Jesus": {"nome": "Igor Jesus", "posicao": "Centroavante", "clube": "Nottingham Forest", "idade": 25, "grupo": "Reservas", "tipo": "Certeza Atual", "nota_vini": 7.5, "nota_roberto": 8.0, "posicoes_multiplas": ["Centroavante"]},
    "Kauã Elias": {"nome": "Kauã Elias", "posicao": "Centroavante", "clube": "Shakhtar Donetsk", "idade": 20, "grupo": "Observação", "tipo": "Promessa 2030", "nota_vini": 7.5, "nota_roberto": 8.0, "posicoes_multiplas": ["Centroavante", "Segundo atacante"]},
    "André": {"nome": "André", "posicao": "Mezzala esquerdo", "clube": "Wolverhampton Wanderers", "idade": 24, "grupo": "Reservas", "nota_vini": 7.5, "nota_roberto": 7.5, "posicoes_multiplas": ["Mezzala esquerdo", "Mezzala direito", "Volante", "Meia-esquerda"]},
    "Matheus Cunha": {"nome": "Matheus Cunha", "posicao": "Centroavante", "clube": "Wolverhampton Wanderers", "idade": 27, "grupo": "Reservas", "nota_vini": 7.0, "nota_roberto": 7.5, "posicoes_multiplas": ["Centroavante", "Segundo atacante", "Meia-armador"]},
    "Danilo": {"nome": "Danilo", "posicao": "Volante", "clube": "Juventus", "idade": 25, "grupo": "Observação", "nota_vini": 6.5, "nota_roberto": 7.0, "posicoes_multiplas": ["Volante", "Mezzala direito", "Mezzala esquerdo"]}
}

def normalizar_banco_dados(data):
    if "Vini Jr." in data:
        data["Vinicius Junior"] = data.pop("Vini Jr.")
        data["Vinicius Junior"]["nome"] = "Vinicius Junior"
        
    if "Wesley" in data and "Wesley França" not in data:
        data["Wesley França"] = data.pop("Wesley")
        data["Wesley França"]["nome"] = "Wesley França"

    # Faxina de Padronização WCAG/Arquitetura
    pos_map_limpeza = {
        "Lateral Esquerdo": "Lateral-esquerdo", "Lateral Direito": "Lateral-direito",
        "Zagueiro Esquerdo": "Zagueiro", "Zagueiro Direito": "Zagueiro", "Zagueiro": "Zagueiro",
        "Meio-Campo (Defensivo)": "Volante", "Meio-Campo (Apoio)": "Mezzala esquerdo",
        "Meio-Campo (Criativo)": "Meia-armador", "Ponta Esquerda": "Ponta-esquerda",
        "Ponta Direita": "Ponta-direita", "Meia Esquerda": "Meia-esquerda", "Meia Direita": "Meia-direita"
    }

    for jogador, info in data.items():
        curr_pos = info.get("posicao")
        if curr_pos in pos_map_limpeza:
            info["posicao"] = pos_map_limpeza[curr_pos]
            
        if "posicoes_multiplas" not in info or not info["posicoes_multiplas"]:
            info["posicoes_multiplas"] = [info.get("posicao", "Observação")]

    return data

def carregar_jogadores():
    if not os.path.exists(DATA_FILE):
        data = BASE_HISTORICA_COMPLETA.copy()
        salvar_jogadores(data)
    else:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Rotina de Self-Healing: Injeta jogadores históricos faltantes
            for nome, dados in BASE_HISTORICA_COMPLETA.items():
                if nome not in data:
                    data[nome] = dados
                else:
                    for k, v in dados.items():
                        if k not in data:
                            data[nome][k] = v

        except Exception:
            data = BASE_HISTORICA_COMPLETA.copy()
            
    data = normalizar_banco_dados(data)
    salvar_jogadores(data)
    return data

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
    "4-3-3 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "28%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "22%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "22%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "28%", "LD"),
        "Mezzala Esquerdo (MCE)": (["Mezzala esquerdo", "Meia-esquerda", "Volante"], "Bruno Guimarães", "30%", "52%", "MCE"),
        "Volante (VOL)": (["Volante"], "André", "50%", "40%", "VOL"),
        "Mezzala Direito (MCD)": (["Mezzala direito", "Meia-direita", "Volante"], "João Gomes", "70%", "52%", "MCD"),
        "Ponta-esquerda (PE)": (["Ponta-esquerda", "Segundo atacante"], "Vinicius Junior", "20%", "72%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "82%", "CA"),
        "Ponta-direita (PD)": (["Ponta-direita", "Meia-armador"], "Estevão", "80%", "72%", "PD")
    },
    "4-3-3 Clássico": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "28%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "22%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "22%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "28%", "LD"),
        "Volante (VOL)": (["Volante"], "André", "38%", "45%", "VOL"),
        "Volante Apoio (VOL)": (["Volante", "Mezzala esquerdo", "Mezzala direito"], "Bruno Guimarães", "62%", "45%", "VOL"),
        "Meia-Armador (MEI)": (["Meia-armador"], "Rodrygo", "50%", "60%", "MEI"),
        "Ponta-esquerda (PE)": (["Ponta-esquerda"], "Vinicius Junior", "20%", "72%", "PE"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "82%", "CA"),
        "Ponta-direita (PD)": (["Ponta-direita"], "Estevão", "80%", "72%", "PD")
    },
    "4-4-2 Diamante": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "28%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "22%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "22%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "28%", "LD"),
        "Volante (VOL)": (["Volante"], "André", "50%", "40%", "VOL"),
        "Mezzala Esquerdo (MCE)": (["Mezzala esquerdo"], "Bruno Guimarães", "30%", "52%", "MCE"),
        "Mezzala Direito (MCD)": (["Mezzala direito", "Mezzala esquerdo", "Meia-armador"], "João Gomes", "70%", "52%", "MCD"),
        "Meia-Armador (MEI)": (["Meia-armador"], "Rodrygo", "50%", "65%", "MEI"),
        "Segundo Atacante (SA)": (["Segundo atacante", "Ponta-esquerda", "Ponta-direita", "Centroavante"], "Vinicius Junior", "38%", "78%", "SA"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "62%", "78%", "CA")
    },
    "4-4-2 Clássico": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "28%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "22%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "22%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "28%", "LD"),
        "Meia-esquerda (ME)": (["Meia-esquerda", "Mezzala esquerdo", "Ponta-esquerda"], "Bruno Guimarães", "20%", "55%", "ME"),
        "Volante Esquerdo (VOL)": (["Volante"], "André", "40%", "45%", "VOL"),
        "Volante Direito (VOL)": (["Volante"], "João Gomes", "60%", "45%", "VOL"),
        "Meia-direita (MD)": (["Meia-direita", "Mezzala direito", "Ponta-direita"], "Estevão", "80%", "55%", "MD"),
        "Segundo Atacante (SA)": (["Segundo atacante", "Meia-armador", "Ponta-esquerda"], "Vinicius Junior", "38%", "78%", "SA"),
        "Centroavante (CA)": (["Centroavante", "Segundo atacante"], "Endrick", "62%", "78%", "CA")
    },
    "4-2-3-1": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "28%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "22%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "22%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "28%", "LD"),
        "Volante Esquerdo (VOL)": (["Volante", "Mezzala esquerdo"], "André", "38%", "42%", "VOL"),
        "Volante Direito (VOL)": (["Volante", "Mezzala direito"], "Bruno Guimarães", "62%", "42%", "VOL"),
        "Ponta-esquerda (PE)": (["Ponta-esquerda", "Meia-esquerda"], "Vinicius Junior", "20%", "65%", "PE"),
        "Meia-Armador (MEI)": (["Meia-armador", "Segundo atacante"], "Rodrygo", "50%", "62%", "MEI"),
        "Ponta-direita (PD)": (["Ponta-direita", "Meia-direita"], "Estevão", "80%", "65%", "PD"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "82%", "CA")
    },
    "4-3-2-1 Árvore de Natal": {
        "Goleiro (GOL)": (["Goleiro"], "Alisson", "50%", "8%", "GOL"),
        "Lateral-esquerdo (LE)": (["Lateral-esquerdo"], "Kaiki Bruno", "15%", "28%", "LE"),
        "Zagueiro Esquerdo (ZAG)": (["Zagueiro"], "Gabriel Magalhães", "37%", "22%", "ZAG"),
        "Zagueiro Direito (ZAG)": (["Zagueiro"], "Lucas Beraldo", "63%", "22%", "ZAG"),
        "Lateral-direito (LD)": (["Lateral-direito"], "Wesley França", "85%", "28%", "LD"),
        "Mezzala Esquerdo (MCE)": (["Mezzala esquerdo", "Volante"], "Bruno Guimarães", "25%", "45%", "MCE"),
        "Volante (VOL)": (["Volante"], "André", "50%", "42%", "VOL"),
        "Mezzala Direito (MCD)": (["Mezzala direito", "Volante"], "João Gomes", "75%", "45%", "MCD"),
        "Meia-Armador Esq (MEI)": (["Meia-armador", "Segundo atacante", "Ponta-esquerda"], "Vinicius Junior", "35%", "65%", "MEI"),
        "Meia-Armador Dir (MEI)": (["Meia-armador", "Segundo atacante", "Ponta-direita"], "Rodrygo", "65%", "65%", "MEI"),
        "Centroavante (CA)": (["Centroavante"], "Endrick", "50%", "82%", "CA")
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
        "Zagueiro Esquerdo (ZAG)": "Gabriel Magalhães", "Zagueiro Direito (ZAG)": "Lucas Beraldo",
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
        valores = [extrair_numero(j.get("tm_valor_mercado", "0")) for j in titulares_dados]

        media_id_26 = sum(idades_26) / len(idades_26) if idades_26 else 0
        media_id_30 = media_id_26 + 4
        
        alt_validas = [a for a in alturas if a > 0]
        media_alt = sum(alt_validas) / len(alt_validas) if alt_validas else 0
        
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
        
        escalados_nomes = list(st.session_state.escalados.values())
        mensagem_share = f"Montei minha Seleção Brasileira no esquema {tática_ativa} do app 'O Caminho para o Hexa'! 🏆\\n\\nMeu Time: {', '.join(escalados_nomes[:5])} e mais!\\n\\nMonte a sua também!"
        texto_codificado = urllib.parse.quote(mensagem_share)
        
        st.markdown("""
        <p style="text-align: center; color: #94A3B8; font-size: 0.95rem; margin-bottom: 5px;">
            <i>📸 Dica: Tire um <b>print (screenshot)</b> desta tela e compartilhe sua escalação usando os botões abaixo!</i>
        </p>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap;">
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
    tipo_sugestao = st.selectbox("Tipo de Envio:", ["Sugerir Jogador", "Sugestão de Melhoria"])
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