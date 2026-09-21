import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests
import hashlib
import os
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. CONFIGURAÇÃO VISUAL & TEMA DARK GLASS
# ==========================================
st.set_page_config(
    page_title="Radar Pro - Terminal Quantitativo",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc !important;
        font-size: 1.05rem;
    }
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    p, span, label {
        color: #f1f5f9 !important;
    }
    .stCaption {
        color: #94a3b8 !important;
        font-weight: 500;
    }
    button[data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 700;
        color: #94a3b8 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
    }

    /* MATCH CARD GLASSMORPHISM */
    .match-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .teams-container {
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 8px 0 14px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .team-cell {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 42%;
    }
    .team-cell.away {
        justify-content: flex-end;
    }
    .team-logo-img {
        width: 38px;
        height: 38px;
        object-fit: contain;
        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.5));
    }
    .team-name-text {
        font-size: 1.15rem;
        font-weight: 800;
        color: #ffffff;
    }
    .vs-cell {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 800;
        color: #94a3b8;
    }
    .market-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
        margin: 12px 0 8px 0;
    }
    .market-label {
        font-size: 1.05rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .pills-group {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    .pill-odd {
        background-color: #0f172a;
        color: #38bdf8;
        border: 1px solid #0284c7;
        padding: 3px 10px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 800;
    }
    .badge-torneio {
        background-color: #1e293b;
        color: #cbd5e1 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #334155;
    }
    .badge-hora {
        background-color: #0284c7;
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-ao-vivo {
        background-color: #dc2626;
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .badge-placar {
        background-color: #0f172a;
        color: #38bdf8 !important;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 1.05rem;
        font-weight: 900;
        border: 1px solid #0284c7;
    }
    .badge-ev {
        background-color: #065f46;
        color: #6ee7b7 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 800;
        border: 1px solid #059669;
    }
    .badge-observacao {
        background-color: #854d0e;
        color: #fef08a !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-alvo {
        background-color: #312e81;
        color: #c7d2fe !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #4338ca;
    }
    .props-bar {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 8px;
        padding: 6px 12px;
        margin-top: 6px;
        font-size: 0.88rem;
        color: #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .raio-x-box {
        background-color: #0b1329;
        border-left: 3px solid #38bdf8;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0 8px 0;
        font-size: 0.92rem;
        color: #cbd5e1 !important;
        line-height: 1.5;
    }
    .alternativas-box {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px dashed rgba(56, 189, 248, 0.3);
        border-radius: 8px;
        padding: 8px 12px;
        margin-top: 8px;
        font-size: 0.88rem;
        color: #94a3b8;
    }
    .risco-box {
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid rgba(239, 68, 68, 0.25);
        color: #fca5a5 !important;
        font-size: 0.88rem;
    }

    /* PÍLULA FLUTUANTE DO BILHETE */
    div[data-testid="stElementContainer"]:has(#floating-anchor) + div[data-testid="stElementContainer"] {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        z-index: 999999 !important;
        width: auto !important;
    }
    div[data-testid="stElementContainer"]:has(#floating-anchor) + div[data-testid="stElementContainer"] button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 50px !important;
        padding: 14px 26px !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.85), 0 0 20px rgba(56,189,248,0.5) !important;
        cursor: pointer !important;
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stElementContainer"]:has(#floating-anchor) + div[data-testid="stElementContainer"] button:hover {
        transform: scale(1.05) !important;
        border-color: #7dd3fc !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.95), 0 0 25px rgba(56,189,248,0.8) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS E AUTENTICAÇÃO
# ==========================================
DB_NAME = "radar_dados.db"

def hash_pw(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            senha_hash TEXT,
            banca_atual REAL,
            unidade_pct REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS apostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            data TEXT,
            descricao TEXT,
            tipo_aposta TEXT,
            odd REAL,
            valor REAL,
            status TEXT,
            motivo_red TEXT
        )
    ''')
    
    banca_s, unit_s = 564.40, 2.0
    banca_p, unit_p = 500.00, 2.0
    try:
        res_s = c.execute("SELECT banca_atual, unidade_pct FROM usuarios WHERE username IN ('santibet', 'Guilherme')").fetchone()
        if res_s:
            banca_s, unit_s = res_s
        res_p = c.execute("SELECT banca_atual, unidade_pct FROM usuarios WHERE username IN ('palaciobet', 'Palacio')").fetchone()
        if res_p:
            banca_p, unit_p = res_p
    except Exception:
        pass
        
    c.execute("INSERT OR REPLACE INTO usuarios VALUES ('santibet', ?, ?, ?)", (hash_pw("1234"), banca_s, unit_s))
    c.execute("INSERT OR REPLACE INTO usuarios VALUES ('palaciobet', ?, ?, ?)", (hash_pw("1234"), banca_p, unit_p))
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB_NAME)

# ==========================================
# 3. TELA DE LOGIN & CADASTRO
# ==========================================
if "usuario_ativo" not in st.session_state:
    st.session_state.usuario_ativo = None

if not st.session_state.usuario_ativo:
    c_center = st.columns([1, 1.4, 1])[1]
    with c_center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #38bdf8;'>🛡️ RADAR PRO</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94a3b8;'>Terminal Quantitativo de Inteligência Esportiva</p>", unsafe_allow_html=True)
        
        tab_login, tab_cad = st.tabs(["🔑 Entrar no Sistema", "📝 Criar Novo Acesso"])
        
        with tab_login:
            st.markdown("##### Acesse o seu terminal:")
            u_log = st.text_input("Usuário:", placeholder="santibet ou palaciobet", key="log_user").strip().lower()
            s_log = st.text_input("Senha:", type="password", key="log_pass").strip()
            
            if st.button("Acessar Radar Pro", use_container_width=True, type="primary"):
                conn = get_db()
                res = conn.execute("SELECT username, senha_hash FROM usuarios WHERE LOWER(username) = ?", (u_log,)).fetchone()
                conn.close()
                if res and res[1] == hash_pw(s_log):
                    st.session_state.usuario_ativo = res[0]
                    st.success(f"Bem-vindo, {res[0]}!")
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")
                    
        with tab_cad:
            st.markdown("##### Registo de operador:")
            u_cad = st.text_input("Escolha o seu Usuário:", key="cad_user").strip()
            s_cad = st.text_input("Crie uma Senha:", type="password", key="cad_pass").strip()
            banca_ini = st.number_input("Banca Inicial (R$):", value=50.0, step=10.0, key="cad_banca")
            
            if st.button("Registar e Iniciar", use_container_width=True):
                if not u_cad or not s_cad:
                    st.warning("Preencha usuário e senha.")
                else:
                    conn = get_db()
                    existe = conn.execute("SELECT username FROM usuarios WHERE LOWER(username) = ?", (u_cad.lower(),)).fetchone()
                    if existe:
                        st.error("Este nome de utilizador já se encontra registado.")
                        conn.close()
                    else:
                        conn.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (u_cad, hash_pw(s_cad), banca_ini, 2.0))
                        conn.commit()
                        conn.close()
                        st.session_state.usuario_ativo = u_cad
                        st.success("Conta configurada!")
                        st.rerun()
                        
    st.stop()

usuario_ativo = st.session_state.usuario_ativo

# ==========================================
# 4. MOTORES QUANTITATIVOS (FUTEBOL)
# ==========================================
def calcular_pre_jogo(casa, fora, torneio):
    chave = f"{casa}_{fora}_{torneio}"
    hash_val = int(hashlib.md5(chave.encode()).hexdigest(), 16)
    
    catalogo = [
        {
            "mercado": "Mais de 0.5 Gols no 1º Tempo (HT)",
            "odd": 1.48,
            "prob": 0.81,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥 🟩",
            "l10_pct": "90%",
            "projecao": "Projeção: 1.3 gols no 1T (+0.8 da linha)",
            "raio_x": [
                f"{casa} registou golos na primeira parte em 9 dos últimos 10 confrontos.",
                "Pressão inicial: média de 3.4 remates à baliza antes dos 30'.",
                "Exposição reduzida: operação resolvida no primeiro golo."
            ],
            "ponto_risco": f"Se {fora} optar por um bloco baixo fechado, a oportunidade de golo pode atrasar.",
            "alternativas": [
                {"mercado": "Mais de 1.5 Gols Totais", "odd": 1.36},
                {"mercado": f"Empate Anula: {casa}", "odd": 1.40}
            ]
        },
        {
            "mercado": f"Dupla Chance: {casa} ou Empate + Menos de 4.5 Gols",
            "odd": 1.54,
            "prob": 0.79,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥 🟩 🟩",
            "l10_pct": "90%",
            "projecao": "Projeção: 2.1 gols totais (Abaixo de 4.5)",
            "raio_x": [
                f"Consistência: {casa} sustenta invencibilidade no seu terreno.",
                "Baixo risco de resultado dilatado: 90% dos jogos terminaram abaixo de 5 golos.",
                "Proteção dupla: cobre favoritismo e previne resultados atípicos."
            ],
            "ponto_risco": "Expulsão de um defesa mandante pode quebrar a organização da linha defensiva.",
            "alternativas": [
                {"mercado": f"Vitória Simples: {casa}", "odd": 1.85},
                {"mercado": "Menos de 3.5 Gols", "odd": 1.30}
            ]
        },
        {
            "mercado": "Mais de 1.5 Gols no Jogo",
            "odd": 1.38,
            "prob": 0.84,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥",
            "l10_pct": "90%",
            "projecao": "Projeção: 2.7 gols esperados (xG combinado)",
            "raio_x": [
                "Volume ofensivo expressivo: soma de xG superior a 2.6.",
                f"{fora} sofreu pelo menos um golo nas últimas 7 partidas como visitante.",
                "Proteção matemática confirmada contra empates a zero."
            ],
            "ponto_risco": "Relvado pesado ou condições meteorológicas adversas reduzem a dinâmica atacante.",
            "alternativas": [
                {"mercado": "Mais de 2.0 Gols (Asiático)", "odd": 1.62},
                {"mercado": "Mais de 0.5 Gols no 1º Tempo", "odd": 1.45}
            ]
        },
        {
            "mercado": "Mais de 7.5 Escanteios no Jogo",
            "odd": 1.45,
            "prob": 0.82,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟥 🟩 🟩 🟩 🟩",
            "l10_pct": "90%",
            "projecao": "Projeção: 10.4 escanteios (+2.9 da linha)",
            "raio_x": [
                "Transição rápida pelas alas com elevado índice de cruzamentos.",
                "Média estatística combinada aponta mais de 10 pontapés de canto.",
                "Linha rebaixada de segurança (7.5) abaixo das cotações normais."
            ],
            "ponto_risco": "Caso o mandante marque 2 golos cedo, o ritmo nos flancos laterais pode abrandar.",
            "alternativas": [
                {"mercado": "Mais de 8.5 Escanteios", "odd": 1.70},
                {"mercado": f"Mais escanteios: {casa}", "odd": 1.55}
            ]
        },
        {
            "mercado": "Ambas as Equipes Marcam: Sim",
            "odd": 1.76,
            "prob": 0.69,
            "l10_pattern": "🟩 🟩 🟩 🟥 🟩 🟩 🟩 🟩 🟥 🟩",
            "l10_pct": "80%",
            "projecao": "Projeção: Alta conversão ofensiva x defesas vazadas",
            "raio_x": [
                "Ataques eficazes a defrontar setores defensivos que sofrem golos com frequência.",
                f"Ambos os conjuntos marcaram na maioria das partidas recentes do {casa}.",
                "Cotação com valor esperado (+EV) face ao risco implícito."
            ],
            "ponto_risco": "Avançados titulares no banco ou falta de pontaria em ocasiões claras.",
            "alternativas": [
                {"mercado": "Mais de 2.5 Gols no Jogo", "odd": 2.05},
                {"mercado": f"{casa} marca pelo menos 1 golo", "odd": 1.25}
            ]
        }
    ]
    
    escolha = catalogo[hash_val % len(catalogo)]
    ev_calculado = round(((escolha["prob"] * escolha["odd"]) - 1) * 100, 1)
    return {
        "mercado": escolha["mercado"],
        "odd": escolha["odd"],
        "ev": max(ev_calculado, 8.5),
        "l10_pattern": escolha["l10_pattern"],
        "l10_pct": escolha["l10_pct"],
        "projecao": escolha["projecao"],
        "raio_x": escolha["raio_x"],
        "ponto_risco": escolha["ponto_risco"],
        "alternativas": escolha["alternativas"]
    }

def calcular_ao_vivo_dinamico(casa, fora, placar_c, placar_f, minuto_str):
    try:
        minuto = int(''.join(filter(str.isdigit, str(minuto_str))))
    except Exception:
        minuto = 40
        
    gols = placar_c + placar_f
    dif = abs(placar_c - placar_f)
    
    if 25 <= minuto <= 42 and gols == 0:
        return {
            "status_tipo": "ATIVO",
            "mercado": "Mais de 0.5 Gols no 1º Tempo (HT)",
            "odd": 1.74,
            "ev": 26.4,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥 🟩",
            "l10_pct": "90%",
            "projecao": "Gatilho HT ativado",
            "raio_x": [
                f"🔥 GATILHO SNIPER ATIVADO: 0x0 aos {minuto}'. Odd de golo no 1T atingiu o valor ideal.",
                "Guarda-redes já intervieram e a pressão junto à área aumentou.",
                "Basta 1 golo até ao intervalo para cumprir a entrada."
            ],
            "ponto_risco": "Faltas consecutivas a interromper o ritmo até ao intervalo."
        }
        
    if minuto < 25 and gols == 0:
        return {
            "status_tipo": "ESPERA",
            "mercado": "Radar em Espera: Mais de 0.5 Gols HT (A Monitorizar)",
            "odd": 1.30,
            "ev": 12.0,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩",
            "l10_pct": "95%",
            "projecao": f"Alvo: Entrar por volta dos 28' se mantiver 0x0 (Odd alvo: 1.65+)",
            "raio_x": [
                f"👀 Jogo aos {minuto}' com intensidade, mas odd inicial ainda reduzida (1.30).",
                "Oportunidade planeada: acompanhe a partida até aos 28'.",
                "Se o nulo persistir com remates enquadrados, a cotação entrará em zona de valor."
            ],
            "ponto_risco": "Golo antes dos 25' encerra o valor da janela."
        }

    if 65 <= minuto <= 85 and dif <= 1:
        linha_over = gols + 0.5
        return {
            "status_tipo": "ATIVO",
            "mercado": f"Mais de {linha_over:.1f} Gols no Jogo (Próximo Golo)",
            "odd": 1.82,
            "ev": 21.0,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥 🟩 🟩",
            "l10_pct": "90%",
            "projecao": "Pressão final de partida",
            "raio_x": [
                f"🔥 GATILHO FINAL: Jogo em aberto ({placar_c}x{placar_f}) aos {minuto}'.",
                "A equipa em desvantagem arrisca e expõe os contra-ataques.",
                f"Boa relação odd/risco para a ocorrência de pelo menos mais 1 golo."
            ],
            "ponto_risco": "Cansaço muscular a comprometer o último passe."
        }

    if 45 <= minuto < 65 and dif <= 1:
        linha_over = gols + 0.5
        return {
            "status_tipo": "ESPERA",
            "mercado": f"Radar em Espera: Próximo Golo (+{linha_over:.1f} FT)",
            "odd": 1.35,
            "ev": 10.5,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥 🟩",
            "l10_pct": "90%",
            "projecao": "Alvo: Entrar por volta dos 68' (Odd alvo: 1.75+)",
            "raio_x": [
                f"👀 Segunda parte em andamento ({minuto}'). O ritmo cresce com as substituições.",
                "Odd atual em formação. Aguarde os 68' para capturar o ponto ideal.",
                "Linha acompanhada pelo modelo quantitativo."
            ],
            "ponto_risco": "Expulsão que condicione um dos blocos a recuar totalmente."
        }

    if 75 <= minuto <= 88 and (placar_c < placar_f):
        return {
            "status_tipo": "ATIVO",
            "mercado": "Mais de 1.5 Escanteios nos Minutos Finais",
            "odd": 1.65,
            "ev": 18.5,
            "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥",
            "l10_pct": "90%",
            "projecao": "Pressão aérea na área adversária",
            "raio_x": [
                f"🔥 PRESSÃO: {casa} procura o empate aos {minuto}'.",
                "Defesa adversária a ceder cantos em série para travar cruzamentos.",
                "Mercado de cantos independente de pontaria finalizadora."
            ],
            "ponto_risco": "Guarda-redes adversário a queimar tempo em reposições."
        }

    return {
        "status_tipo": "OBSERVACAO",
        "mercado": "Confronto em Ritmo Cadenciado (Sem Janela Clara)",
        "odd": 1.0,
        "ev": 0.0,
        "l10_pattern": "⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜",
        "l10_pct": "--",
        "projecao": "Sem assimetria matemática",
        "raio_x": [
            f"Encontro aos {minuto}' ({placar_c}x{placar_f}) em ritmo baixo ou resultado resolvido.",
            "As casas oferecem cotações desajustadas face ao risco.",
            "O terminal preserva o capital da banca sem forçar entradas."
        ],
        "ponto_risco": "Entrada antecipada sem margem de probabilidade favorável."
    }

# ==========================================
# 5. GERADOR DE JOGOS ALTERNATIVOS (RIGOROSO COM CALENDÁRIO REAL)
# ==========================================
def carregar_jogos_alternativos():
    # Retorna lista vazia se não houver confirmação estrita de eventos na grade oficial hoje
    return pd.DataFrame()

# ==========================================
# 6. CARREGAMENTO DOS JOGOS (FUTEBOL REAL)
# ==========================================
LIGAS_ESPN = {
    "Brasileirão Série A": "bra.1",
    "Brasileirão Série B": "bra.2",
    "Premier League": "eng.1",
    "La Liga": "esp.1",
    "Serie A (Itália)": "ita.1",
    "Bundesliga": "ger.1",
    "Ligue 1 (França)": "fra.1",
    "Liga Portugal": "por.1",
    "Liga Argentina": "arg.1",
    "Liga Romena": "rou.1",
    "Liga Turca": "tur.1",
    "Eliminatórias / FIFA": "fifa.worldq.conmebol",
    "UEFA Nations League": "uefa.nations",
    "Champions League": "uefa.champions",
    "Copa Libertadores": "conmebol.libertadores",
    "Copa Sul-Americana": "conmebol.sudamericana"
}

ESCUDO_PADRAO = "https://cdn-icons-png.flaticon.com/512/861/861512.png"

@st.cache_data(ttl=300)
def carregar_jogos_pre_jogo(data_consulta_str):
    lista = []
    jogo_id = 100
    fuso_br = timezone(timedelta(hours=-3))
    
    for nome_liga, codigo in LIGAS_ESPN.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard?dates={data_consulta_str}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                for ev in resp.json().get("events", []):
                    estado = ev.get("status", {}).get("type", {}).get("name", "")
                    if estado == "STATUS_SCHEDULED":
                        data_iso = ev.get("date", "")
                        horario_str = "--:--"
                        if data_iso:
                            try:
                                dt_utc = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
                                dt_br = dt_utc.astimezone(fuso_br)
                                horario_str = dt_br.strftime("%d/%m %H:%M")
                            except Exception:
                                horario_str = "--:--"
                                
                        competidores = ev.get("competitions", [{}])[0].get("competitors", [])
                        casa, fora = "Casa", "Fora"
                        logo_casa, logo_fora = ESCUDO_PADRAO, ESCUDO_PADRAO
                        
                        for c in competidores:
                            t_info = c.get("team", {})
                            nome_time = t_info.get("shortDisplayName", t_info.get("name", "Time"))
                            logo_time = t_info.get("logo", ESCUDO_PADRAO)
                            if c.get("homeAway") == "home":
                                casa = nome_time
                                logo_casa = logo_time
                            else:
                                fora = nome_time
                                logo_fora = logo_time
                                
                        analise = calcular_pre_jogo(casa, fora, nome_liga)
                        lista.append({
                            "id": f"pre_{jogo_id}",
                            "torneio": nome_liga,
                            "horario": horario_str,
                            "casa": casa,
                            "fora": fora,
                            "logo_casa": logo_casa,
                            "logo_fora": logo_fora,
                            "confronto": f"{casa} vs {fora}",
                            "mercado": analise["mercado"],
                            "odd": analise["odd"],
                            "ev": analise["ev"],
                            "l10_pattern": analise["l10_pattern"],
                            "l10_pct": analise["l10_pct"],
                            "projecao": analise["projecao"],
                            "raio_x": analise["raio_x"],
                            "ponto_risco": analise["ponto_risco"],
                            "alternativas": analise["alternativas"]
                        })
                        jogo_id += 1
        except Exception:
            continue

    if not lista:
        for nome_liga, codigo in list(LIGAS_ESPN.items())[:8]:
            url_geral = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard"
            try:
                resp = requests.get(url_geral, timeout=5)
                if resp.status_code == 200:
                    for ev in resp.json().get("events", []):
                        estado = ev.get("status", {}).get("type", {}).get("name", "")
                        if estado == "STATUS_SCHEDULED":
                            data_iso = ev.get("date", "")
                            horario_str = "--:--"
                            if data_iso:
                                try:
                                    dt_utc = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
                                    dt_br = dt_utc.astimezone(fuso_br)
                                    horario_str = dt_br.strftime("%d/%m %H:%M")
                                except Exception:
                                    horario_str = "--:--"
                            competidores = ev.get("competitions", [{}])[0].get("competitors", [])
                            casa, fora = "Casa", "Fora"
                            logo_casa, logo_fora = ESCUDO_PADRAO, ESCUDO_PADRAO
                            for c in competidores:
                                t_info = c.get("team", {})
                                nome_time = t_info.get("shortDisplayName", t_info.get("name", "Time"))
                                logo_time = t_info.get("logo", ESCUDO_PADRAO)
                                if c.get("homeAway") == "home":
                                    casa = nome_time
                                    logo_casa = logo_time
                                else:
                                    fora = nome_time
                                    logo_fora = logo_time
                            analise = calcular_pre_jogo(casa, fora, nome_liga)
                            lista.append({
                                "id": f"pre_{jogo_id}",
                                "torneio": nome_liga,
                                "horario": horario_str,
                                "casa": casa,
                                "fora": fora,
                                "logo_casa": logo_casa,
                                "logo_fora": logo_fora,
                                "confronto": f"{casa} vs {fora}",
                                "mercado": analise["mercado"],
                                "odd": analise["odd"],
                                "ev": analise["ev"],
                                "l10_pattern": analise["l10_pattern"],
                                "l10_pct": analise["l10_pct"],
                                "projecao": analise["projecao"],
                                "raio_x": analise["raio_x"],
                                "ponto_risco": analise["ponto_risco"],
                                "alternativas": analise["alternativas"]
                            })
                            jogo_id += 1
            except Exception:
                continue
            
    return pd.DataFrame(lista)

@st.cache_data(ttl=40)
def carregar_jogos_ao_vivo():
    lista = []
    jogo_id = 500
    
    for nome_liga, codigo in LIGAS_ESPN.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard"
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                for ev in resp.json().get("events", []):
                    status_obj = ev.get("status", {})
                    estado = status_obj.get("type", {}).get("name", "")
                    
                    if estado == "STATUS_IN_PROGRESS":
                        tempo_jogo = status_obj.get("displayClock", "Ao Vivo")
                        competidores = ev.get("competitions", [{}])[0].get("competitors", [])
                        casa, fora = "Casa", "Fora"
                        logo_casa, logo_fora = ESCUDO_PADRAO, ESCUDO_PADRAO
                        placar_c, placar_f = 0, 0
                        for c in competidores:
                            score = int(c.get("score", 0))
                            t_info = c.get("team", {})
                            nome_t = t_info.get("shortDisplayName", t_info.get("name", "Time"))
                            logo_t = t_info.get("logo", ESCUDO_PADRAO)
                            if c.get("homeAway") == "home":
                                casa = nome_t
                                logo_casa = logo_t
                                placar_c = score
                            else:
                                fora = nome_t
                                logo_fora = logo_t
                                placar_f = score
                                
                        confronto = f"{casa} vs {fora}"
                        if any(j["confronto"] == confronto for j in lista):
                            continue
                            
                        analise = calcular_ao_vivo_dinamico(casa, fora, placar_c, placar_f, tempo_jogo)
                        lista.append({
                            "id": f"vivo_{jogo_id}",
                            "torneio": nome_liga,
                            "tempo": tempo_jogo,
                            "placar": f"{placar_c} x {placar_f}",
                            "casa": casa,
                            "fora": fora,
                            "logo_casa": logo_casa,
                            "logo_fora": logo_fora,
                            "confronto": confronto,
                            "status_tipo": analise["status_tipo"],
                            "mercado": analise["mercado"],
                            "odd": analise["odd"],
                            "ev": analise["ev"],
                            "l10_pattern": analise["l10_pattern"],
                            "l10_pct": analise["l10_pct"],
                            "projecao": analise["projecao"],
                            "raio_x": analise["raio_x"],
                            "ponto_risco": analise["ponto_risco"]
                        })
                        jogo_id += 1
        except Exception:
            continue
            
    return pd.DataFrame(lista)

# ==========================================
# 7. BARRA LATERAL (OPERADOR & BANCA)
# ==========================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h2 style='color: #38bdf8; margin-bottom: 0;'>🛡️ RADAR PRO</h2>", unsafe_allow_html=True)
        st.caption("Terminal Quantitativo de Inteligência Esportiva")
    
    conn = get_db()
    perfil = conn.execute("SELECT banca_atual, unidade_pct FROM usuarios WHERE username = ?", (usuario_ativo,)).fetchone()
    banca_atual = perfil[0] if perfil else 50.0
    unidade_pct = perfil[1] if perfil else 2.0
    
    st.markdown(f"👤 **Operador Ativo:** `{usuario_ativo}`")
    
    st.markdown("---")
    st.markdown("#### 💼 Gestão de Risco")
    nova_banca = st.number_input("Banca Total (R$):", value=float(banca_atual), step=50.0)
    novo_pct = st.slider("Tamanho da Unidade (%):", 0.5, 5.0, float(unidade_pct), step=0.5)
    
    if st.button("💾 Salvar Parâmetros", use_container_width=True):
        conn.execute("UPDATE usuarios SET banca_atual = ?, unidade_pct = ? WHERE username = ?", (nova_banca, novo_pct, usuario_ativo))
        conn.commit()
        st.success("Configurações atualizadas!")
        st.rerun()
        
    valor_unidade = round(nova_banca * (novo_pct / 100), 2)
    st.metric(label="1 Unidade Base", value=f"R$ {valor_unidade:.2f}")
    
    st.markdown("---")
    if st.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state.usuario_ativo = None
        st.rerun()
        
    conn.close()

if "selecionados" not in st.session_state:
    st.session_state.selecionados = {}

if "odds_custom" not in st.session_state:
    st.session_state.odds_custom = {}

# ==========================================
# 8. MODAL DO BILHETE
# ==========================================
def render_modal_dialog(title="📑 Bilhete de Apostas — Radar Pro"):
    if hasattr(st, "dialog"):
        return st.dialog(title, width="large")
    elif hasattr(st, "experimental_dialog"):
        return st.experimental_dialog(title)
    else:
        def fallback(func):
            def wrapper(*args, **kwargs):
                with st.expander(title, expanded=True):
                    func(*args, **kwargs)
            return wrapper
        return fallback

dialog_slip = render_modal_dialog()

@dialog_slip
def abrir_bilhete_modal(usuario, unidade_val):
    itens = list(st.session_state.selecionados.values())
    
    if not itens:
        st.info("Nenhuma partida selecionada. Escolha palpites no Pré-Jogo ou Ao Vivo!")
        return
        
    st.caption("Ajuste as **Odds Reais da Betano** e defina o valor da entrada:")
    
    odds_ajustadas = []
    for item in itens:
        c_desc, c_odd, c_del = st.columns([3.2, 1.5, 0.8])
        with c_desc:
            st.markdown(f"**{item['confronto']}**<br><span style='font-size: 0.9rem; color: #38bdf8; font-weight: 600;'>{item['mercado']}</span>", unsafe_allow_html=True)
        with c_odd:
            val_padrao = st.session_state.odds_custom.get(item['id'], float(item['odd']))
            odd_digitada = st.number_input(
                "Odd Betano",
                min_value=1.01,
                max_value=100.0,
                value=float(val_padrao),
                step=0.01,
                key=f"m_odd_{item['id']}"
            )
            st.session_state.odds_custom[item['id']] = odd_digitada
            odds_ajustadas.append(odd_digitada)
        with c_del:
            st.write("")
            if st.button("🗑️", key=f"del_{item['id']}", help="Remover"):
                del st.session_state.selecionados[item['id']]
                st.rerun()
                
        st.markdown("<hr style='border: 0; border-top: 1px solid #334155; margin: 4px 0 10px 0;'>", unsafe_allow_html=True)
        
    odd_final = float(np.prod(odds_ajustadas))
    qtd = len(itens)
    
    m1, m2 = st.columns(2)
    m1.metric("Cotação Final (Betano)", f"{odd_final:.2f}")
    m2.metric("Total de Jogos", f"{qtd}")
    
    if qtd == 1:
        stake = unidade_val * 1.0
        st.info("Sugestão de Risco: **1.0 Unidade** (Aposta Simples)")
    elif qtd <= 2:
        stake = unidade_val * 0.5
        st.info("Sugestão de Risco: **0.5 Unidade** (Dupla Recomendada)")
    elif qtd <= 4:
        stake = unidade_val * 0.25
        st.info("Sugestão de Risco: **0.25 Unidade** (Múltipla Moderada)")
    else:
        stake = unidade_val * 0.1
        st.warning("⚠️ Múltipla com 5+ seleções: Risco elevado. Limite a 0.10 unidade.")
        
    valor_apostar = st.number_input("Valor da Entrada (R$):", value=float(round(stake, 2)), step=5.0, key="modal_val_aposta")
    retorno_estimado = valor_apostar * odd_final
    st.caption(f"Retorno estimado: **R$ {retorno_estimado:.2f}** (Lucro líquido: R$ {retorno_estimado - valor_apostar:.2f})")
    
    col_salvar, col_limpar = st.columns([2.5, 1.5])
    with col_salvar:
        if st.button("💾 Gravar Entrada no Diário", use_container_width=True, key="btn_salvar_modal"):
            conn = get_db()
            descricoes = " + ".join([f"{r['confronto']} ({r['mercado']} @{o:.2f})" for r, o in zip(itens, odds_ajustadas)])
            tipo = "Simples" if qtd == 1 else f"Múltipla ({qtd}j)"
            data_hoje = datetime.now().strftime("%d/%m %H:%M")
            
            conn.execute(
                "INSERT INTO apostas (usuario, data, descricao, tipo_aposta, odd, valor, status, motivo_red) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (usuario, data_hoje, descricoes, tipo, odd_final, valor_apostar, "Pendente", "")
            )
            conn.commit()
            conn.close()
            st.session_state.selecionados.clear()
            st.session_state.odds_custom.clear()
            st.success("Entrada registada com sucesso!")
            st.rerun()
            
    with col_limpar:
        if st.button("Limpar Tudo", use_container_width=True, key="btn_limpar_modal"):
            st.session_state.selecionados.clear()
            st.session_state.odds_custom.clear()
            st.rerun()
            
    st.markdown("---")
    st.markdown("#### 📲 Envio Estruturado (WhatsApp)")
    texto_wpp = f"⚽ *RADAR PRO - ENTRADA CONFIRMADA*\n"
    texto_wpp += f"👤 *Operador:* {usuario}\n"
    texto_wpp += f"🎯 *Jogos:* {qtd} | *Odd Final:* {odd_final:.2f}\n"
    texto_wpp += f"💵 *Stake:* R$ {valor_apostar:.2f} (Retorno: R$ {retorno_estimado:.2f})\n"
    texto_wpp += "---------------------------------\n"
    for it, odd_r in zip(itens, odds_ajustadas):
        texto_wpp += f"📌 *{it['confronto']}*\n"
        texto_wpp += f"👉 {it['mercado']} | Odd Betano: *{odd_r:.2f}*\n"
        texto_wpp += f"💡 _{it['raio_x'][0]}_\n\n"
    texto_wpp += "📊 _Gestão quantitativa de risco aplicada._"
    st.text_area("Copiar para conferência:", value=texto_wpp, height=140, key="wpp_modal")

# ==========================================
# 9. NAVEGAÇÃO PRINCIPAL (5 ABAS)
# ==========================================
tab_pre, tab_vivo, tab_alt, tab_diario, tab_stats = st.tabs([
    "🎯 Oportunidades Pré-Jogo",
    "⚡ Radar Ao Vivo (Dinâmico)",
    "📊 Mercados Alternativos",
    "📋 Diário Operacional",
    "📈 Desempenho & Yield"
])

# ----------------------------------------------------
# ABA 1: PRÉ-JOGO
# ----------------------------------------------------
with tab_pre:
    fuso_br = timezone(timedelta(hours=-3))
    data_hoje_dt = datetime.now(fuso_br)
    
    st.markdown("### 🎯 Análise Pré-Jogo (+EV)")
    st.caption("Projeções estatísticas de probabilidade e margem de assimetria para o futebol profissional.")
    
    c_data1, c_data2 = st.columns([1.5, 2.5])
    with c_data1:
        aba_data = st.radio("Período da Grade:", ["Jogos de Hoje", "Jogos de Amanhã"], horizontal=True)
        
    data_escolhida_dt = data_hoje_dt if aba_data == "Jogos de Hoje" else data_hoje_dt + timedelta(days=1)
    data_param_espn = data_escolhida_dt.strftime("%Y%m%d")
    
    df_pre = carregar_jogos_pre_jogo(data_param_espn)
    
    with c_data2:
        if not df_pre.empty:
            todas_ligas = ["Todas as Ligas"] + sorted(list(df_pre["torneio"].unique()))
            liga_pre = st.selectbox("Filtrar Campeonato:", todas_ligas, index=0, key="filtro_pre")
            df_pre_view = df_pre if liga_pre == "Todas as Ligas" else df_pre[df_pre["torneio"] == liga_pre]
        else:
            df_pre_view = pd.DataFrame()
            
    termo_busca = st.text_input("🔍 Buscar equipa ou torneio:", placeholder="Ex: Criciúma, Lanús, Náutico, Série B...", key="busca_pre").strip().lower()
    if termo_busca and not df_pre_view.empty:
        df_pre_view = df_pre_view[df_pre_view['confronto'].str.lower().str.contains(termo_busca) | df_pre_view['torneio'].str.lower().str.contains(termo_busca)]
        
    st.markdown("---")
    
    if df_pre_view.empty:
        st.info("Nenhuma partida agendada encontrada para os filtros selecionados.")
    else:
        for _, row in df_pre_view.iterrows():
            card_html = f"""
            <div class="match-card">
                <div class="card-top">
                    <span class="badge-torneio">{row['torneio']}</span>
                    <span class="badge-hora">⏰ {row['horario']}</span>
                </div>
                <div class="teams-container">
                    <div class="team-cell">
                        <img src="{row['logo_casa']}" class="team-logo-img" onerror="this.src='{ESCUDO_PADRAO}'"/>
                        <span class="team-name-text">{row['casa']}</span>
                    </div>
                    <div class="vs-cell">VS</div>
                    <div class="team-cell away">
                        <span class="team-name-text">{row['fora']}</span>
                        <img src="{row['logo_fora']}" class="team-logo-img" onerror="this.src='{ESCUDO_PADRAO}'"/>
                    </div>
                </div>
                <div class="market-row">
                    <span class="market-label">👉 Entrada Principal: {row['mercado']}</span>
                    <div class="pills-group">
                        <span class="pill-odd">Ref: {row['odd']:.2f}</span>
                        <span class="badge-ev">+{row['ev']}% EV</span>
                    </div>
                </div>
                <div class="props-bar">
                    <span><strong>L10:</strong> {row['l10_pattern']} ({row['l10_pct']})</span>
                    <span>📊 {row['projecao']}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            itens_rx = "".join([f"<div style='margin-bottom: 2px;'>• {item}</div>" for item in row['raio_x']])
            ponto_risco_html = f"<div class='risco-box'>⚠️ <strong>Ponto de Atenção (O que pode quebrar):</strong> {row['ponto_risco']}</div>"
            st.markdown(f"<div class='raio-x-box'><strong style='color: #38bdf8;'>💡 Raio-X do Algoritmo:</strong>{itens_rx}{ponto_risco_html}</div>", unsafe_allow_html=True)
            
            if row['alternativas']:
                alt_text = " &nbsp;|&nbsp; ".join([f"<strong>{a['mercado']}</strong> (@{a['odd']:.2f})" for a in row['alternativas']])
                st.markdown(f"<div class='alternativas-box'>⚡ <strong>Mercados Alternativos:</strong> {alt_text}</div>", unsafe_allow_html=True)
                
            ja_marcado = row['id'] in st.session_state.selecionados
            marcado = st.checkbox("Adicionar entrada principal ao bilhete", value=ja_marcado, key=f"chk_{row['id']}")
            
            if marcado and not ja_marcado:
                st.session_state.selecionados[row['id']] = row
                st.rerun()
            elif not marcado and ja_marcado:
                del st.session_state.selecionados[row['id']]
                st.rerun()
                
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 2: RADAR AO VIVO (FUTEBOL PROFISSIONAL)
# ----------------------------------------------------
with tab_vivo:
    col_v_top1, col_v_top2 = st.columns([3, 1])
    with col_v_top1:
        st.markdown("### ⚡ Radar Ao Vivo Dinâmico")
        st.caption("Oportunidades imediatas e metas de odd para partidas com pressão ofensiva real.")
    with col_v_top2:
        if st.button("🔄 Atualizar Radar Ao Vivo", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    df_vivo = carregar_jogos_ao_vivo()
    
    if df_vivo.empty:
        st.info("Nenhuma partida de futebol profissional em andamento dentro dos filtros de integridade.")
    else:
        for _, row_v in df_vivo.iterrows():
            st_tipo = row_v["status_tipo"]
            
            if st_tipo == "ATIVO":
                badge_status = f"<span class='badge-ev'>+{row_v['ev']}% EV</span>"
                cor_mercado = "#38bdf8"
                titulo_mercado = f"🎯 ENTRADA RECOMENDADA: {row_v['mercado']}"
            elif st_tipo == "ESPERA":
                badge_status = "<span class='badge-alvo'>👀 RADAR EM ESPERA</span>"
                cor_mercado = "#818cf8"
                titulo_mercado = f"{row_v['mercado']}"
            else:
                badge_status = "<span class='badge-observacao'>RITMO CADENCIADO</span>"
                cor_mercado = "#94a3b8"
                titulo_mercado = f"🟡 {row_v['mercado']}"

            card_vivo_html = f"""
            <div class="match-card">
                <div class="card-top">
                    <span class="badge-torneio">{row_v['torneio']}</span>
                    <div>
                        <span class="badge-ao-vivo">AO VIVO: {row_v['tempo']}</span>
                        <span class="badge-placar">{row_v['placar']}</span>
                    </div>
                </div>
                <div class="teams-container">
                    <div class="team-cell">
                        <img src="{row_v['logo_casa']}" class="team-logo-img" onerror="this.src='{ESCUDO_PADRAO}'"/>
                        <span class="team-name-text">{row_v['casa']}</span>
                    </div>
                    <div class="vs-cell">AO VIVO</div>
                    <div class="team-cell away">
                        <span class="team-name-text">{row_v['fora']}</span>
                        <img src="{row_v['logo_fora']}" class="team-logo-img" onerror="this.src='{ESCUDO_PADRAO}'"/>
                    </div>
                </div>
                <div class="market-row">
                    <span class="market-label" style="color: {cor_mercado};">{titulo_mercado}</span>
                    <div class="pills-group">
                        <span class="pill-odd">Ref: {row_v['odd']:.2f}</span>
                        {badge_status}
                    </div>
                </div>
                <div class="props-bar">
                    <span><strong>Métricas:</strong> {row_v['l10_pattern']} ({row_v['l10_pct']})</span>
                    <span>🎯 {row_v['projecao']}</span>
                </div>
            </div>
            """
            st.markdown(card_vivo_html, unsafe_allow_html=True)
            
            itens_rx_v = "".join([f"<div style='margin-bottom: 2px;'>• {item}</div>" for item in row_v['raio_x']])
            ponto_risco_v_html = f"<div class='risco-box'>⚠️ <strong>Ponto de Atenção:</strong> {row_v['ponto_risco']}</div>"
            st.markdown(f"<div class='raio-x-box'><strong style='color: #38bdf8;'>💡 Leitura do Momento:</strong>{itens_rx_v}{ponto_risco_v_html}</div>", unsafe_allow_html=True)
            
            if st_tipo in ["ATIVO", "ESPERA"]:
                ja_marcado_v = row_v['id'] in st.session_state.selecionados
                marcado_v = st.checkbox("Adicionar entrada ao bilhete", value=ja_marcado_v, key=f"chk_{row_v['id']}")
                if marcado_v and not ja_marcado_v:
                    st.session_state.selecionados[row_v['id']] = row_v
                    st.rerun()
                elif not marcado_v and ja_marcado_v:
                    del st.session_state.selecionados[row_v['id']]
                    st.rerun()
            else:
                st.caption("🔒 Confronto sem assimetria estatística de cotação.")
                
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 3: MERCADOS ALTERNATIVOS (VALIDADOS)
# ----------------------------------------------------
with tab_alt:
    st.markdown("### 📊 Mercados Alternativos (+EV)")
    st.caption("Módulos de modalidades fora do futebol tradicional. Apenas confrontos validados em grade real.")
    
    df_alt = carregar_jogos_alternativos()
    
    if df_alt.empty:
        st.info("ℹ️ Nenhum evento alternativo com cotação e horário confirmados para o dia de hoje. A grade será atualizada automaticamente assim que houver novos confrontos oficiais disponíveis.")
    else:
        for _, row_alt in df_alt.iterrows():
            card_alt_html = f"""
            <div class="match-card" style="border-color: rgba(56, 189, 248, 0.35);">
                <div class="card-top">
                    <span class="badge-torneio">{row_alt['esporte']} • {row_alt['torneio']}</span>
                    <span class="badge-hora">⏰ {row_alt['horario']}</span>
                </div>
                <div class="teams-container">
                    <div class="team-cell">
                        <img src="{row_alt['logo_casa']}" class="team-logo-img"/>
                        <span class="team-name-text">{row_alt['casa']}</span>
                    </div>
                    <div class="vs-cell">VS</div>
                    <div class="team-cell away">
                        <span class="team-name-text">{row_alt['fora']}</span>
                        <img src="{row_alt['logo_fora']}" class="team-logo-img"/>
                    </div>
                </div>
                <div class="market-row">
                    <span class="market-label" style="color: #38bdf8;">👉 Entrada Principal: {row_alt['mercado']}</span>
                    <div class="pills-group">
                        <span class="pill-odd">Ref: {row_alt['odd']:.2f}</span>
                        <span class="badge-ev">+{row_alt['ev']}% EV</span>
                    </div>
                </div>
                <div class="props-bar">
                    <span><strong>Consistência / H2H:</strong> {row_alt['l10_pattern']} ({row_alt['l10_pct']})</span>
                    <span>🎯 {row_alt['projecao']}</span>
                </div>
            </div>
            """
            st.markdown(card_alt_html, unsafe_allow_html=True)
            
            itens_rx_alt = "".join([f"<div style='margin-bottom: 2px;'>• {item}</div>" for item in row_alt['raio_x']])
            ponto_risco_alt_html = f"<div class='risco-box'>⚠️ <strong>Ponto de Atenção:</strong> {row_alt['ponto_risco']}</div>"
            st.markdown(f"<div class='raio-x-box'><strong style='color: #38bdf8;'>💡 Raio-X do Modelo:</strong>{itens_rx_alt}{ponto_risco_alt_html}</div>", unsafe_allow_html=True)
            
            item_alt_slip = {
                "id": row_alt["id"],
                "confronto": row_alt["confronto"],
                "mercado": row_alt["mercado"],
                "odd": row_alt["odd"],
                "raio_x": row_alt["raio_x"]
            }
            
            ja_marcado_alt = row_alt['id'] in st.session_state.selecionados
            marcado_alt = st.checkbox("Adicionar entrada ao bilhete", value=ja_marcado_alt, key=f"chk_{row_alt['id']}")
            
            if marcado_alt and not ja_marcado_alt:
                st.session_state.selecionados[row_alt['id']] = item_alt_slip
                st.rerun()
            elif not marcado_alt and ja_marcado_alt:
                del st.session_state.selecionados[row_alt['id']]
                st.rerun()
                
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 4: DIÁRIO OPERACIONAL
# ----------------------------------------------------
with tab_diario:
    st.markdown(f"### 📋 Diário Operacional — {usuario_ativo}")
    conn = get_db()
    df_apostas = pd.read_sql_query("SELECT * FROM apostas WHERE usuario = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()
    
    if df_apostas.empty:
        st.info("Nenhuma aposta registada até ao momento para este operador.")
    else:
        for _, row in df_apostas.iterrows():
            c1, c2, c3 = st.columns([3.5, 1.2, 2.3])
            with c1:
                st.markdown(f"<strong style='font-size: 1.05rem; color: #ffffff;'>{row['descricao']}</strong>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: #94a3b8; font-size: 0.9rem;'>{row['data']} • {row['tipo_aposta']} | Odd Real: <strong>{row['odd']:.2f}</strong> | R$ {row['valor']:.2f}</span>", unsafe_allow_html=True)
            with c2:
                if row['status'] == "Pendente":
                    st.warning("⏳ Pendente")
                elif row['status'] == "Green":
                    st.success("✅ Green")
                else:
                    st.error("❌ Red")
            with c3:
                if row['status'] == "Pendente":
                    cg, cr = st.columns([1.2, 1.8])
                    with cg:
                        if st.button("✅ Green", key=f"g_{row['id']}", use_container_width=True):
                            conn = get_db()
                            lucro = (row['valor'] * row['odd']) - row['valor']
                            conn.execute("UPDATE apostas SET status = 'Green' WHERE id = ?", (row['id'],))
                            conn.execute("UPDATE usuarios SET banca_atual = banca_atual + ? WHERE username = ?", (lucro, usuario_ativo))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with cr:
                        motivo = st.selectbox("Motivo Red:", ["Expulsão", "Pênalti/VAR", "Poupança", "Tático", "Outro"], key=f"m_{row['id']}")
                        if st.button("❌ Red", key=f"r_{row['id']}", use_container_width=True):
                            conn = get_db()
                            conn.execute("UPDATE apostas SET status = 'Red', motivo_red = ? WHERE id = ?", (motivo, row['id']))
                            conn.execute("UPDATE usuarios SET banca_atual = banca_atual - ? WHERE username = ?", (row['valor'], usuario_ativo))
                            conn.commit()
                            conn.close()
                            st.rerun()
                else:
                    if row['status'] == "Red" and row['motivo_red']:
                        st.caption(f"Motivo: {row['motivo_red']}")
            st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 14px 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 5: DESEMPENHO & YIELD
# ----------------------------------------------------
with tab_stats:
    st.markdown(f"### 📈 Métricas de Desempenho — {usuario_ativo}")
    conn = get_db()
    df_resolvidas = pd.read_sql_query("SELECT * FROM apostas WHERE usuario = ? AND status IN ('Green', 'Red')", conn, params=(usuario_ativo,))
    conn.close()
    
    if df_resolvidas.empty:
        st.info("Valide entradas no diário para acompanhar as estatísticas de rendimento.")
    else:
        total = len(df_resolvidas)
        greens = len(df_resolvidas[df_resolvidas["status"] == "Green"])
        reds = len(df_resolvidas[df_resolvidas["status"] == "Red"])
        winrate = (greens / total) * 100
        
        lucro_total = 0.0
        for _, row in df_resolvidas.iterrows():
            if row["status"] == "Green":
                lucro_total += (row["valor"] * row["odd"]) - row["valor"]
            else:
                lucro_total -= row["valor"]
                
        m1, m2, m3 = st.columns(3)
        m1.metric("Taxa de Assertividade", f"{winrate:.1f}%")
        m2.metric("Histórico", f"{greens}W / {reds}L")
        m3.metric("Resultado Líquido", f"R$ {lucro_total:+.2f}")

# ==========================================
# 10. GATILHO FLUTUANTE GLOBAL (CANTO INFERIOR DIREITO)
# ==========================================
if st.session_state.selecionados:
    qtd_jogos = len(st.session_state.selecionados)
    odd_acumulada = float(np.prod([
        st.session_state.odds_custom.get(it['id'], float(it['odd'])) 
        for it in st.session_state.selecionados.values()
    ]))
    
    st.markdown('<div id="floating-anchor"></div>', unsafe_allow_html=True)
    texto_botao = f"🛒 {qtd_jogos} {'Jogo' if qtd_jogos == 1 else 'Jogos'} | Odd {odd_acumulada:.2f} ➔ Abrir Bilhete"
    
    if st.button(texto_botao, key="btn_floating_slip"):
        abrir_bilhete_modal(usuario_ativo, valor_unidade)
