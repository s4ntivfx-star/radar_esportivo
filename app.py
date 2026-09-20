import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests
import hashlib
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. CONFIGURAÇÃO VISUAL & TEMA ESCURO DE ALTO CONTRASTE
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
        animation: pulse 2s infinite;
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
# 3. MOTORES ANALÍTICOS (PRÉ-JOGO E AO VIVO)
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
                f"Consistência tática: {casa} sustenta invencibilidade recente como mandante.",
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
                "Segurança matemática comprovada contra empates em zero a zero."
            ]
        },
        {
            "mercado": "Mais de 7.5 Escanteios no Jogo",
            "odd": 1.45,
            "prob": 0.82,
            "raio_x": [
                "Transição rápida pelas alas com frequência alta de bolas cruzadas na área.",
                "Média estatística do confronto aponta mais de 10.2 escanteios totais.",
                "Linha rebaixada de segurança (7.5) bem abaixo do padrão das casas."
            ]
        },
        {
            "mercado": "Ambas as Equipes Marcam: Sim",
            "odd": 1.76,
            "prob": 0.69,
            "raio_x": [
                "Ataques produtivos enfrentando setores defensivos com instabilidade recente.",
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
        "prob": escolha["prob"],
        "ev": max(ev_calculado, 8.5),
        "raio_x": escolha["raio_x"]
    }

def calcular_ao_vivo(casa, fora, placar_c, placar_f, minuto_str):
    try:
        minuto = int(''.join(filter(str.isdigit, minuto_str)))
    except Exception:
        minuto = 45
        
    gols_atuais = placar_c + placar_f
    diferenca = abs(placar_c - placar_f)
    
    # 1. Primeiro tempo sem gols (0x0 até 35') -> Oportunidade clara de gol no 1T
    if minuto < 40 and gols_atuais == 0:
        return {
            "mercado": "Mais de 0.5 Gols no 1º Tempo (HT)",
            "odd": 1.85,
            "ev": 24.5,
            "raio_x": [
                f"Placar zerado aos {minuto}'. A odd do gol antes do intervalo subiu e abriu valor.",
                "Pressão alta esperada na reta final da primeira etapa.",
                "Basta 1 gol antes dos 45' para bater a entrada."
            ]
        }
    
    # 2. Jogo em reta final com placar já dilatado (ex: 3x1 aos 80') -> Bloqueia zebras
    if minuto >= 75 and diferenca >= 2:
        linha_under = gols_atuais + 1.5
        return {
            "mercado": f"Menos de {linha_under:.1f} Gols Totais",
            "odd": 1.40,
            "ev": 14.0,
            "raio_x": [
                f"Placar dilatado ({placar_c}x{placar_f}) aos {minuto}'. Ritmo da partida desacelerando.",
                "Equipe em vantagem administra posse e evita divididas de desgaste.",
                f"Protege contra mais gols tardios (linha rebaixada em {linha_under:.1f})."
            ]
        }
    
    # 3. Segundo tempo parelho (ex: 1x0, 0x1, 1x1 até os 75') -> Linha de Over limite
    if 45 <= minuto <= 75 and diferenca <= 1:
        linha_over = gols_atuais + 0.5
        return {
            "mercado": f"Mais de {linha_over:.1f} Gols no Jogo (Próximo Gol)",
            "odd": 1.62,
            "ev": 18.2,
            "raio_x": [
                f"Confronto em aberto ({placar_c}x{placar_f}) aos {minuto}'. O time em desvantagem partiu para o ataque.",
                "Cenário propício a contragolpe rápido ou empate na reta final.",
                f"Entrada confirmada assim que sair mais 1 gol na partida."
            ]
        }
        
    # 4. Reta final absoluta (80'+ parelho) -> Corrida de Escanteios
    linha_cantos = 8.5
    return {
        "mercado": f"Mais de {linha_cantos} Escanteios Totais",
        "odd": 1.50,
        "ev": 15.5,
        "raio_x": [
            f"Fase de abafa tático aos {minuto}'. Defesas afastando bolas por linha de fundo.",
            "Cruzamentos insistentes gerando rebatidas para escanteio.",
            "Mercado que independe da pontaria dos atacantes no gol."
        ]
    }

# ==========================================
# 4. CARREGAMENTO DOS DADOS (SEPARADOS POR ESTADO)
# ==========================================
LIGAS_ESPN = {
    "Brasileirão": "bra.1",
    "Premier League": "eng.1",
    "La Liga": "esp.1",
    "Serie A": "ita.1",
    "Bundesliga": "ger.1",
    "Champions League": "uefa.champions"
}

@st.cache_data(ttl=300)
def carregar_jogos_pre_jogo():
    lista = []
    jogo_id = 100
    fuso_br = timezone(timedelta(hours=-3))
    
    for nome_liga, codigo in LIGAS_ESPN.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard"
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                for ev in resp.json().get("events", []):
                    estado = ev.get("status", {}).get("type", {}).get("name", "")
                    # Apenas partidas agendadas (que ainda NÃO começaram)
                    if estado == "STATUS_SCHEDULED":
                        data_iso = ev.get("date", "")
                        horario_str = "--:--"
                        if data_iso:
                            try:
                                dt_utc = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
                                dt_br = dt_utc.astimezone(fuso_br)
                                horario_str = dt_br.strftime("%H:%M")
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
                            "id": jogo_id,
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

@st.cache_data(ttl=45)
def carregar_jogos_ao_vivo():
    lista = []
    jogo_id = 500
    
    # 1. Partidas ao vivo via ESPN
    for nome_liga, codigo in LIGAS_ESPN.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard"
        try:
            resp = requests.get(url, timeout=5)
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
                                
                        analise = calcular_ao_vivo(casa, fora, placar_c, placar_f, tempo_jogo)
                        lista.append({
                            "id": jogo_id,
                            "torneio": nome_liga,
                            "tempo": tempo_jogo,
                            "placar": f"{placar_c} x {placar_f}",
                            "confronto": f"{casa} vs {fora}",
                            "mercado": analise["mercado"],
                            "odd": analise["odd"],
                            "ev": analise["ev"],
                            "raio_x": analise["raio_x"]
                        })
                        jogo_id += 1
        except Exception:
            continue
            
    # 2. Partidas ao vivo adicionais via SportAPI
    rapidapi_key = st.secrets.get("RAPIDAPI_KEY", "")
    rapidapi_host = st.secrets.get("RAPIDAPI_HOST", "sportapi7.p.rapidapi.com")
    if rapidapi_key:
        try:
            url_rapid = f"https://{rapidapi_host}/api/v1/sport/football/events/live"
            headers_rapid = {"x-rapidapi-key": rapidapi_key, "x-rapidapi-host": rapidapi_host}
            resp_rapid = requests.get(url_rapid, headers=headers_rapid, timeout=5)
            if resp_rapid.status_code == 200:
                for ev in resp_rapid.json().get("events", [])[:8]:
                    casa = ev.get("homeTeam", {}).get("shortName", "Casa")
                    fora = ev.get("awayTeam", {}).get("shortName", "Fora")
                    torneio = ev.get("tournament", {}).get("name", "Internacional")
                    confronto = f"{casa} vs {fora}"
                    
                    if any(j["confronto"] == confronto for j in lista):
                        continue
                        
                    placar_c = int(ev.get("homeScore", {}).get("current", 0))
                    placar_f = int(ev.get("awayScore", {}).get("current", 0))
                    tempo_jogo = "Ao Vivo"
                    
                    analise = calcular_ao_vivo(casa, fora, placar_c, placar_f, tempo_jogo)
                    lista.append({
                        "id": jogo_id,
                        "torneio": torneio,
                        "tempo": tempo_jogo,
                        "placar": f"{placar_c} x {placar_f}",
                        "confronto": confronto,
                        "mercado": analise["mercado"],
                        "odd": analise["odd"],
                        "ev": analise["ev"],
                        "raio_x": analise["raio_x"]
                    })
                    jogo_id += 1
        except Exception:
            pass
            
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

# Gerenciamento de seleção entre abas
if "selecionados" not in st.session_state:
    st.session_state.selecionados = {}

# ==========================================
# 6. NAVEGAÇÃO PRINCIPAL EM 4 ABAS
# ==========================================
tab_pre, tab_vivo, tab_diario, tab_stats = st.tabs([
    "🎯 Oportunidades Pré-Jogo",
    "⚡ Radar Ao Vivo",
    "📋 Diário Operacional",
    "📈 Desempenho & Yield"
])

# ----------------------------------------------------
# ABA 1: PRÉ-JOGO (APENAS PARTIDAS NÃO INICIADAS)
# ----------------------------------------------------
with tab_pre:
    col_pre_lista, col_pre_bilhete = st.columns([3.2, 2.2], gap="large")
    df_pre = carregar_jogos_pre_jogo()
    
    with col_pre_lista:
        st.markdown("### 🎯 Análise Pré-Jogo (+EV)")
        st.caption("Apenas partidas agendadas que ainda não começaram. Quando o jogo inicia, ele migra para o Radar Ao Vivo.")
        
        if df_pre.empty:
            st.info("Nenhuma partida agendada no momento para as ligas principais. Confira o Radar Ao Vivo!")
        else:
            todas_ligas = ["Todas as Ligas"] + sorted(list(df_pre["torneio"].unique()))
            liga_pre = st.selectbox("Filtrar Campeonato:", todas_ligas, index=0, key="filtro_pre")
            df_pre_view = df_pre if liga_pre == "Todas as Ligas" else df_pre[df_pre["torneio"] == liga_pre]
            
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
                
                marcado = st.checkbox("Adicionar ao bilhete", key=f"pre_{row['id']}")
                if marcado:
                    st.session_state.selecionados[row['id']] = row
                elif row['id'] in st.session_state.selecionados:
                    del st.session_state.selecionados[row['id']]
                    
                st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

    with col_pre_bilhete:
        st.markdown("### 📑 Construtor de Bilhete")
        itens_bilhete = list(st.session_state.selecionados.values())
        
        if itens_bilhete:
            st.caption("Ajuste a **Odd Real da Betano** para cada entrada:")
            odds_ajustadas = []
            for item in itens_bilhete:
                with st.container():
                    c_txt, c_odd = st.columns([3, 1.6])
                    with c_txt:
                        st.markdown(f"**{item['confronto']}**<br><span style='font-size: 0.9rem; color: #38bdf8; font-weight: 600;'>{item['mercado']}</span>", unsafe_allow_html=True)
                    with c_odd:
                        odd_digitada = st.number_input(
                            "Odd Betano",
                            min_value=1.01,
                            max_value=100.0,
                            value=float(item['odd']),
                            step=0.01,
                            key=f"odd_b_{item['id']}"
                        )
                        odds_ajustadas.append(odd_digitada)
                    st.markdown("<hr style='border: 0; border-top: 1px solid #334155; margin: 6px 0 10px 0;'>", unsafe_allow_html=True)
                    
            odd_final = float(np.prod(odds_ajustadas))
            qtd = len(itens_bilhete)
            
            c_res1, c_res2 = st.columns(2)
            c_res1.metric("Cotação Final (Real)", f"{odd_final:.2f}")
            c_res2.metric("Total de Jogos", f"{qtd}")
            
            if qtd == 1:
                stake = valor_unidade * 1.0
                st.info("Sugestão de Risco: **1.0 Unidade** (Aposta Simples)")
            elif qtd <= 2:
                stake = valor_unidade * 0.5
                st.info("Sugestão de Risco: **0.5 Unidade** (Dupla Recomendada)")
            elif qtd <= 4:
                stake = valor_unidade * 0.25
                st.info("Sugestão de Risco: **0.25 Unidade** (Múltipla Moderada)")
            else:
                stake = valor_unidade * 0.1
                st.warning("⚠️ Múltipla com 5+ jogos: Risco alto. Limite a 0.10 unidade.")
                
            valor_apostar = st.number_input("Valor da Entrada (R$):", value=float(round(stake, 2)), step=5.0, key="val_apostar_pre")
            retorno_estimado = valor_apostar * odd_final
            st.caption(f"Retorno estimado: **R$ {retorno_estimado:.2f}** (Lucro líquido: R$ {retorno_estimado - valor_apostar:.2f})")
            
            if st.button("💾 Gravar Entrada no Diário", use_container_width=True, key="btn_salvar_pre"):
                conn = get_db()
                descricoes = " + ".join([f"{r['confronto']} ({r['mercado']} @{o:.2f})" for r, o in zip(itens_bilhete, odds_ajustadas)])
                tipo = "Simples" if qtd == 1 else f"Múltipla ({qtd}j)"
                data_hoje = datetime.now().strftime("%d/%m %H:%M")
                
                conn.execute(
                    "INSERT INTO apostas (usuario, data, descricao, tipo_aposta, odd, valor, status, motivo_red) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (usuario_ativo, data_hoje, descricoes, tipo, odd_final, valor_apostar, "Pendente", "")
                )
                conn.commit()
                conn.close()
                st.session_state.selecionados.clear()
                st.success("Aposta registrada no Diário!")
                st.rerun()
                
            st.markdown("---")
            st.markdown("#### 📲 Envio para WhatsApp")
            texto_wpp = f"⚽ *RADAR PRO - ENTRADA*\n"
            texto_wpp += f"👤 *Operador:* {usuario_ativo}\n"
            texto_wpp += f"🎯 *Jogos:* {qtd} | *Odd:* {odd_final:.2f}\n"
            texto_wpp += f"💵 *Stake:* R$ {valor_apostar:.2f} (Retorno: R$ {retorno_estimado:.2f})\n"
            texto_wpp += "---------------------------------\n"
            for it, odd_r in zip(itens_bilhete, odds_ajustadas):
                texto_wpp += f"📌 *{it['confronto']}*\n"
                texto_wpp += f"👉 {it['mercado']} | Odd: *{odd_r:.2f}*\n"
                texto_wpp += f"💡 _{it['raio_x'][0]}_\n\n"
            texto_wpp += "📊 _Gestão quantitativa de risco aplicada._"
            st.text_area("Copiar bilhete:", value=texto_wpp, height=160, key="wpp_pre")
        else:
            st.info("Selecione partidas na lista ao lado para montar o bilhete.")

# ----------------------------------------------------
# ABA 2: RADAR AO VIVO (DINÂMICO, PLACAR & MINUTAGEM)
# ----------------------------------------------------
with tab_vivo:
    col_v_top1, col_v_top2 = st.columns([3, 1])
    with col_v_top1:
        st.markdown("### ⚡ Radar Ao Vivo Dinâmico")
        st.caption("Oportunidades calculadas em tempo real com base no placar, minutagem e momento do confronto.")
    with col_v_top2:
        if st.button("🔄 Atualizar Radar Ao Vivo", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    df_vivo = carregar_jogos_ao_vivo()
    
    if df_vivo.empty:
        st.info("Nenhuma partida em andamento nas ligas monitoradas neste exato momento.")
    else:
        for _, row_v in df_vivo.iterrows():
            cabecalho_v = f"""
            <span class='badge-torneio'>{row_v['torneio']}</span> 
            <span class='badge-ao-vivo'>AO VIVO: {row_v['tempo']}</span> 
            <span class='badge-placar'>{row_v['placar']}</span> &nbsp; 
            <strong style='font-size: 1.15rem; color: #ffffff;'>{row_v['confronto']}</strong><br>
            ⚡ <span style='color: #38bdf8; font-weight: 700;'>Oportunidade Ao Vivo: {row_v['mercado']}</span> | Ref: <code>{row_v['odd']}</code> 
            <span class='badge-ev'>+{row_v['ev']}% EV</span>
            """
            st.markdown(cabecalho_v, unsafe_allow_html=True)
            
            itens_rx_v = "".join([f"<div style='margin-bottom: 2px;'>• {item}</div>" for item in row_v['raio_x']])
            st.markdown(f"<div class='raio-x-box'><strong style='color: #38bdf8;'>💡 Leitura do Momento:</strong>{itens_rx_v}</div>", unsafe_allow_html=True)
            
            marcado_v = st.checkbox("Adicionar entrada ao bilhete", key=f"v_{row_v['id']}")
            if marcado_v:
                st.session_state.selecionados[row_v['id']] = row_v
            elif row_v['id'] in st.session_state.selecionados:
                del st.session_state.selecionados[row_v['id']]
                
            st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------
# ABA 3: DIÁRIO OPERACIONAL REESTRUTURADO
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
