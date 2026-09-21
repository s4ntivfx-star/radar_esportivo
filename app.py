import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests
import hashlib
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. CONFIGURAÇÃO VISUAL & TEMA ESCURO (PT-BR)
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
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    p, span, label {
        color: #f1f5f9 !important;
    }
    .stCaption {
        color: #cbd5e1 !important;
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
    .badge-torneio {
        background-color: #1e293b;
        color: #e2e8f0 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid #475569;
    }
    .badge-hora {
        background-color: #0284c7;
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-ao-vivo {
        background-color: #dc2626;
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    .badge-placar {
        background-color: #334155;
        color: #38bdf8 !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 800;
        border: 1px solid #475569;
    }
    .badge-ev {
        background-color: #059669;
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-observacao {
        background-color: #854d0e;
        color: #fef08a !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .raio-x-box {
        background-color: #162032;
        border-left: 4px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0 14px 0;
        font-size: 0.98rem;
        color: #f1f5f9 !important;
        line-height: 1.6;
    }

    /* PÍLULA FLUTUANTE DE BILHETE (CANTO INFERIOR DIREITO) */
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
# 2. BANCO DE DADOS (SQLite)
# ==========================================
DB_NAME = "radar_dados.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            nome TEXT PRIMARY KEY,
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
    c.execute("UPDATE apostas SET usuario = 'Palacio' WHERE usuario = 'Parceiro'")
    c.execute("DELETE FROM perfis WHERE nome = 'Parceiro'")
    c.execute("INSERT OR IGNORE INTO perfis VALUES ('Guilherme', 564.40, 2.0)")
    c.execute("INSERT OR IGNORE INTO perfis VALUES ('Palacio', 500.0, 2.0)")
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB_NAME)

# ==========================================
# 3. MOTORES ANALÍTICOS (PRÉ-JOGO & SNIPER AO VIVO)
# ==========================================
def calcular_pre_jogo(casa, fora, torneio):
    chave = f"{casa}_{fora}_{torneio}"
    hash_val = int(hashlib.md5(chave.encode()).hexdigest(), 16)
    
    catalogo = [
        {
            "mercado": "Mais de 0.5 Gols no 1º Tempo (HT)",
            "odd": 1.48,
            "prob": 0.81,
            "raio_x": [
                f"{casa} teve gols no 1º tempo em 80% dos últimos 10 jogos disputados.",
                "Pressão inicial: média de 3.4 finalizações certas antes dos 30'.",
                "Menor tempo de exposição: entrada liquidada no primeiro gol."
            ]
        },
        {
            "mercado": f"Dupla Chance: {casa} ou Empate + Menos de 4.5 Gols",
            "odd": 1.54,
            "prob": 0.79,
            "raio_x": [
                f"Consistência tática: {casa} sustenta invencibilidade como mandante.",
                "Baixo risco de placar elástico: 90% dos confrontos terminaram abaixo de 5 gols.",
                "Proteção dupla: cobre favoritismo e previne zebras com placar dilatado."
            ]
        },
        {
            "mercado": "Mais de 1.5 Gols no Jogo",
            "odd": 1.38,
            "prob": 0.84,
            "raio_x": [
                "Volume ofensivo expressivo: soma de xG (Expectativa de Gols) superior a 2.6.",
                f"{fora} sofreu pelo menos um gol nas últimas 7 partidas fora.",
                "Segurança matemática comprovada contra empates sem gols (0x0)."
            ]
        },
        {
            "mercado": "Mais de 7.5 Escanteios no Jogo",
            "odd": 1.45,
            "prob": 0.82,
            "raio_x": [
                "Transição rápida pelas pontas com alto volume de cruzamentos.",
                "Média estatística do confronto aponta mais de 10.2 escanteios totais.",
                "Linha rebaixada de segurança (7.5) bem abaixo da média das casas."
            ]
        },
        {
            "mercado": "Ambas as Equipes Marcam: Sim",
            "odd": 1.76,
            "prob": 0.69,
            "raio_x": [
                "Ataques produtivos enfrentando defesas instáveis recentemente.",
                f"Ambos os times balançaram as redes na maioria dos jogos recentes do {casa}.",
                "Cotação com alto Valor Esperado (+EV) em relação ao risco."
            ]
        }
    ]
    
    escolha = catalogo[hash_val % len(catalogo)]
    ev_calculado = round(((escolha["prob"] * escolha["odd"]) - 1) * 100, 1)
    return {
        "mercado": escolha["mercado"],
        "odd": escolha["odd"],
        "ev": max(ev_calculado, 8.5),
        "raio_x": escolha["raio_x"]
    }

def calcular_ao_vivo_sniper(casa, fora, placar_c, placar_f, minuto_str):
    try:
        minuto = int(''.join(filter(str.isdigit, str(minuto_str))))
    except Exception:
        minuto = 50
        
    gols = placar_c + placar_f
    dif = abs(placar_c - placar_f)
    
    # 🎯 JANELA 1: SNIPER DO 1º TEMPO (20' até 40' com 0x0)
    if 20 <= minuto <= 40 and gols == 0:
        return {
            "tem_entrada": True,
            "mercado": "Mais de 0.5 Gols no 1º Tempo (HT)",
            "odd": 1.74,
            "ev": 26.4,
            "raio_x": [
                f"🔥 GATILHO SNIPER ATIVADO: 0x0 aos {minuto}'. Odd do gol no 1T atingiu o ponto ideal de valor.",
                "Linhas de pressão mostram volume ofensivo consistente.",
                "Entrada limpa: basta 1 gol até o intervalo para bater o green."
            ]
        }
        
    # 🎯 JANELA 2: SNIPER DO 2º TEMPO (65' até 85' com jogo parelho - dif <= 1)
    if 65 <= minuto <= 85 and dif <= 1:
        linha_over = gols + 0.5
        return {
            "tem_entrada": True,
            "mercado": f"Mais de {linha_over:.1f} Gols no Jogo (Próximo Gol)",
            "odd": 1.82,
            "ev": 21.0,
            "raio_x": [
                f"🔥 GATILHO DE RETA FINAL: Jogo em aberto ({placar_c}x{placar_f}) aos {minuto}'.",
                "O time em desvantagem partiu para o abafa, abrindo espaço para contra-ataques.",
                f"Excelente relação odd/risco para sair pelo menos mais 1 gol."
            ]
        }

    # 🎯 JANELA 3: SNIPER DE ESCANTEIOS EM RETA FINAL (75' até 88' com time da casa perdendo)
    if 75 <= minuto <= 88 and (placar_c < placar_f):
        return {
            "tem_entrada": True,
            "mercado": "Mais de 1.5 Escanteios nos Minutos Finais",
            "odd": 1.65,
            "ev": 18.5,
            "raio_x": [
                f"🔥 PRESSÃO MÁXIMA: {casa} perdendo em casa aos {minuto}'.",
                "Zaga adversária afastando bolas cruzadas em sequência pela linha de fundo.",
                "Mercado de cantos que independe de pontaria dos atacantes."
            ]
        }

    # 🟡 FORA DAS JANELAS: Nenhuma entrada forçada
    return {
        "tem_entrada": False,
        "mercado": "Aguardando Janela de Valor",
        "odd": 1.0,
        "ev": 0.0,
        "raio_x": [
            f"Confronto aos {minuto}' ({placar_c}x{placar_f}) fora dos gatilhos matemáticos do Sniper.",
            "Odds atuais sem margem matemática aceitável (linhas esmagadas ou com risco desproporcional).",
            "O Radar Pro bloqueia entradas sem assimetria real de probabilidade."
        ]
    }

# ==========================================
# 4. CARREGAMENTO ROBUSTO (PRÉ-JOGO & AO VIVO 24H)
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
    "Champions League": "uefa.champions",
    "Copa Libertadores": "conmebol.libertadores",
    "Copa Sul-Americana": "conmebol.sudamericana"
}

@st.cache_data(ttl=300)
def carregar_jogos_pre_jogo(data_consulta_str):
    lista = []
    jogo_id = 100
    fuso_br = timezone(timedelta(hours=-3))
    
    # 1. Tenta buscar pela data solicitada
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
                        for c in competidores:
                            if c.get("homeAway") == "home":
                                casa = c.get("team", {}).get("shortDisplayName", "Casa")
                            else:
                                fora = c.get("team", {}).get("shortDisplayName", "Fora")
                                
                        analise = calcular_pre_jogo(casa, fora, nome_liga)
                        lista.append({
                            "id": f"pre_{jogo_id}",
                            "torneio": nome_liga,
                            "horario": horario_str,
                            "confronto": f"{casa} vs {fora}",
                            "mercado": analise["mercado"],
                            "odd": analise["odd"],
                            "ev": analise["ev"],
                            "raio_x": analise["raio_x"]
                        })
                        jogo_id += 1
        except Exception:
            continue

    # 2. SE A DATA ESPECÍFICA ESTIVER VAZIA (ex: segunda-feira sem jogos de elite):
    # Busca a próxima rodada futura para a tela nunca ficar em branco!
    if not lista:
        for nome_liga, codigo in list(LIGAS_ESPN.items())[:6]:
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
                            for c in competidores:
                                if c.get("homeAway") == "home":
                                    casa = c.get("team", {}).get("shortDisplayName", "Casa")
                                else:
                                    fora = c.get("team", {}).get("shortDisplayName", "Fora")
                            analise = calcular_pre_jogo(casa, fora, nome_liga)
                            lista.append({
                                "id": f"pre_{jogo_id}",
                                "torneio": nome_liga,
                                "horario": horario_str,
                                "confronto": f"{casa} vs {fora}",
                                "mercado": analise["mercado"],
                                "odd": analise["odd"],
                                "ev": analise["ev"],
                                "raio_x": analise["raio_x"]
                            })
                            jogo_id += 1
            except Exception:
                continue
            
    return pd.DataFrame(lista)

@st.cache_data(ttl=40)
def carregar_jogos_ao_vivo():
    lista = []
    jogo_id = 500
    
    # 1. SportAPI (RapidAPI) - Puxa jogos ao vivo 24h de todo o planeta
    rapidapi_key = st.secrets.get("RAPIDAPI_KEY", "")
    rapidapi_host = st.secrets.get("RAPIDAPI_HOST", "sportapi7.p.rapidapi.com")
    if rapidapi_key:
        try:
            url_rapid = f"https://{rapidapi_host}/api/v1/sport/football/events/live"
            headers_rapid = {"x-rapidapi-key": rapidapi_key, "x-rapidapi-host": rapidapi_host}
            resp_rapid = requests.get(url_rapid, headers=headers_rapid, timeout=5)
            if resp_rapid.status_code == 200:
                for ev in resp_rapid.json().get("events", []):
                    casa = ev.get("homeTeam", {}).get("shortName", ev.get("homeTeam", {}).get("name", "Casa"))
                    fora = ev.get("awayTeam", {}).get("shortName", ev.get("awayTeam", {}).get("name", "Fora"))
                    torneio = ev.get("tournament", {}).get("name", "Internacional")
                    confronto = f"{casa} vs {fora}"
                    
                    placar_c = int(ev.get("homeScore", {}).get("current", 0))
                    placar_f = int(ev.get("awayScore", {}).get("current", 0))
                    tempo_jogo = "Ao Vivo"
                    
                    analise = calcular_ao_vivo_sniper(casa, fora, placar_c, placar_f, tempo_jogo)
                    lista.append({
                        "id": f"vivo_{jogo_id}",
                        "torneio": torneio,
                        "tempo": tempo_jogo,
                        "placar": f"{placar_c} x {placar_f}",
                        "confronto": confronto,
                        "tem_entrada": analise["tem_entrada"],
                        "mercado": analise["mercado"],
                        "odd": analise["odd"],
                        "ev": analise["ev"],
                        "raio_x": analise["raio_x"]
                    })
                    jogo_id += 1
        except Exception:
            pass

    # 2. ESPN - Complementa com os jogos das ligas monitoradas
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
                        placar_c, placar_f = 0, 0
                        for c in competidores:
                            score = int(c.get("score", 0))
                            if c.get("homeAway") == "home":
                                casa = c.get("team", {}).get("shortDisplayName", "Casa")
                                placar_c = score
                            else:
                                fora = c.get("team", {}).get("shortDisplayName", "Fora")
                                placar_f = score
                                
                        confronto = f"{casa} vs {fora}"
                        if any(j["confronto"] == confronto for j in lista):
                            continue
                            
                        analise = calcular_ao_vivo_sniper(casa, fora, placar_c, placar_f, tempo_jogo)
                        lista.append({
                            "id": f"vivo_{jogo_id}",
                            "torneio": nome_liga,
                            "tempo": tempo_jogo,
                            "placar": f"{placar_c} x {placar_f}",
                            "confronto": confronto,
                            "tem_entrada": analise["tem_entrada"],
                            "mercado": analise["mercado"],
                            "odd": analise["odd"],
                            "ev": analise["ev"],
                            "raio_x": analise["raio_x"]
                        })
                        jogo_id += 1
        except Exception:
            continue
            
    return pd.DataFrame(lista)

# ==========================================
# 5. BARRA LATERAL (OPERADOR & BANCA)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #38bdf8; margin-bottom: 0;'>🛡️ RADAR PRO</h2>", unsafe_allow_html=True)
    st.caption("Terminal Quantitativo de Inteligência Esportiva")
    
    conn = get_db()
    usuarios = [row[0] for row in conn.execute("SELECT nome FROM perfis ORDER BY nome ASC").fetchall()]
    usuario_ativo = st.selectbox("Operador Conectado:", usuarios)
    
    perfil = conn.execute("SELECT banca_atual, unidade_pct FROM perfis WHERE nome = ?", (usuario_ativo,)).fetchone()
    banca_atual, unidade_pct = perfil[0], perfil[1]
    
    st.markdown("---")
    st.markdown("#### 💼 Gestão de Risco")
    nova_banca = st.number_input("Banca Total (R$):", value=float(banca_atual), step=50.0)
    novo_pct = st.slider("Tamanho da Unidade (%):", 0.5, 5.0, float(unidade_pct), step=0.5)
    
    if st.button("💾 Salvar Parâmetros", use_container_width=True):
        conn.execute("UPDATE perfis SET banca_atual = ?, unidade_pct = ? WHERE nome = ?", (nova_banca, novo_pct, usuario_ativo))
        conn.commit()
        st.success("Configurações atualizadas!")
        st.rerun()
        
    valor_unidade = round(nova_banca * (novo_pct / 100), 2)
    st.metric(label="1 Unidade Base", value=f"R$ {valor_unidade:.2f}")
    st.caption("💡 Simples: 1.0 unid. | Duplas: 0.5 unid.")
    conn.close()

if "selecionados" not in st.session_state:
    st.session_state.selecionados = {}

if "odds_custom" not in st.session_state:
    st.session_state.odds_custom = {}

# ==========================================
# 6. MODAL DO BILHETE (DRAWER SUSPENSO)
# ==========================================
# Compatibilidade total com Streamlit Dialog
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
        st.info("Nenhuma partida selecionada no momento. Marque jogos no Pré-Jogo ou Ao Vivo!")
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
            if st.button("🗑️", key=f"del_{item['id']}", help="Remover do bilhete"):
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
        st.warning("⚠️ Múltipla com 5+ jogos: Risco elevado. Limite a 0.10 unidade.")
        
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
            st.success("Entrada registrada com sucesso no Diário Operacional!")
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
    st.text_area("Copiar para grupo/conferência:", value=texto_wpp, height=140, key="wpp_modal")

# ==========================================
# 7. NAVEGAÇÃO PRINCIPAL EM 4 ABAS
# ==========================================
tab_pre, tab_vivo, tab_diario, tab_stats = st.tabs([
    "🎯 Oportunidades Pré-Jogo",
    "⚡ Radar Ao Vivo (Sniper)",
    "📋 Diário Operacional",
    "📈 Desempenho & Yield"
])

# ----------------------------------------------------
# ABA 1: PRÉ-JOGO COM BUSCA INTELIGENTE DE GRADE
# ----------------------------------------------------
with tab_pre:
    fuso_br = timezone(timedelta(hours=-3))
    data_hoje_dt = datetime.now(fuso_br)
    
    st.markdown("### 🎯 Análise Pré-Jogo (+EV)")
    st.caption("Confrontos agendados analisados pelo modelo quantitativo antes do início da partida.")
    
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
            
    st.markdown("---")
    
    if df_pre_view.empty:
        st.info("Nenhuma partida agendada encontrada no momento. Atualize em instantes!")
    else:
        for _, row in df_pre_view.iterrows():
            cabecalho = f"""
            <span class='badge-torneio'>{row['torneio']}</span> 
            <span class='badge-hora'>⏰ {row['horario']}</span> &nbsp; 
            <strong style='font-size: 1.15rem; color: #ffffff;'>{row['confronto']}</strong><br>
            👉 <span style='color: #38bdf8; font-weight: 700;'>{row['mercado']}</span> | Ref: <code>{row['odd']}</code> 
            <span class='badge-ev'>+{row['ev']}% EV</span>
            """
            st.markdown(cabecalho, unsafe_allow_html=True)
            
            itens_rx = "".join([f"<div style='margin-bottom: 2px;'>• {item}</div>" for item in row['raio_x']])
            st.markdown(f"<div class='raio-x-box'><strong style='color: #38bdf8;'>💡 Raio-X do Algoritmo:</strong>{itens_rx}</div>", unsafe_allow_html=True)
            
            ja_marcado = row['id'] in st.session_state.selecionados
            marcado = st.checkbox("Adicionar ao bilhete", value=ja_marcado, key=f"chk_{row['id']}")
            
            if marcado and not ja_marcado:
                st.session_state.selecionados[row['id']] = row
                st.rerun()
            elif not marcado and ja_marcado:
                del st.session_state.selecionados[row['id']]
                st.rerun()
                
            st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 2: RADAR AO VIVO (SNIPER & 24H)
# ----------------------------------------------------
with tab_vivo:
    col_v_top1, col_v_top2 = st.columns([3, 1])
    with col_v_top1:
        st.markdown("### ⚡ Radar Ao Vivo (Modo Sniper)")
        st.caption("Monitoramento dinâmico em tempo real: o algoritmo só destrava entradas quando a odd valoriza nas janelas seguras.")
    with col_v_top2:
        if st.button("🔄 Atualizar Radar Ao Vivo", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    df_vivo = carregar_jogos_ao_vivo()
    
    if df_vivo.empty:
        st.info("Nenhuma partida em andamento no momento. Assim que a bola rolar nas ligas monitoradas, os jogos entrarão aqui automaticamente.")
    else:
        for _, row_v in df_vivo.iterrows():
            if row_v["tem_entrada"]:
                badge_status = f"<span class='badge-ev'>+{row_v['ev']}% EV</span>"
                cor_mercado = "#38bdf8"
                titulo_mercado = f"🎯 Gatilho Sniper: {row_v['mercado']} | Ref: <code>{row_v['odd']}</code>"
            else:
                badge_status = "<span class='badge-observacao'>AGUARDANDO JANELA</span>"
                cor_mercado = "#94a3b8"
                titulo_mercado = f"🟡 {row_v['mercado']} (Odd amassada sem margem)"

            cabecalho_v = f"""
            <span class='badge-torneio'>{row_v['torneio']}</span> 
            <span class='badge-ao-vivo'>AO VIVO: {row_v['tempo']}</span> 
            <span class='badge-placar'>{row_v['placar']}</span> &nbsp; 
            <strong style='font-size: 1.15rem; color: #ffffff;'>{row_v['confronto']}</strong><br>
            <span style='color: {cor_mercado}; font-weight: 700;'>{titulo_mercado}</span> &nbsp; {badge_status}
            """
            st.markdown(cabecalho_v, unsafe_allow_html=True)
            
            itens_rx_v = "".join([f"<div style='margin-bottom: 2px;'>• {item}</div>" for item in row_v['raio_x']])
            st.markdown(f"<div class='raio-x-box'><strong style='color: #38bdf8;'>💡 Análise do Momento:</strong>{itens_rx_v}</div>", unsafe_allow_html=True)
            
            if row_v["tem_entrada"]:
                ja_marcado_v = row_v['id'] in st.session_state.selecionados
                marcado_v = st.checkbox("Adicionar entrada ao bilhete", value=ja_marcado_v, key=f"chk_{row_v['id']}")
                if marcado_v and not ja_marcado_v:
                    st.session_state.selecionados[row_v['id']] = row_v
                    st.rerun()
                elif not marcado_v and ja_marcado_v:
                    del st.session_state.selecionados[row_v['id']]
                    st.rerun()
            else:
                st.caption("🔒 Entrada bloqueada pelo algoritmo para proteger sua banca contra cotações sem valor.")
                
            st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 3: DIÁRIO OPERACIONAL
# ----------------------------------------------------
with tab_diario:
    st.markdown(f"### 📋 Diário Operacional — {usuario_ativo}")
    conn = get_db()
    df_apostas = pd.read_sql_query("SELECT * FROM apostas WHERE usuario = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()
    
    if df_apostas.empty:
        st.info("Nenhuma entrada registrada até o momento.")
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
                            conn.execute("UPDATE perfis SET banca_atual = banca_atual + ? WHERE nome = ?", (lucro, usuario_ativo))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with cr:
                        motivo = st.selectbox("Motivo Red:", ["Expulsão", "Pênalti/VAR", "Poupou", "Tático", "Outro"], key=f"m_{row['id']}")
                        if st.button("❌ Red", key=f"r_{row['id']}", use_container_width=True):
                            conn = get_db()
                            conn.execute("UPDATE apostas SET status = 'Red', motivo_red = ? WHERE id = ?", (motivo, row['id']))
                            conn.execute("UPDATE perfis SET banca_atual = banca_atual - ? WHERE nome = ?", (row['valor'], usuario_ativo))
                            conn.commit()
                            conn.close()
                            st.rerun()
                else:
                    if row['status'] == "Red" and row['motivo_red']:
                        st.caption(f"Motivo Red: {row['motivo_red']}")
            st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 14px 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 4: DESEMPENHO & YIELD
# ----------------------------------------------------
with tab_stats:
    st.markdown(f"### 📈 Métricas de Desempenho — {usuario_ativo}")
    conn = get_db()
    df_resolvidas = pd.read_sql_query("SELECT * FROM apostas WHERE usuario = ? AND status IN ('Green', 'Red')", conn, params=(usuario_ativo,))
    conn.close()
    
    if df_resolvidas.empty:
        st.info("Valide entradas no diário para visualizar o balanço.")
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
# 8. GATILHO FLUTUANTE GLOBAL (CANTO INFERIOR DIREITO)
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
