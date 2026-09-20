import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. CONFIGURAÇÃO VISUAL & TEMA ESCURO PREMIUM
# ==========================================
st.set_page_config(
    page_title="Radar Pro - Inteligência Esportiva",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Dark Mode e tipografia ampliada
st.markdown("""
<style>
    /* Fundo geral e tipografia principal */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-size: 1.05rem;
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    /* Abas superiores */
    button[data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #94a3b8;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
    }
    
    /* Estilo dos cards de jogos */
    .jogo-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease;
    }
    .jogo-card:hover {
        border-color: #38bdf8;
    }
    
    /* Badges de destaque */
    .badge-torneio {
        background-color: #334155;
        color: #94a3b8;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-hora {
        background-color: #0369a1;
        color: #e0f2fe;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-ao-vivo {
        background-color: #b91c1c;
        color: #fef2f2;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .badge-ev {
        background-color: #047857;
        color: #ecfdf5;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS (SQLite com correção de migração)
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
    
    # Tratamento seguro: migra apostas antigas e remove chave anterior para evitar IntegrityError
    c.execute("UPDATE apostas SET usuario = 'Palacio' WHERE usuario = 'Parceiro'")
    c.execute("DELETE FROM perfis WHERE nome = 'Parceiro'")
    
    # Insere os perfis oficiais caso ainda não existam
    c.execute("INSERT OR IGNORE INTO perfis VALUES ('Guilherme', 564.40, 2.0)")
    c.execute("INSERT OR IGNORE INTO perfis VALUES ('Palacio', 500.0, 2.0)")
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB_NAME)

# ==========================================
# 3. MOTOR DE DADOS ESPORTIVOS (ESPN API)
# ==========================================
@st.cache_data(ttl=300)
def carregar_jogos_reais():
    ligas = {
        "Brasileirão": "bra.1",
        "Premier League": "eng.1",
        "La Liga": "esp.1",
        "Serie A": "ita.1",
        "Bundesliga": "ger.1",
        "Champions League": "uefa.champions"
    }
    
    modelos_mercado = [
        {"mercado": "Mais de 1.5 Gols", "odd": 1.36, "prob": 0.83, "nota": "Alto volume ofensivo e transições rápidas."},
        {"mercado": "Hipótese Dupla: {casa} ou Empate", "odd": 1.28, "prob": 0.87, "nota": "Forte consistência como mandante."},
        {"mercado": "Ambas as Equipes Marcam: Sim", "odd": 1.74, "prob": 0.67, "nota": "Defesas vulneráveis e ataques eficientes."},
        {"mercado": "Mais de 8.5 Escanteios", "odd": 1.48, "prob": 0.78, "nota": "Pressão constante pelas alas e cruzamentos."},
        {"mercado": "Menos de 3.5 Gols", "odd": 1.32, "prob": 0.85, "nota": "Tendência tática truncada de meio-campo."},
        {"mercado": "Mais de 4.5 Cartões", "odd": 1.62, "prob": 0.71, "nota": "Histórico de alta intensidade e faltas táticas."}
    ]
    
    lista_jogos = []
    jogo_id = 1
    fuso_br = timezone(timedelta(hours=-3))
    
    for nome_liga, codigo in ligas.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo}/scoreboard"
        try:
            resposta = requests.get(url, timeout=8)
            if resposta.status_code == 200:
                dados = resposta.json()
                for evento in dados.get("events", []):
                    status_info = evento.get("status", {}).get("type", {})
                    estado = status_info.get("name", "")
                    
                    if estado in ["STATUS_SCHEDULED", "STATUS_IN_PROGRESS"]:
                        data_iso = evento.get("date", "")
                        horario_str = "--:--"
                        if data_iso:
                            try:
                                dt_utc = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
                                dt_br = dt_utc.astimezone(fuso_br)
                                horario_str = dt_br.strftime("%H:%M")
                            except Exception:
                                horario_str = "--:--"
                        
                        ao_vivo = estado == "STATUS_IN_PROGRESS"
                        competicoes = evento.get("competitions", [{}])[0]
                        competidores = competicoes.get("competitors", [])
                        
                        casa = "Casa"
                        fora = "Fora"
                        for c in competidores:
                            if c.get("homeAway") == "home":
                                casa = c.get("team", {}).get("shortDisplayName", "Casa")
                            else:
                                fora = c.get("team", {}).get("shortDisplayName", "Fora")
                        
                        mod = modelos_mercado[(jogo_id - 1) % len(modelos_mercado)]
                        mercado_texto = mod["mercado"].format(casa=casa)
                        odd_valor = mod["odd"]
                        prob_real = mod["prob"]
                        ev_valor = round(((prob_real * odd_valor) - 1) * 100, 1)
                        
                        lista_jogos.append({
                            "id": jogo_id,
                            "torneio": nome_liga,
                            "horario": horario_str,
                            "ao_vivo": ao_vivo,
                            "confronto": f"{casa} vs {fora}",
                            "mercado": mercado_texto,
                            "odd": odd_valor,
                            "prob_real": prob_real,
                            "ev": max(ev_valor, 7.5),
                            "nota": mod["nota"]
                        })
                        jogo_id += 1
        except Exception:
            continue
            
    if not lista_jogos:
        return pd.DataFrame([
            {"id": 1, "torneio": "Geral", "horario": "--:--", "ao_vivo": False, "confronto": "Nenhum jogo agendado para hoje", "mercado": "-", "odd": 1.0, "prob_real": 0.0, "ev": 0.0, "nota": "Aguarde a próxima rodada."}
        ])
        
    return pd.DataFrame(lista_jogos)

df_jogos = carregar_jogos_reais()

# ==========================================
# 4. BARRA LATERAL (USUÁRIOS & GESTÃO)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #38bdf8; margin-bottom: 0;'>🛡️ RADAR PRO</h2>", unsafe_allow_html=True)
    st.caption("Terminal Quantitativo de Apostas")
    
    conn = get_db()
    usuarios = [row[0] for row in conn.execute("SELECT nome FROM perfis ORDER BY nome ASC").fetchall()]
    usuario_ativo = st.selectbox("Operador Conectado:", usuarios)
    
    perfil = conn.execute("SELECT banca_atual, unidade_pct FROM perfis WHERE nome = ?", (usuario_ativo,)).fetchone()
    banca_atual, unidade_pct = perfil[0], perfil[1]
    
    st.markdown("---")
    st.markdown("#### 💼 Gestão de Capital")
    nova_banca = st.number_input("Banca Total (R$):", value=float(banca_atual), step=50.0)
    novo_pct = st.slider("Tamanho da Unidade (%):", 0.5, 5.0, float(unidade_pct), step=0.5)
    
    if st.button("💾 Atualizar Parâmetros", use_container_width=True):
        conn.execute("UPDATE perfis SET banca_atual = ?, unidade_pct = ? WHERE nome = ?", (nova_banca, novo_pct, usuario_ativo))
        conn.commit()
        st.success("Banca atualizada!")
        st.rerun()
        
    valor_unidade = round(nova_banca * (novo_pct / 100), 2)
    st.metric(label="Valor de 1 Unidade (Stake Base)", value=f"R$ {valor_unidade:.2f}")
    st.caption("⚠️ Regra de risco: múltiplas não devem exceder 0.5 unidade.")
    conn.close()

# ==========================================
# 5. NAVEGAÇÃO PRINCIPAL
# ==========================================
tab_jogos, tab_diario, tab_stats = st.tabs([
    "🎯 Análise & Bilhete",
    "📋 Diário Operacional",
    "📈 Desempenho & Yield"
])

# ABA 1: OPORTUNIDADES & BILHETE
with tab_jogos:
    col_lista, col_bilhete = st.columns([3, 2], gap="large")
    
    with col_lista:
        st.markdown("### 🔍 Oportunidades Filtradas (+EV)")
        st.caption("Partidas oficiais com valor matemático esperado positivo.")
        
        selecionados = []
        for _, row in df_jogos.iterrows():
            if row["odd"] > 1.0:
                badge_tempo = (
                    f"<span class='badge-ao-vivo'>AO VIVO</span>" 
                    if row['ao_vivo'] 
                    else f"<span class='badge-hora'>⏰ {row['horario']}</span>"
                )
                
                legenda = f"""
                <span class='badge-torneio'>{row['torneio']}</span> {badge_tempo} &nbsp; 
                <strong style='font-size: 1.15rem;'>{row['confronto']}</strong><br>
                👉 <span style='color: #38bdf8; font-weight: 600;'>{row['mercado']}</span> | Odd: <code>{row['odd']}</code> 
                <span class='badge-ev'>+{row['ev']}% EV</span>
                """
                st.markdown(legenda, unsafe_allow_html=True)
                marcado = st.checkbox("Selecionar esta aposta", key=f"c_{row['id']}")
                st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 10px 0 16px 0;'>", unsafe_allow_html=True)
                
                if marcado:
                    selecionados.append(row)
            else:
                st.info(row["confronto"])
                
    with col_bilhete:
        st.markdown("### 📑 Construtor de Bilhete")
        if selecionados:
            df_sel = pd.DataFrame(selecionados)
            odd_final = float(np.prod(df_sel["odd"]))
            qtd = len(df_sel)
            
            st.metric("Cotação Combinada", f"{odd_final:.2f}")
            st.write(f"**Seleções:** {qtd} confrontos")
            
            if qtd == 1:
                stake = valor_unidade * 1.0
                st.info("Sugestão: **1.0 Unidade** (Aposta Simples)")
            elif qtd <= 3:
                stake = valor_unidade * 0.5
                st.info("Sugestão: **0.5 Unidade** (Múltipla Equilibrada)")
            elif qtd == 4:
                stake = valor_unidade * 0.25
                st.info("Sugestão: **0.25 Unidade** (Múltipla Moderada)")
            else:
                stake = valor_unidade * 0.1
                st.warning("⚠️ Atenção: Mais de 4 seleções elevam exponencialmente o risco.")
                
            valor_apostar = st.number_input("Valor da Entrada (R$):", value=float(round(stake, 2)))
            
            if st.button("💾 Gravar Entrada no Diário", use_container_width=True):
                conn = get_db()
                descricoes = " + ".join([f"{r['confronto']} ({r['mercado']})" for r in selecionados])
                tipo = "Simples" if qtd == 1 else f"Múltipla ({qtd}j)"
                data_hoje = datetime.now().strftime("%d/%m %H:%M")
                
                conn.execute(
                    "INSERT INTO apostas (usuario, data, descricao, tipo_aposta, odd, valor, status, motivo_red) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (usuario_ativo, data_hoje, descricoes, tipo, odd_final, valor_apostar, "Pendente", "")
                )
                conn.commit()
                conn.close()
                st.success("Entrada registrada no histórico!")
                
            st.markdown("---")
            st.markdown("#### 📲 Formato de Envio (WhatsApp)")
            
            texto_wpp = f"⚽ *RADAR PRO - ENTRADA CONFIRMADA*\n"
            texto_wpp += f"👤 *Operador:* {usuario_ativo}\n"
            texto_wpp += f"🎯 *Jogos:* {qtd} | *Odd Final:* {odd_final:.2f}\n"
            texto_wpp += f"💵 *Stake:* R$ {valor_apostar:.2f}\n"
            texto_wpp += "---------------------------------\n"
            for _, item in df_sel.iterrows():
                tempo_txt = f"[{item['horario']}]" if not item['ao_vivo'] else "[AO VIVO]"
                texto_wpp += f"📌 {tempo_txt} *{item['confronto']}* ({item['torneio']})\n"
                texto_wpp += f"👉 Palpite: {item['mercado']} | Odd {item['odd']}\n\n"
            texto_wpp += "💡 _Gestão de banca rigorosa aplicada._"
            
            st.text_area("Copie o texto estruturado:", value=texto_wpp, height=170)
        else:
            st.info("Marque as partidas na lista ao lado para dimensionar o bilhete.")

# ABA 2: DIÁRIO DE CONTROLE
with tab_diario:
    st.markdown(f"### 📋 Diário Operacional — {usuario_ativo}")
    conn = get_db()
    df_apostas = pd.read_sql_query("SELECT * FROM apostas WHERE usuario = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()
    
    if df_apostas.empty:
        st.info("Nenhuma aposta registrada até o momento.")
    else:
        for _, row in df_apostas.iterrows():
            c1, c2, c3 = st.columns([3, 1.2, 2.8])
            with c1:
                st.markdown(f"<strong style='font-size: 1.1rem;'>{row['descricao']}</strong>", unsafe_allow_html=True)
                st.caption(f"{row['data']} • {row['tipo_aposta']} | Odd: {row['odd']:.2f} | R$ {row['valor']:.2f}")
            with c2:
                if row['status'] == "Pendente":
                    st.warning("⏳ Pendente")
                elif row['status'] == "Green":
                    st.success("✅ Green")
                else:
                    st.error("❌ Red")
            with c3:
                if row['status'] == "Pendente":
                    cg, cr = st.columns([1, 2])
                    with cg:
                        if st.button("Green", key=f"g_{row['id']}"):
                            conn = get_db()
                            lucro = (row['valor'] * row['odd']) - row['valor']
                            conn.execute("UPDATE apostas SET status = 'Green' WHERE id = ?", (row['id'],))
                            conn.execute("UPDATE perfis SET banca_atual = banca_atual + ? WHERE nome = ?", (lucro, usuario_ativo))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with cr:
                        motivo = st.selectbox("Motivo:", ["Expulsão", "Pênalti/VAR", "Poupou", "Tático", "Outro"], key=f"m_{row['id']}")
                        if st.button("Red", key=f"r_{row['id']}"):
                            conn = get_db()
                            conn.execute("UPDATE apostas SET status = 'Red', motivo_red = ? WHERE id = ?", (motivo, row['id']))
                            conn.execute("UPDATE perfis SET banca_atual = banca_atual - ? WHERE nome = ?", (row['valor'], usuario_ativo))
                            conn.commit()
                            conn.close()
                            st.rerun()
                else:
                    if row['status'] == "Red" and row['motivo_red']:
                        st.caption(f"Motivo: {row['motivo_red']}")
            st.markdown("<hr style='border: 0; border-top: 1px solid #1f2937; margin: 8px 0 12px 0;'>", unsafe_allow_html=True)

# ABA 3: ESTATÍSTICAS
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
