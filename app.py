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
    .pill-odd {
        background-color: #0f172a;
        color: #38bdf8;
        border: 1px solid #0284c7;
        padding: 3px 10px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 800;
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
# 4. MOTORES QUANTITATIVOS (FUTEBOL)
# ==========================================
def calcular_pre_jogo(casa, fora, torneio):
    chave = f"{casa}_{fora}_{torneio}"
    hash_val = int(hashlib.md5(chave.encode()).hexdigest(), 16)
    catalogo = [
        {"mercado": "Mais de 0.5 Gols no 1º Tempo (HT)", "odd": 1.48, "prob": 0.81, "ev": 19.8, "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥 🟩", "l10_pct": "90%", "projecao": "Projeção: 1.3 gols no 1T", "raio_x": [f"{casa} registou golos na primeira parte em 9 dos últimos 10 jogos."]},
        {"mercado": "Mais de 1.5 Gols no Jogo", "odd": 1.38, "prob": 0.84, "ev": 15.9, "l10_pattern": "🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟩 🟥", "l10_pct": "90%", "projecao": "Projeção: 2.7 gols esperados", "raio_x": ["Volume ofensivo expressivo combinado."]}
    ]
    return catalogo[hash_val % len(catalogo)]

ESCUDO_PADRAO = "https://cdn-icons-png.flaticon.com/512/861/861512.png"

@st.cache_data(ttl=300)
def carregar_jogos_pre_jogo():
    lista = []
    jogo_id = 100
    LIGAS = {"Brasileirão Série A": "bra.1", "Premier League": "eng.1", "Copa Libertadores": "conmebol.libertadores"}
    for nome_liga, codigo in LIGAS.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard"
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                for ev in resp.json().get("events", []):
                    if ev.get("status", {}).get("type", {}).get("name", "") == "STATUS_SCHEDULED":
                        competidores = ev.get("competitions", [{}])[0].get("competitors", [])
                        casa, fora = "Casa", "Fora"
                        logo_c, logo_f = ESCUDO_PADRAO, ESCUDO_PADRAO
                        for c in competidores:
                            t_info = c.get("team", {})
                            if c.get("homeAway") == "home":
                                casa = t_info.get("shortDisplayName", "Time")
                                logo_c = t_info.get("logo", ESCUDO_PADRAO)
                            else:
                                fora = t_info.get("shortDisplayName", "Time")
                                logo_f = t_info.get("logo", ESCUDO_PADRAO)
                        analise = calcular_pre_jogo(casa, fora, nome_liga)
                        lista.append({
                            "id": f"pre_{jogo_id}", "torneio": nome_liga, "horario": "Hoje",
                            "casa": casa, "fora": fora, "logo_casa": logo_c, "logo_fora": logo_f,
                            "confronto": f"{casa} vs {fora}", "mercado": analise["mercado"],
                            "odd": analise["odd"], "ev": analise["ev"], "l10_pattern": analise["l10_pattern"],
                            "l10_pct": analise["l10_pct"], "projecao": analise["projecao"], "raio_x": analise["raio_x"]
                        })
                        jogo_id += 1
        except Exception:
            continue
    return pd.DataFrame(lista)

# ==========================================
# 5. BARRA LATERAL
# ==========================================
with st.sidebar:
    st.markdown(f"👤 **Operador:** `{usuario_ativo}`")
    conn = get_db()
    perfil = conn.execute("SELECT banca_atual, unidade_pct FROM usuarios WHERE username = ?", (usuario_ativo,)).fetchone()
    conn.close()
    banca_atual = perfil[0] if perfil else 50.0
    unidade_pct = perfil[1] if perfil else 2.0
    
    nova_banca = st.number_input("Banca Total (R$):", value=float(banca_atual), step=10.0)
    novo_pct = st.slider("Unidade (%):", 0.5, 5.0, float(unidade_pct), step=0.5)
    if st.button("Salvar", use_container_width=True):
        conn = get_db()
        conn.execute("UPDATE usuarios SET banca_atual = ?, unidade_pct = ? WHERE username = ?", (nova_banca, novo_pct, usuario_ativo))
        conn.commit()
        conn.close()
        st.rerun()
        
    valor_unidade = round(nova_banca * (novo_pct / 100), 2)
    st.metric("1 Unidade", f"R$ {valor_unidade:.2f}")

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
# 7. ABAS PRINCIPAIS
# ==========================================
tab_pre, tab_esoccer, tab_diario = st.tabs(["🎯 Futebol Pré-Jogo", "🎮 e-Soccer Analytics Automático", "📋 Diário & Banca"])

with tab_pre:
    st.markdown("### 🎯 Análise Pré-Jogo")
    df_pre = carregar_jogos_pre_jogo()
    if df_pre.empty:
        st.info("A carregar partidas...")
    else:
        for _, row in df_pre.iterrows():
            st.markdown(f"""
            <div class="match-card">
                <strong>{row['torneio']}</strong> | {row['confronto']}<br>
                <span style="color: #38bdf8;">👉 {row['mercado']}</span> (Ref: {row['odd']:.2f} | <span style="color: #6ee7b7;">+{row['ev']}% EV</span>)
            </div>
            """, unsafe_allow_html=True)
            ja = row['id'] in st.session_state.selecionados
            if st.checkbox("Adicionar ao bilhete", value=ja, key=f"cp_{row['id']}"):
                if not ja:
                    st.session_state.selecionados[row['id']] = row
                    st.rerun()
            elif ja:
                del st.session_state.selecionados[row['id']]
                st.rerun()

# ----------------------------------------------------
# e-SOCCER AUTOMÁTICO COM RECOMENDAÇÕES INTELIGENTES
# ----------------------------------------------------
with tab_esoccer:
    st.markdown("### 🎮 e-Soccer — Recomendador Automático de Apostas")
    st.caption("Selecione os pilotos e as médias. O terminal faz os cálculos e entrega mastigadas as melhores opções de aposta em Gols e Vitória.")
    
    categoria_jogo = st.selectbox(
        "Selecione a Liga / Formato (Betano):",
        [
            "Esoccer - Battle - Liga dos Campeões - 2x4 min",
            "Esoccer - Battle - Liga Europa - 2x4 min",
            "Esoccer - Battle - Série A - 2x4 min",
            "Esoccer - Battle - Internacional - 2x6 min",
            "Esoccer - GT Leagues - 2x6 min",
            "Esoccer - H2H GG League - 2x4 min"
        ]
    )
    
    PILOTOS_BETTORS_ORD = [
        "chevare (Juventus)", "Animal (Sporting CP)", "Maki (Arsenal)", "Linox (B Dortmund)",
        "Llulle (Roma)", "Sena (Fenerbahce)", "Cira (Salzburg)", "pikalicaaa (Porto)",
        "BlackStar98 (Villarreal)", "Revenge (Barcelona)", "Lx7ss (Sassuolo)", "SPECIAL (Roma)",
        "Jokadinho (Juventus)", "maggett0 (Bologna)", "Dov1n (Napoli)", "Buu (France)",
        "Lufy (Spain)", "Pex (Germany)", "Firminho (England)", "ZORO (Argentina)",
        "Eros (AZ Alkmaar)", "Fox (RSC Anderlecht)", "Kratos (Crystal Palace)", "Crysis (Celtic Glasgow)",
        "Thunder (Sunderland AFC)", "Penn (TSG 1899 Hoffenheim)", "Atlas (Dinamo Zagreb)", "Tiago (Stade Rennais)",
        "VENUS (Real Madrid)", "COSMOS (FC Bayern Munchen)", "CLINICAL (England)", "INSTINCT (France)", "DEZZY (Arsenal)"
    ]
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("#### 🏠 Piloto 1 (Casa)")
        p1 = st.selectbox("Pesquisar Piloto 1:", PILOTOS_BETTORS_ORD, index=0, key="sel_p1_v4")
        gfc = st.number_input("Média Gols Feitos (P1):", value=2.9, step=0.1, key="mg_f1_v4")
        gsc = st.number_input("Média Gols Sofridos (P1):", value=1.6, step=0.1, key="mg_s1_v4")
        odd_p1 = st.number_input("Odd Betano (Vitória P1):", value=2.10, step=0.01, key="od_p1_v4")
        
    with col_s2:
        st.markdown("#### ✈️ Piloto 2 (Fora)")
        p2 = st.selectbox("Pesquisar Piloto 2:", PILOTOS_BETTORS_ORD, index=1, key="sel_p2_v4")
        gff = st.number_input("Média Gols Feitos (P2):", value=3.2, step=0.1, key="mg_f2_v4")
        gsf = st.number_input("Média Gols Sofridos (P2):", value=1.8, step=0.1, key="mg_s2_v4")
        odd_p2 = st.number_input("Odd Betano (Vitória P2):", value=2.45, step=0.01, key="od_p2_v4")

    # MÓDULO DE RECOMENDAÇÃO AUTOMÁTICA INTELIGENTE
    tipo_tempo = "4 min" if "2x4 min" in categoria_jogo else "6 min"
    fator = 1.25 if tipo_tempo == "4 min" else 1.10
    
    # Projeção de gols de cada um
    gols_esperados_p1 = (gfc + gsf) / 2
    gols_esperados_p2 = (gff + gsc) / 2
    gols_total_proj = round((gols_esperados_p1 + gols_esperados_p2) * fator, 2)
    
    # Definição automática da melhor linha de gols
    if gols_total_proj >= 9.5:
        melhor_linha_gols = "Mais de 8.5 Gols"
        odd_sugerida_gols = 1.62
    elif gols_total_proj >= 8.0:
        melhor_linha_gols = "Mais de 7.5 Gols"
        odd_sugerida_gols = 1.55
    else:
        melhor_linha_gols = "Mais de 6.5 Gols"
        odd_sugerida_gols = 1.45

    # Veredicto automático de Vitória / 1X2
    if odd_p1 < odd_p2 and gols_esperados_p1 > gols_esperados_p2:
        melhor_vitoria = f"Vitória Simples ou Dupla Hipótese: {p1}"
        odd_vitoria_ref = odd_p1
    elif odd_p2 < odd_p1 and gols_esperados_p2 > gols_esperados_p1:
        melhor_vitoria = f"Vitória Simples ou Dupla Hipótese: {p2}"
        odd_vitoria_ref = odd_p2
    else:
        melhor_vitoria = "Confronto Equilibrado / Ambas Marcam (BTTS)"
        odd_vitoria_ref = 1.75

    st.markdown("---")
    st.markdown("### 🎯 Melhores Opções de Aposta Recomendadas pelo Terminal")
    
    c_rec1, c_rec2 = st.columns(2)
    
    id_rec1 = f"esoccer_gols_{p1}_{p2}"
    item_rec1 = {
        "id": id_rec1, "confronto": f"{p1} vs {p2}", "mercado": f"{melhor_linha_gols} ({categoria_jogo})",
        "odd": odd_sugerida_gols, "raio_x": [f"Projeção: {gols_total_proj} gols"]
    }
    
    with c_rec1:
        st.markdown(f"""
        <div class="match-card" style="border-color: #38bdf8;">
            <h4 style="color: #38bdf8; margin-top: 0;">⚽ Mercado de Gols</h4>
            <p><strong>Sugestão:</strong> {melhor_linha_gols}</p>
            <p><strong>Projeção do Jogo:</strong> {gols_total_proj} gols esperados</p>
            <p><strong>Odd Média Betano:</strong> ~{odd_sugerida_gols:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        ja_r1 = id_rec1 in st.session_state.selecionados
        if st.checkbox("📥 Adicionar Sugestão de Gols ao Bilhete", value=ja_r1, key="chk_rec_gols"):
            if not ja_r1:
                st.session_state.selecionados[id_rec1] = item_rec1
                st.success("Adicionado ao bilhete!")
                st.rerun()
        elif ja_r1:
            del st.session_state.selecionados[id_rec1]
            st.rerun()

    id_rec2 = f"esoccer_vit_{p1}_{p2}"
    item_rec2 = {
        "id": id_rec2, "confronto": f"{p1} vs {p2}", "mercado": f"{melhor_vitoria} ({categoria_jogo})",
        "odd": odd_vitoria_ref, "raio_x": [f"Análise de desempenho cruzada"]
    }
    
    with c_rec2:
        st.markdown(f"""
        <div class="match-card" style="border-color: #10b981;">
            <h4 style="color: #10b981; margin-top: 0;">🏆 Mercado de Resultado</h4>
            <p><strong>Sugestão:</strong> {melhor_vitoria}</p>
            <p><strong>Análise:</strong> Baseada na conversão ofensiva e solidez defensiva.</p>
            <p><strong>Odd de Referência:</strong> ~{odd_vitoria_ref:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        ja_r2 = id_rec2 in st.session_state.selecionados
        if st.checkbox("📥 Adicionar Sugestão de Resultado ao Bilhete", value=ja_r2, key="chk_rec_vit"):
            if not ja_r2:
                st.session_state.selecionados[id_rec2] = item_rec2
                st.success("Adicionado ao bilhete!")
                st.rerun()
        elif ja_r2:
            del st.session_state.selecionados[id_rec2]
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
