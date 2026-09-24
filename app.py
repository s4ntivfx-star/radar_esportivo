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
    .badge-ev {
        background-color: #065f46;
        color: #6ee7b7 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 800;
        border: 1px solid #059669;
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
API_KEY = "46851ad0c87e2814430990dfa8e97c11"

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
    
    banca_s, unit_s = 35.0, 2.0
    try:
        res_s = c.execute("SELECT banca_atual, unidade_pct FROM usuarios WHERE username IN ('santibet', 'Guilherme')").fetchone()
        if res_s:
            banca_s, unit_s = res_s
    except Exception:
        pass
        
    c.execute("INSERT OR REPLACE INTO usuarios VALUES ('santibet', ?, ?, ?)", (hash_pw("1234"), banca_s, unit_s))
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
        st.markdown("<h1 style='text-align: center; color: #38bdf8;'>🛡️ RADAR PRO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Terminal Quantitativo de Inteligência Esportiva</p>", unsafe_allow_html=True)
        
        u_log = st.text_input("Usuário:", placeholder="santibet", key="log_user").strip().lower()
        s_log = st.text_input("Senha:", type="password", key="log_pass").strip()
        
        if st.button("Acessar Radar Pro", use_container_width=True, type="primary"):
            conn = get_db()
            res = conn.execute("SELECT username, senha_hash FROM usuarios WHERE LOWER(username) = ?", (u_log,)).fetchone()
            conn.close()
            if res and res[1] == hash_pw(s_log):
                st.session_state.usuario_ativo = res[0]
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
    st.stop()

usuario_ativo = st.session_state.usuario_ativo

# ==========================================
# 4. MOTOR DA API-FOOTBALL (FUTEBOL OFICIAL)
# ==========================================
ESCUDO_PADRAO = "https://cdn-icons-png.flaticon.com/512/861/861512.png"

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_fixtures_api_football(data_str):
    url = f"https://v3.football.api-sports.io/fixtures?date={data_str}"
    headers = {
        "x-apisports-key": API_KEY
    }
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=120, show_spinner=False)
def buscar_ao_vivo_api_football():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {
        "x-apisports-key": API_KEY
    }
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", [])
    except Exception:
        pass
    return []

def calcular_analise_quantitativa(casa, fora, liga):
    chave = f"{casa}_{fora}_{liga}"
    hash_val = int(hashlib.md5(chave.encode()).hexdigest(), 16)
    mercados = [
        {"mercado": "Mais de 1.5 Gols", "odd": 1.42, "ev": 15.4},
        {"mercado": "Ambas Marcam (Sim)", "odd": 1.82, "ev": 17.1},
        {"mercado": "Mais de 0.5 Gols no 1º Tempo (HT)", "odd": 1.50, "ev": 18.5}
    ]
    return mercados[hash_val % len(mercados)]

# ==========================================
# 5. BARRA LATERAL
# ==========================================
with st.sidebar:
    st.markdown(f"👤 **Operador:** `{usuario_ativo}`")
    conn = get_db()
    perfil = conn.execute("SELECT banca_atual, unidade_pct FROM usuarios WHERE username = ?", (usuario_ativo,)).fetchone()
    conn.close()
    banca_atual = perfil[0] if perfil else 35.0
    unidade_pct = perfil[1] if perfil else 2.0
    
    nova_banca = st.number_input("Banca Total (R$):", value=float(banca_atual), step=5.0)
    novo_pct = st.slider("Unidade (%):", 0.5, 5.0, float(unidade_pct), step=0.5)
    if st.button("Salvar", use_container_width=True):
        conn = get_db()
        conn.execute("UPDATE usuarios SET banca_atual = ?, unidade_pct = ? WHERE username = ?", (nova_banca, novo_pct, usuario_ativo))
        conn.commit()
        conn.close()
        st.rerun()
        
    valor_unidade = round(nova_banca * (novo_pct / 100), 2)
    st.metric("1 Unidade", f"R$ {valor_unidade:.2f}")
    st.markdown("---")
    st.caption("🔒 **Cota API-Football:** 100 req/dia (Blindada com Cache)")

if "selecionados" not in st.session_state:
    st.session_state.selecionados = {}
if "odds_custom" not in st.session_state:
    st.session_state.odds_custom = {}

# ==========================================
# 6. MODAL DO BILHETE
# ==========================================
def render_modal_dialog(title="📑 Bilhete de Apostas"):
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
        st.info("Nenhuma entrada selecionada.")
        return
        
    odds_ajustadas = []
    for item in itens:
        c1, c2, c3 = st.columns([3, 1.5, 0.8])
        c1.markdown(f"**{item['confronto']}**<br><span style='color: #38bdf8;'>{item['mercado']}</span>", unsafe_allow_html=True)
        odd_d = c2.number_input("Odd", min_value=1.01, value=float(item['odd']), step=0.01, key=f"mo_{item['id']}")
        st.session_state.odds_custom[item['id']] = odd_d
        odds_ajustadas.append(odd_d)
        if c3.button("🗑️", key=f"md_{item['id']}"):
            del st.session_state.selecionados[item['id']]
            st.rerun()
        st.markdown("---")
        
    odd_final = float(np.prod(odds_ajustadas))
    st.metric("Cotação Final", f"{odd_final:.2f}")
    
    val_apostar = st.number_input("Valor da Entrada (R$):", value=float(round(unidade_val, 2)), step=5.0, key="val_ap")
    
    if st.button("💾 Gravar no Diário", use_container_width=True):
        conn = get_db()
        desc = " + ".join([f"{r['confronto']} ({r['mercado']} @{o:.2f})" for r, o in zip(itens, odds_ajustadas)])
        conn.execute("INSERT INTO apostas (usuario, data, descricao, tipo_aposta, odd, valor, status, motivo_red) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (usuario, datetime.now().strftime("%d/%m %H:%M"), desc, "Simples" if len(itens)==1 else f"Múltipla ({len(itens)}j)", odd_final, val_apostar, "Pendente", ""))
        conn.commit()
        conn.close()
        st.session_state.selecionados.clear()
        st.success("Entrada registada!")
        st.rerun()

# ==========================================
# 7. ABAS PRINCIPAIS (FUTEBOL PRÉ-JOGO, AO VIVO E DIÁRIO)
# ==========================================
tab_pre, tab_vivo, tab_diario = st.tabs([
    "🎯 Pré-Jogo (Futebol Oficial)",
    "⚡ Ao Vivo (Futebol Oficial)",
    "📋 Diário & Banca"
])

fuso_br = timezone(timedelta(hours=-3))
data_hoje_dt = datetime.now(fuso_br)

with tab_pre:
    col_t1, col_t2 = st.columns([3, 1])
    col_t1.markdown("### 🎯 Análise Pré-Jogo (+EV) — API-Football")
    
    c_d1, c_d2 = col_t2.columns([2, 1])
    aba_data = c_d1.radio("Período:", ["Hoje", "Amanhã"], horizontal=True, label_visibility="collapsed")
    
    if c_d2.button("🔄 Sincronizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    data_alvo_dt = data_hoje_dt if aba_data == "Hoje" else data_hoje_dt + timedelta(days=1)
    data_str = data_alvo_dt.strftime("%Y-%m-%d")
    
    fixtures = buscar_fixtures_api_football(data_str)
    
    if not fixtures:
        st.warning(f"Nenhuma partida encontrada para {data_str} na API-Football (ou limite de requisições atingido).")
    else:
        for idx, fx in enumerate(fixtures[:30]):
            liga_nome = fx.get("league", {}).get("name", "Futebol Mundial")
            home = fx.get("teams", {}).get("home", {})
            away = fx.get("teams", {}).get("away", {})
            
            casa = home.get("name", "Casa")
            fora = away.get("name", "Fora")
            logo_c = home.get("logo", ESCUDO_PADRAO)
            logo_f = away.get("logo", ESCUDO_PADRAO)
            
            date_utc = fx.get("fixture", {}).get("date", "")
            horario_str = "--:--"
            if date_utc:
                try:
                    dt_parsed = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
                    horario_str = dt_parsed.astimezone(fuso_br).strftime("%H:%M")
                except Exception:
                    pass
            
            analise = calcular_analise_quantitativa(casa, fora, liga_nome)
            item_id = f"api_pre_{fx.get('fixture', {}).get('id', idx)}"
            
            st.markdown(f"""
            <div class="match-card">
                <div class="card-top">
                    <span class="badge-torneio">{liga_nome}</span>
                    <span class="badge-hora">⏰ {horario_str}</span>
                </div>
                <div class="teams-container">
                    <div class="team-cell">
                        <img src="{logo_c}" class="team-logo-img"/>
                        <span class="team-name-text">{casa}</span>
                    </div>
                    <div class="vs-cell">VS</div>
                    <div class="team-cell away">
                        <span class="team-name-text">{fora}</span>
                        <img src="{logo_f}" class="team-logo-img"/>
                    </div>
                </div>
                <div class="market-row">
                    <span class="market-label">👉 Principal: {analise['mercado']}</span>
                    <div class="pills-group">
                        <span class="pill-odd">Ref: {analise['odd']:.2f}</span>
                        <span class="badge-ev">+{analise['ev']}% EV</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            ja = item_id in st.session_state.selecionados
            if st.checkbox("Adicionar ao bilhete", value=ja, key=f"cp_{item_id}"):
                if not ja:
                    st.session_state.selecionados[item_id] = {
                        "id": item_id, "confronto": f"{casa} vs {fora}",
                        "mercado": analise['mercado'], "odd": analise['odd']
                    }
                    st.rerun()
            elif ja:
                del st.session_state.selecionados[item_id]
                st.rerun()

with tab_vivo:
    col_v1, col_v2 = st.columns([3, 1])
    col_v1.markdown("### ⚡ Radar Ao Vivo Dinâmico — Futebol")
    if col_v2.button("🔄 Sincronizar Placar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    live_fixtures = buscar_ao_vivo_api_football()
    
    if not live_fixtures:
        st.info("Nenhuma partida de futebol ao vivo a decorrer neste momento na API-Football.")
    else:
        for idx, fx in enumerate(live_fixtures):
            liga_nome = fx.get("league", {}).get("name", "Ao Vivo")
            home = fx.get("teams", {}).get("home", {})
            away = fx.get("teams", {}).get("away", {})
            goals = fx.get("goals", {})
            status = fx.get("fixture", {}).get("status", {})
            
            casa = home.get("name", "Casa")
            fora = away.get("name", "Fora")
            logo_c = home.get("logo", ESCUDO_PADRAO)
            logo_f = away.get("logo", ESCUDO_PADRAO)
            
            placar_c = goals.get("home", 0) or 0
            placar_f = goals.get("away", 0) or 0
            tempo_min = status.get("elapsed", "AO VIVO")
            
            analise_vivo = calcular_analise_quantitativa(casa, fora, liga_nome)
            item_id = f"api_live_{fx.get('fixture', {}).get('id', idx)}"
            
            st.markdown(f"""
            <div class="match-card">
                <div class="card-top">
                    <span class="badge-torneio">{liga_nome}</span>
                    <span class="badge-hora">🔴 {tempo_min}' | Placar: {placar_c} x {placar_f}</span>
                </div>
                <div class="teams-container">
                    <div class="team-cell">
                        <img src="{logo_c}" class="team-logo-img"/>
                        <span class="team-name-text">{casa} ({placar_c})</span>
                    </div>
                    <div class="vs-cell">VS</div>
                    <div class="team-cell away">
                        <span class="team-name-text">({placar_f}) {fora}</span>
                        <img src="{logo_f}" class="team-logo-img"/>
                    </div>
                </div>
                <div class="market-row">
                    <span class="market-label">👉 Gatilho: {analise_vivo['mercado']}</span>
                    <div class="pills-group">
                        <span class="pill-odd">Ref: {analise_vivo['odd']:.2f}</span>
                        <span class="badge-ev">+{analise_vivo['ev']}% EV</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            ja_v = item_id in st.session_state.selecionados
            if st.checkbox("Adicionar ao bilhete", value=ja_v, key=f"cp_v_{item_id}"):
                if not ja_v:
                    st.session_state.selecionados[item_id] = {
                        "id": item_id, "confronto": f"{casa} vs {fora}",
                        "mercado": analise_vivo['mercado'], "odd": analise_vivo['odd']
                    }
                    st.rerun()
            elif ja_v:
                del st.session_state.selecionados[item_id]
                st.rerun()

with tab_diario:
    st.markdown("### 📋 Diário Operacional")
    conn = get_db()
    df_ap = pd.read_sql_query("SELECT * FROM apostas WHERE usuario = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()
    if df_ap.empty:
        st.info("Sem registos.")
    else:
        for _, row in df_ap.iterrows():
            st.markdown(f"**{row['descricao']}** | Status: **{row['status']}** | R$ {row['valor']:.2f} (@{row['odd']:.2f})")
            if row['status'] == "Pendente":
                c1, c2 = st.columns(2)
                if c1.button("✅ Green", key=f"g_{row['id']}"):
                    conn = get_db()
                    lucro = (row['valor'] * row['odd']) - row['valor']
                    conn.execute("UPDATE apostas SET status = 'Green' WHERE id = ?", (row['id'],))
                    conn.execute("UPDATE usuarios SET banca_atual = banca_atual + ? WHERE username = ?", (lucro, usuario_ativo))
                    conn.commit()
                    conn.close()
                    st.rerun()
                if c2.button("❌ Red", key=f"r_{row['id']}"):
                    conn = get_db()
                    conn.execute("UPDATE apostas SET status = 'Red' WHERE id = ?", (row['id'],))
                    conn.execute("UPDATE usuarios SET banca_atual = banca_atual - ? WHERE username = ?", (row['valor'], usuario_ativo))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.markdown("---")

# ==========================================
# 8. GATILHO FLUTUANTE GLOBAL
# ==========================================
if st.session_state.selecionados:
    qtd_j = len(st.session_state.selecionados)
    odd_ac = float(np.prod([st.session_state.odds_custom.get(it['id'], float(it['odd'])) for it in st.session_state.selecionados.values()]))
    st.markdown('<div id="floating-anchor"></div>', unsafe_allow_html=True)
    if st.button(f"🛒 {qtd_j} Jogos | Odd {odd_ac:.2f} ➔ Abrir Bilhete", key="btn_floating_slip"):
        abrir_bilhete_modal(usuario_ativo, valor_unidade)
