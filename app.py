import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# ==============================================================================
# 1. CONFIGURATION SYSTÈME
# ==============================================================================
st.set_page_config(
    page_title="EPL - Master Panel",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. DESIGN SYSTEM "SLATE & BOLD" (CSS)
# ==============================================================================
st.markdown("""
<style>
    /* IMPORT POLICE MODERNE */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;900&display=swap');

    /* VARIABLES DE COULEURS (Thème Gris/Ardoise) */
    :root {
        --bg-color: #cbd5e1;        /* Fond général (Gris Moyen) */
        --card-bg: #f8fafc;         /* Fond des cartes (Gris très clair) */
        --text-primary: #0f172a;    /* Noir Profond (Bleu Nuit) */
        --text-secondary: #334155;  /* Gris Foncé */
        --brand-color: #1e293b;     /* Couleur Principale */
        --accent-color: #2563eb;    /* Bleu Roi (Action) */
        --border-color: #94a3b8;    /* Bordures visibles */
    }

    /* FOND GÉNÉRAL (Pas de blanc pur) */
    .stApp {
        background-color: var(--bg-color);
    }

    /* TYPOGRAPHIE HAUTE VISIBILITÉ */
    html, body, p, div, span, label, li, .stMarkdown {
        font-family: 'Inter', sans-serif;
        color: var(--text-primary) !important;
        font-weight: 600 !important; /* Gras par défaut pour lisibilité */
        line-height: 1.5;
    }

    h1, h2, h3, h4 {
        color: var(--brand-color) !important;
        font-weight: 900 !important; /* Titres très gras */
        letter-spacing: -0.5px;
    }

    /* HERO SECTION (Bannière Moderne) */
    .hero-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 4rem 1.5rem;
        border-radius: 0 0 24px 24px;
        margin: -6rem -4rem 2rem -4rem; /* Full width */
        text-align: center;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        border-bottom: 4px solid var(--accent-color);
    }
    .hero-title {
        color: #ffffff !important;
        font-size: 3rem;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        color: #cbd5e1 !important;
        font-size: 1.2rem;
        font-weight: 500 !important;
        max-width: 700px;
        margin: 0 auto;
    }

    /* CARTES & CONTENEURS (Style Industriel Pro) */
    .metric-card {
        background-color: var(--card-bg);
        border: 2px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        margin-bottom: 15px;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: var(--brand-color);
    }

    /* CHAMPS DE SAISIE (Robustes) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff;
        border: 2px solid #64748b;
        color: #0f172a !important;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1rem;
    }
    
    /* BOUTONS (Actions Fortes) */
    .stButton>button {
        background-color: var(--brand-color);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 0 #0f172a; /* Effet 3D */
        transition: all 0.1s;
    }
    .stButton>button:hover {
        background-color: var(--accent-color);
        box-shadow: 0 2px 0 #1e40af;
        transform: translateY(2px);
    }

    /* CHIFFRES CLÉS (Metrics) */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        color: var(--text-primary) !important;
        font-weight: 900 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: var(--text-secondary) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
    }

    /* RESPONSIVE MOBILE */
    @media (max-width: 768px) {
        .hero-container { margin: -2rem -1rem 1rem -1rem; padding: 2rem 1rem; }
        .hero-title { font-size: 2rem; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. LOGIQUE BACKEND (Sécurité & Données)
# ==============================================================================

# --- Mots de Passe ---
CREDENTIALS = {
    "ADMIN": "light3993",
    "PROF": "ayeleh@edo",
    "DELEGATES": {
        "pass_lt_2024": "LT", "pass_gc_2024": "GC", "pass_iabd_2024": "IABD",
        "pass_is_2024": "IS", "pass_ge_2024": "GE", "pass_gm_2024": "GM"
    }
}

# --- Connexion Supabase ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("❌ ERREUR : Clés Supabase non détectées.")
    st.stop()

# --- Fonctions Utilitaires ---
def init_session():
    if 'user_role' not in st.session_state: st.session_state['user_role'] = None
    if 'user_scope' not in st.session_state: st.session_state['user_scope'] = None

def login(password):
    if password == CREDENTIALS["ADMIN"]:
        st.session_state.update({'user_role': 'ADMIN', 'user_scope': 'ALL'})
        return True
    elif password == CREDENTIALS["PROF"]:
        st.session_state.update({'user_role': 'PROF', 'user_scope': 'ALL'})
        return True
    elif password in CREDENTIALS["DELEGATES"]:
        st.session_state.update({'user_role': 'DELEGATE', 'user_scope': CREDENTIALS["DELEGATES"][password]})
        return True
    return False

# --- Requêtes BDD ---
def get_courses(stream):
    return supabase.table('courses').select("*").eq('stream_target', stream).execute().data

def get_students(stream):
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

def get_student_details(search_term):
    res = supabase.from_('student_stats').select("*").eq('student_id', search_term).execute()
    if not res.data:
        res = supabase.from_('student_stats').select("*").ilike('last_name', f"%{search_term}%").execute()
    return res.data

def get_global_stats():
    return supabase.from_('student_stats').select("*").execute().data

def get_past_sessions(stream):
    courses = get_courses(stream)
    c_ids = [c['id'] for c in courses]
    if not c_ids: return []
    return supabase.table('sessions').select("*, courses(name)").in_('course_id', c_ids).order('date_time', desc=True).limit(20).execute().data

# --- Écriture BDD ---
def save_attendance(course_id, date, present_ids, all_students):
    try:
        sess = supabase.table('sessions').insert({"course_id": course_id, "date_time": date.isoformat()}).execute()
        sess_id = sess.data[0]['id']
        records = [{"session_id": sess_id, "student_id": s['id'], "status": "PRESENT" if s['id'] in present_ids else "ABSENT"} for s in all_students]
        supabase.table('attendance').insert(records).execute()
        return True
    except: return False

def update_correction(session_id, presence_map, all_students):
    try:
        supabase.table('attendance').delete().eq('session_id', session_id).execute()
        records = [{"session_id": session_id, "student_id": s['id'], "status": "PRESENT" if presence_map.get(s['id']) else "ABSENT"} for s in all_students]
        supabase.table('attendance').insert(records).execute()
        return True
    except: return False

# ==============================================================================
# 4. INTERFACE UTILISATEUR (FRONTEND)
# ==============================================================================
init_session()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=120)
    st.markdown("### 🏛️ EPL - GESTION")
    
    app_mode = option_menu(
        menu_title=None,
        options=["Espace Étudiant", "Espace Staff"],
        icons=["person-circle", "shield-lock-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "#f1f5f9", "border-radius": "10px"},
            "nav-link": {"font-weight": "700", "color": "#334155"},
            "nav-link-selected": {"background-color": "#1e293b", "color": "white"},
        }
    )
    st.divider()
    st.caption("v5.0 Stable • OB")

# ==============================================================================
# A. ESPACE ÉTUDIANT (PUBLIC - HERO MODERNE)
# ==============================================================================
if app_mode == "Espace Étudiant":
    
    # Hero Moderne
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">PORTAIL ÉTUDIANT</div>
        <div class="hero-subtitle">
            Consultation des relevés d'assiduité et dossier académique numérique.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Barre de recherche (Carte Flottante)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:15px; border:2px solid #94a3b8; margin-top:-40px; position:relative; z-index:10; box-shadow:0 10px 20px rgba(0,0,0,0.1);">
            <h5 style="margin:0 0 10px 0; color:#334155;">🔎 IDENTIFICATION</h5>
        """, unsafe_allow_html=True)
        search = st.text_input("Search", placeholder="Matricule (ex: LF-GC-001) ou Nom", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("CONSULTER MON DOSSIER", type="primary", use_container_width=True):
            if not search: st.warning("Veuillez entrer un matricule.")
            else:
                with st.spinner("Chargement..."):
                    res = get_student_details(search.strip())
                    time.sleep(0.5)
                    
                    if res:
                        stu = res[0]
                        st.session_state['found_student'] = stu
                    else:
                        st.session_state['found_student'] = None
                        st.error("❌ Dossier introuvable.")

    # Affichage Résultats
    if 'found_student' in st.session_state and st.session_state['found_student']:
        s = st.session_state['found_student']
        
        st.markdown("---")
        
        # En-tête Profil
        avatar = "https://img.icons8.com/ios-filled/100/1e293b/student-male.png" if "M" in str(s.get('gender')).upper() else "https://img.icons8.com/ios-filled/100/1e293b/student-female.png"
        
        col_pic, col_info = st.columns([1, 4])
        with col_pic:
            st.markdown(f'<div style="text-align:center; background:white; border-radius:50%; padding:10px; border:3px solid #1e293b; width:100px; height:100px; display:flex; align-items:center; justify-content:center; margin:auto;"><img src="{avatar}" width="60"></div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(f"""
            <h2 style="margin:0; font-size:2.2rem; color:#1e293b;">{s['last_name']} <span style="font-weight:500; color:#475569;">{s['first_name']}</span></h2>
            <div style="margin-top:10px;">
                <span style="background:#1e293b; color:white !important; padding:6px 15px; border-radius:6px; font-weight:700;">{s['student_id']}</span>
                <span style="background:#cbd5e1; color:#1e293b !important; padding:6px 15px; border-radius:6px; font-weight:700; margin-left:10px;">{s['stream']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Cartes Stats
        pct = float(s['attendance_percentage'])
        color = "#15803d" if pct >= 75 else "#b45309" if pct >= 50 else "#b91c1c"

        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 8px solid {color};">
                <p style="margin:0; font-size:0.9rem;">TAUX DE PRÉSENCE</p>
                <h1 style="color:{color} !important; font-size:3rem; margin:5px 0;">{pct}%</h1>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="metric-card">
                <p style="margin:0; font-size:0.9rem;">SESSIONS</p>
                <h1 style="color:#1e293b !important; font-size:3rem; margin:5px 0;">{s['present_count']}<span style="font-size:1.5rem; color:#64748b;">/{s['total_sessions']}</span></h1>
            </div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="metric-card">
                <p style="margin:0; font-size:0.9rem;">ABSENCES</p>
                <h1 style="color:#b91c1c !important; font-size:3rem; margin:5px 0;">{s['absent_count']}</h1>
            </div>""", unsafe_allow_html=True)

        # Graphique & Info
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("##### 📊 RÉPARTITION VISUELLE")
            df_chart = pd.DataFrame({"Statut": ["Présence", "Absence"], "Valeur": [s['present_count'], s['absent_count']]})
            c = alt.Chart(df_chart).mark_arc(innerRadius=60).encode(
                theta="Valeur", color=alt.Color("Statut", scale=alt.Scale(range=["#15803d", "#b91c1c"])), tooltip=["Statut", "Valeur"]
            )
            st.altair_chart(c, use_container_width=True)
        
        with g2:
            st.markdown("##### ℹ️ STATUT")
            if pct >= 75: st.success("✅ **EXCELLENT** : Assiduité conforme.")
            elif pct >= 50: st.warning("⚠️ **MOYEN** : Attention au seuil critique.")
            else: st.error("🚨 **DANGER** : Présence insuffisante.")

# ==============================================================================
# B. ESPACE STAFF (PRIVÉ)
# ==============================================================================
elif app_mode == "Espace Staff":
    
    # 1. Login
    if not st.session_state['user_role']:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns([1,1,1])
        with col_c2:
            st.markdown('<div class="metric-card"><h3>🔐 ACCÈS STAFF</h3>', unsafe_allow_html=True)
            pwd = st.text_input("Mot de passe", type="password")
            if st.button("CONNEXION", use_container_width=True):
                if login(pwd): st.rerun()
                else: st.error("Accès refusé.")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. Dashboard
    else:
        with st.sidebar:
            st.success(f"👤 **{st.session_state['user_role']}**")
            
            opts = []
            role = st.session_state['user_role']
            if role == 'DELEGATE': opts = ["Faire l'Appel"]
            elif role == 'PROF': opts = ["Tableau de Bord", "Alertes", "Data Explorer"]
            elif role == 'ADMIN': opts = ["Corrections", "Faire l'Appel (Admin)", "Stats Globales"]
            opts.append("Déconnexion")
            
            nav = option_menu("Menu", opts, icons=['pencil', 'exclamation', 'table', 'door-open'], default_index=0)
            
            if nav == "Déconnexion":
                st.session_state.clear()
                st.rerun()

        # --- MODULES ---
        if nav in ["Faire l'Appel", "Faire l'Appel (Admin)"]:
            st.title("📝 Saisie des Présences")
            stream = st.session_state['user_scope'] if role == 'DELEGATE' else st.selectbox("Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
            
            c1, c2 = st.columns(2)
            courses = get_courses(stream)
            cmap = {c['name']: c['id'] for c in courses}
            matiere = c1.selectbox("Matière", list(cmap.keys()) if courses else [])
            date = c2.date_input("Date", datetime.now())
            
            if st.button("CHARGER LA LISTE", type="primary"):
                st.session_state['ctx'] = {'studs': get_students(stream), 'cid': cmap[matiere], 'cname': matiere}
            
            if 'ctx' in st.session_state:
                st.divider()
                st.markdown(f"#### 📅 {st.session_state['ctx']['cname']}")
                with st.form("appel"):
                    ids = []
                    cols = st.columns(3)
                    for i, s in enumerate(st.session_state['ctx']['studs']):
                        if cols[i%3].checkbox(f"{s['last_name']} {s['first_name']}", value=True, key=s['id']):
                            ids.append(s['id'])
                    if st.form_submit_button("💾 ENREGISTRER", type="primary", use_container_width=True):
                        if save_attendance(st.session_state['ctx']['cid'], date, ids, st.session_state['ctx']['studs']):
                            st.balloons()
                            st.success("Enregistré !")
                            del st.session_state['ctx']
                            time.sleep(1)
                            st.rerun()

        elif nav == "Corrections":
            st.title("🛠️ Correction Admin")
            sf = st.selectbox("Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
            hists = get_past_sessions(sf)
            if hists:
                s_dict = {f"{s['date_time'][:10]} | {s['courses']['name']}": s['id'] for s in hists}
                sel_s = st.selectbox("Séance à corriger", list(s_dict.keys()))
                if st.button("CHARGER DONNÉES"):
                    st.session_state['edit_ctx'] = {
                        'sid': s_dict[sel_s],
                        'studs': get_students(sf),
                        'recs': supabase.table('attendance').select("*").eq('session_id', s_dict[sel_s]).execute().data
                    }
            
            if 'edit_ctx' in st.session_state:
                p_set = {r['student_id'] for r in st.session_state['edit_ctx']['recs'] if r['status'] == 'PRESENT'}
                df_e = pd.DataFrame([{"ID": s['id'], "Nom": f"{s['last_name']} {s['first_name']}", "Présent": s['id'] in p_set} for s in st.session_state['edit_ctx']['studs']])
                res_df = st.data_editor(df_e, column_config={"Présent": st.column_config.CheckboxColumn(default=False)}, disabled=["ID","Nom"], hide_index=True, use_container_width=True)
                
                if st.button("💾 SAUVEGARDER CORRECTIONS", type="primary"):
                    pmap = dict(zip(res_df['ID'], res_df['Présent']))
                    if update_correction(st.session_state['edit_ctx']['sid'], pmap, st.session_state['edit_ctx']['studs']):
                        st.success("Corrigé !")
                        time.sleep(1)
                        st.rerun()

        elif nav in ["Tableau de Bord", "Stats Globales"]:
            st.title("📊 Statistiques")
            df = pd.DataFrame(get_global_stats())
            if not df.empty:
                sel_f = st.multiselect("Filières", df['stream'].unique(), default=df['stream'].unique())
                dff = df[df['stream'].isin(sel_f)]
                c1, c2 = st.columns(2)
                c1.metric("Moyenne", f"{dff['attendance_percentage'].mean():.1f}%")
                c2.metric("Effectif", len(dff))
                st.altair_chart(alt.Chart(dff).mark_bar().encode(x=alt.X("attendance_percentage", bin=True), y='count()', color='stream'), use_container_width=True)

        elif nav == "Alertes":
            st.title("🚨 Zone de Vigilance (<50%)")
            df = pd.DataFrame(get_global_stats())
            if not df.empty:
                red = df[df['attendance_percentage'] < 50]
                if not red.empty: st.dataframe(red[['last_name', 'first_name', 'stream', 'attendance_percentage']], use_container_width=True)
                else: st.success("R.A.S.")

        elif nav == "Data Explorer":
            st.title("🔎 Explorateur")
            st.dataframe(pd.DataFrame(get_global_stats()), use_container_width=True)
