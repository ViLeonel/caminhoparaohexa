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
# 2. DESIGN VISUAL E CSS (PALETA AZUL E AMARELO)
# ==========================================
st.markdown("""
<style>
    /* Estilização Geral do App (Fundo Soft Navy/Grafite Escuro) */
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
    
    /* O Campo Tático Azul ("Blue Pitch") */
    .pitch-container {
        background: radial-gradient(circle, #1e3a8a 0%, #090d16 100%);
        border: 4px solid #eab308;
        border-radius: 20px;
        padding: 30px;
        position: relative;
        min-height: 720px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.7);
        margin-bottom: 25px;
    }
    .pitch-line-center {
        position: absolute;
        top: 50%;
        left: 0;
        width: 100%;
        height: 3px;
        background-color: rgba(234, 179, 8, 0.4);
    }
    .pitch-circle {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 160px;
        height: 160px;
        border: 3px solid rgba(234, 179, 8, 0.4);
        border-radius: 50%;
    }
    .pitch-penalty-top {
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 120px;
        border-bottom: 3px solid rgba(234, 179, 8, 0.4);
        border-left: 3px solid rgba(234, 179, 8, 0.4);
        border-right: 3px solid rgba(234, 179, 8, 0.4);
    }
    .pitch-penalty-bottom {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 120px;
        border-top: 3px solid rgba(234, 179, 8, 0.4);
        border-left: 3px solid rgba(234, 179, 8, 0.4);
        border-right: 3px solid rgba(234, 179, 8, 0.4);
    }
    
    /* Cards dos Jogadores no Campo */
    .player-card {
        background: rgba(15, 23, 42, 0.9);
        border: 2px solid #eab308;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        color: #f8fafc;
        font-weight: bold;
        font-size: 11pt;
        box-shadow: 0 8px 16px rgba(0,0,0,0.5);
        transition: transform 0.2s, border-color 0.2s;
    }
    .player-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    .rating-badge {
        background-color: #eab308;
        color: #090d16;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 9pt;
        font-weight: 800;
        margin-top: 6px;
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GERENCIAMENTO DE BANCO DE DADOS (JSON)
# ==========================================
DATA_FILE = "jogadores_hexa_2030.json"

def carregar_jogadores():
    if not os.path.exists(DATA_FILE):
        st.error("Erro: arquivo jogadores_hexa_2030.json não foi encontrado na pasta!")
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
        return {}

def salvar_jogadores(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

jogadores = carregar_jogadores()

# ==========================================
# 4. MOTOR LIVE SCRAPING (CBF BRASILEIRÃO)
# ==========================================
@st.cache_data(ttl=600)  # Mantém os dados guardados em cache por 10 minutos para o app ficar super veloz
def buscar_classificacao_cbf():
    """Busca a tabela de classificação do Brasileirão diretamente do site oficial da CBF"""
    urls = {
        "Série A": "https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a",
        "Série B": "https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-b"
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
                    for linha in linhas[1:]:  # Pula a linha do cabeçalho
                        colunas = linha.find_all("td")
                        if len(colunas) >= 5:
                            # Posição do time
                            pos_crua = colunas[0].text.strip()
                            posicao = "".join(filter(str.isdigit, pos_crua))
                            
                            # Nome do clube
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
            pass # Caso o site da CBF mude a estrutura ou caia, o sistema usa o fallback abaixo
            
    return dados_cbf

# Executa o crawler de dados
tabela_ao_vivo_cbf = buscar_classificacao_cbf()

# Banco de dados de backup (Fallback) caso o site da CBF esteja bloqueando requisições
TABELA_BACKUP_CBF = {
    "palmeiras": {"posicao": "1º", "pts": "40", "jogos": "18", "vitorias": "12", "serie": "Série A"},
    "flamengo": {"posicao": "2º", "pts": "34", "jogos": "17", "vitorias": "10", "serie": "Série A"},
    "cruzeiro": {"posicao": "3º", "pts": "31", "jogos": "18", "vitorias": "9", "serie": "Série A"},
    "bahia": {"posicao": "6º", "pts": "26", "jogos": "17", "vitorias": "7", "serie": "Série A"},
    "corinthians": {"posicao": "13º", "pts": "20", "jogos": "18", "vitorias": "5", "serie": "Série A"},
    "gremio": {"posicao": "15º", "pts": "18", "jogos": "17", "vitorias": "5", "serie": "Série A"},
    "santos": {"posicao": "1º", "pts": "38", "jogos": "18", "vitorias": "11", "serie": "Série B"}
}

def obter_dados_reais_clube(clube):
    clube_busca = clube.lower().strip()
    
    # 1. Tenta pegar os dados capturados ao vivo do site da CBF
    for chave_time, dados in tabela_ao_vivo_cbf.items():
        if clube_busca in chave_time or chave_time in clube_busca:
            return dados, "🔴 AO VIVO (CBF)"
            
    # 2. Se falhar por bloqueio de rede, usa os dados do backup
    for chave_time, dados in TABELA_BACKUP_CBF.items():
        if clube_busca in chave_time or chave_time in clube_busca:
            return dados, "📋 DADOS EM CACHE"
            
    return None, None

# ==========================================
# 5. REGRAS DE ESCALAÇÃO POR POSIÇÃO
# ==========================================
MAPA_POSICOES = {
    "Goleiro (GOL)": ["Goleiro"],
    "Lateral Esquerdo (LE)": ["Lateral Esquerdo"],
    "Zagueiro Esquerdo (ZE)": ["Zagueiro Esquerdo"],
    "Zagueiro Direito (ZD)": ["Zagueiro Direito"],
    "Lateral Direito (LD)": ["Lateral Direito"],
    "Primeiro Volante (VOL)": ["Meio-Campo (Defensivo)", "Zagueiro Direito"],  # Permite Beraldo improvisado aqui
    "Meio-Campo Apoio (MCE)": ["Meio-Campo (Apoio)"],
    "Meio-Campo Criativo (10)": ["Meio-Campo (Criativo)", "Ponta Esquerda"],  # Permite Martinelli de meia
    "Ponta Esquerda (PE)": ["Ponta Esquerda"],
    "Centroavante (CA)": ["Centroavante"],
    "Ponta Direita (PD)": ["Ponta Direita"]
}

def obter_atletas_compativeis(pos_permitidas):
    filtrados = []
    for nome, dados in jogadores.items():
        if dados["posicao"] in pos_permitidas:
            filtrados.append(nome)
        # Versatilidade de Lucas Beraldo (Volante)
        elif nome == "Lucas Beraldo" and "Meio-Campo (Defensivo)" in pos_permitidas:
            filtrados.append(nome)
        # Versatilidade de Gabriel Martinelli (Meia)
        elif nome == "Gabriel Martinelli" and "Meio-Campo (Criativo)" in pos_permitidas:
            filtrados.append(nome)
    return sorted(filtrados)

# ==========================================
# 6. MENU LATERAL & IDENTIDADE VISUAL
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/pt/e/e4/Confedera%C3%A7%C3%A3o_Brasileira_de_Futebol_2019.svg", width=100)
st.sidebar.markdown("<h2 style='text-align: center; color: #eab308; margin-top:0;'>CONSELHO TÁTICO</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação do Painel:",
    ["🏟️ Campo de Jogo (Escalação)", "👤 Perfis dos Jogadores & Scout", "📋 Gestão do Roster", "📊 Análise de Opiniões"]
)

# Configuração de titulares em cache de navegação
if "escalados" not in st.session_state:
    st.session_state.escalados = {
        "Goleiro (GOL)": "Alisson",
        "Lateral Esquerdo (LE)": "Kaiki Bruno",
        "Zagueiro Esquerdo (ZE)": "Gabriel Magalhães",
        "Zagueiro Direito (ZD)": "Lucas Beraldo",
        "Lateral Direito (LD)": "Wesley",
        "Primeiro Volante (VOL)": "Andrey Santos",
        "Meio-Campo Apoio (MCE)": "Bruno Guimarães",
        "Meio-Campo Criativo (10)": "Rodrygo",
        "Ponta Esquerda (PE)": "Vini Jr.",
        "Centroavante (CA)": "Endrick",
        "Ponta Direita (PD)": "Estevão"
    }

# ==========================================
# TELA 1: CAMPO DE JOGO
# ==========================================
if menu == "🏟️ Campo de Jogo (Escalação)":
    st.markdown("<h1 class='app-title'>🏆 Caminho Para o Hexa</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='project-subtitle' style='text-align: center;'>"
        "Uma plataforma tática criada por <strong>Vini Leoneo e Roberto Muñoz</strong> "
        "para planejar as escalações, projetar as idades e gerenciar o radar da Seleção Brasileira até a Copa do Mundo de 2030."
        "</p>", 
        unsafe_allow_html=True
    )
    
    col_config, col_campo = st.columns([1, 2])
    
    with col_config:
        st.markdown("### 📋 Calibrar Escalação")
        st.write("Substitua os titulares respeitando a posição de origem do atleta.")
        
        novos_titulares = {}
        for slot, pos_validas in MAPA_POSICOES.items():
            valid_names = obter_atletas_compativeis(pos_validas)
            default_val = st.session_state.escalados[slot]
            idx = valid_names.index(default_val) if default_val in valid_names else 0
            
            novos_titulares[slot] = st.selectbox(
                f"{slot}:",
                valid_names,
                index=idx,
                key=f"field_{slot}"
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
        
        # Desenhando o Campo de Futebol Azul
        st.markdown('<div class="pitch-container">', unsafe_allow_html=True)
        st.markdown('<div class="pitch-line-center"></div>', unsafe_allow_html=True)
        st.markdown('<div class="pitch-circle"></div>', unsafe_allow_html=True)
        st.markdown('<div class="pitch-penalty-top"></div>', unsafe_allow_html=True)
        st.markdown('<div class="pitch-penalty-bottom"></div>', unsafe_allow_html=True)
        
        # Ataque
        pe = jogadores.get(st.session_state.escalados["Ponta Esquerda (PE)"], {"nome": "Vini Jr.", "nota_vini": 9, "nota_roberto": 9})
        ca = jogadores.get(st.session_state.escalados["Centroavante (CA)"], {"nome": "Endrick", "nota_vini": 8, "nota_roberto": 9})
        pd = jogadores.get(st.session_state.escalados["Ponta Direita (PD)"], {"nome": "Estevão", "nota_vini": 9, "nota_roberto": 10})
        
        col_at = st.columns(3)
        with col_at[0]:
            st.markdown(f'<div class="player-card">PE: {pe["nome"]}<br><span class="rating-badge">★ {pe["nota_vini"]} / {pe["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_at[1]:
            st.markdown(f'<div class="player-card">CA: {ca["nome"]}<br><span class="rating-badge">★ {ca["nota_vini"]} / {ca["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_at[2]:
            st.markdown(f'<div class="player-card">PD: {pd["nome"]}<br><span class="rating-badge">★ {pd["nota_vini"]} / {pd["nota_roberto"]}</span></div>', unsafe_allow_html=True)
            
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Meio-Campo
        mce = jogadores.get(st.session_state.escalados["Meio-Campo Apoio (MCE)"], {"nome": "Bruno Guimarães", "nota_vini": 8, "nota_roberto": 8.5})
        m10 = jogadores.get(st.session_state.escalados["Meio-Campo Criativo (10)"], {"nome": "Rodrygo", "nota_vini": 8, "nota_roberto": 8})
        vol = jogadores.get(st.session_state.escalados["Primeiro Volante (VOL)"], {"nome": "Andrey Santos", "nota_vini": 7.5, "nota_roberto": 8})
        
        col_mid = st.columns(3)
        with col_mid[0]:
            st.markdown(f'<div class="player-card">MCE: {mce["nome"]}<br><span class="rating-badge">★ {mce["nota_vini"]} / {mce["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_mid[1]:
            st.markdown(f'<div class="player-card">MC: {m10["nome"]}<br><span class="rating-badge">★ {m10["nota_vini"]} / {m10["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_mid[2]:
            st.markdown(f'<div class="player-card">VOL: {vol["nome"]}<br><span class="rating-badge">★ {vol["nota_vini"]} / {vol["nota_roberto"]}</span></div>', unsafe_allow_html=True)
            
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Defesa
        le = jogadores.get(st.session_state.escalados["Lateral Esquerdo (LE)"], {"nome": "Kaiki Bruno", "nota_vini": 6, "nota_roberto": 6})
        ze = jogadores.get(st.session_state.escalados["Zagueiro Esquerdo (ZE)"], {"nome": "Gabriel Magalhães", "nota_vini": 9, "nota_roberto": 9})
        zd = jogadores.get(st.session_state.escalados["Zagueiro Direito (ZD)"], {"nome": "Lucas Beraldo", "nota_vini": 8, "nota_roberto": 8})
        ld = jogadores.get(st.session_state.escalados["Lateral Direito (LD)"], {"nome": "Wesley", "nota_vini": 7.5, "nota_roberto": 7.5})
        
        col_def = st.columns(4)
        with col_def[0]:
            st.markdown(f'<div class="player-card">LE: {le["nome"]}<br><span class="rating-badge">★ {le["nota_vini"]} / {le["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_def[1]:
            st.markdown(f'<div class="player-card">ZAG: {ze["nome"]}<br><span class="rating-badge">★ {ze["nota_vini"]} / {ze["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_def[2]:
            st.markdown(f'<div class="player-card">ZAG: {zd["nome"]}<br><span class="rating-badge">★ {zd["nota_vini"]} / {zd["nota_roberto"]}</span></div>', unsafe_allow_html=True)
        with col_def[3]:
            st.markdown(f'<div class="player-card">LD: {ld["nome"]}<br><span class="rating-badge">★ {ld["nota_vini"]} / {ld["nota_roberto"]}</span></div>', unsafe_allow_html=True)
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Goleiro
        gol = jogadores.get(st.session_state.escalados["Goleiro (GOL)"], {"nome": "Alisson", "nota_vini": 7, "nota_roberto": 7.5})
        col_gk = st.columns([1.5, 1, 1.5])
        with col_gk[1]:
            st.markdown(f'<div class="player-card">GOL: {gol["nome"]}<br><span class="rating-badge">★ {gol["nota_vini"]} / {gol["nota_roberto"]}</span></div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TELA 2: PERFIS DOS JOGADORES & SCOUT
# ==========================================
elif menu == "👤 Perfis dos Jogadores & Scout":
    st.title("👤 Ficha Individual & Scout em Tempo Real")
    st.write("Abra o dossiê detalhado do atleta. Se ele jogar no Brasil, pegaremos a classificação do clube dele ao vivo no site da CBF.")
    
    selected_name = st.selectbox("Escolha o Atleta:", sorted(list(jogadores.keys())))
    p = jogadores[selected_name]
    
    st.markdown("---")
    
    col_p, col_d = st.columns([1, 2])
    
    with col_p:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 25px; border-radius: 15px; border: 3px solid #eab308; text-align: center;">
            <h2 style="color: #f8fafc; margin-bottom: 5px; font-size: 2.2rem;">{p['nome']}</h2>
            <span style="background-color: #3b82f6; color: #f8fafc; font-weight: bold; padding: 5px 15px; border-radius: 20px; font-size: 10pt;">
                {p['tipo']}
            </span>
            <p style="margin-top: 20px; font-size: 11pt; color: #cbd5e1; text-align: left; line-height: 1.8;">
                <b>📍 Posição:</b> {p['posicao']}<br>
                <b>🏢 Clube Atual:</b> {p['clube']}<br>
                <b>📅 Idade em 2026:</b> {p['idade']} anos<br>
                <b>🏆 Idade em 2030:</b> <span style="color:#eab308; font-weight:bold;">{p['idade'] + 4} anos</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Avaliação Tática")
        st.metric("Nota do Vini", f"{p['nota_vini']:.1f} / 10")
        st.metric("Nota do Roberto", f"{p['nota_roberto']:.1f} / 10")

    with col_d:
        # Busca dinâmica na tabela da CBF
        dados_live, fonte_status = obter_dados_reais_clube(p['clube'])
        
        st.markdown(f"### 📈 Contexto do Clube na Temporada ({fonte_status if fonte_status else '🌐 LIGA EXTERNA'})")
        
        if dados_live:
            st.write(f"Atleta com contrato ativo no futebol nacional. Abaixo estão os dados reais do time dele no Brasileirão:")
            cbf_df = pd.DataFrame([{
                "Clube": p['clube'],
                "Campeonato": dados_live['serie'],
                "Posição Atual": dados_live['posicao'],
                "Pontos (PTS)": dados_live['pts'],
                "Partidas": dados_live['jogos'],
                "Vitórias": dados_live['vitorias']
            }])
            st.dataframe(cbf_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                f"ℹ️ {p['nome']} joga na Europa ({p['clube']}).\n\n"
                "Em breve, o sistema receberá novas conexões para trazer as métricas ao vivo das ligas da UEFA (La Liga, Premier League e Ligue 1)."
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
        st.markdown("**🗣️ Notas dos Debates (Vini & Roberto):**")
        st.write(p.get("historico", "Nenhuma anotação de mesa de bar cadastrada."))
        st.markdown('</div>', unsafe_allow_html=True)

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
                "Posição": v["posicao"],
                "Clube": v["clube"],
                "Idade 2026": v["idade"],
                "Idade 2030": v["idade"] + 4,
                "Grupo": v["grupo"],
                "Nota Vini": v["nota_vini"],
                "Nota Roberto": v["nota_roberto"],
                "Tipo": v["tipo"]
            } for k, v in jogadores.items()
        ])
        st.dataframe(df_players, use_container_width=True)
        
        st.markdown("### 🗑️ Cortar Atleta")
        remover_nome = st.selectbox("Selecione quem quer cortar:", list(jogadores.keys()))
        if st.button("Confirmar Corte Permanente"):
            if remover_nome in jogadores:
                del jogadores[remover_nome]
                salvar_jogadores(jogadores)
                st.success(f"{remover_nome} foi cortado do elenco!")
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
    st.write("Veja onde a opinião da comissão técnica converge perfeitamente e onde o debate é mais caloroso.")

    df_stats = pd.DataFrame([
        {
            "Nome": k,
            "Posição": v["posicao"],
            "Vini": v["nota_vini"],
            "Roberto": v["nota_roberto"],
            "Diferença Absoluta": abs(v["nota_vini"] - v["nota_roberto"])
        } for k, v in jogadores.items()
    ])

    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.subheader("🤝 Consenso Absoluto")
        st.write("Atletas onde as opiniões batem de forma idêntica:")
        concordancias = df_stats.sort_values(by="Diferença Absoluta", ascending=True).head(5)
        st.dataframe(concordancias[["Nome", "Posição", "Vini", "Roberto"]], use_container_width=True, hide_index=True)

    with col_s2:
        st.subheader("🔥 Divergências de Mesa de Bar")
        st.write("Atletas que geram as maiores discussões de bar entre a dupla:")
        divergencias = df_stats.sort_values(by="Diferença Absoluta", ascending=False).head(5)
        st.dataframe(divergencias[["Nome", "Posição", "Vini", "Roberto", "Diferença Absoluta"]], use_container_width=True, hide_index=True)

# ==========================================
# 7. CAIXA DE SUGESTÕES (RADAR TOTALMENTE PRIVADO)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Radar do Torcedor")
st.sidebar.write("Lembrou de alguma joia do futebol brasileiro que nós esquecemos? Mande agora mesmo!")

with st.sidebar.form("form_sugestao", clear_on_submit=True):
    sug_nome = st.text_input("Nome do Craque*", placeholder="Ex: Estevão Willian")
    sug_pos = st.text_input("Posição*", placeholder="Ex: Ponta Direita")
    sug_clube = st.text_input("Clube Atual*", placeholder="Ex: Palmeiras")
    sug_just = st.text_area("Por que ele merece estar no Radar?*", placeholder="Escreva as qualidades dele...")
    
    btn_sugestion = st.form_submit_button("Sugerir para a Comissão")
    
    if btn_sugestion:
        if sug_nome and sug_pos and sug_clube and sug_just:
            # Geração dinâmica do link para evitar crawlers salvando seu e-mail pessoal em texto puro
            assunto = urllib.parse.quote(f"Caminho para o Hexa: Nova Sugestão - {sug_nome}")
            corpo = urllib.parse.quote(
                f"Fala, Vini e Beto!\n\n"
                f"Quero sugerir um novo jogador para entrar no nosso radar tático da Copa de 2030:\n\n"
                f"👤 Atleta: {sug_nome}\n"
                f"📍 Posição: {sug_pos}\n"
                f"🏢 Clube: {sug_clube}\n\n"
                f"📝 Análise técnica de performance:\n{sug_just}\n\n"
                f"Abraços!"
            )
            mailto_url = f"mailto:viniciusbl87@gmail.com?subject={assunto}&body={corpo}"
            
            st.success("🎉 Sugestão compilada com sucesso!")
            st.markdown(f"""
                <div style="text-align: center; margin-top: 5px;">
                    <a href="{mailto_url}" target="_blank" style="background-color: #eab308; color: #090d16; font-weight: 800; padding: 10px 15px; border-radius: 8px; text-decoration: none; display: inline-block;">
                        🚀 Confirmar Envio por E-mail
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Por favor, preencha todos os campos obrigatórios!")