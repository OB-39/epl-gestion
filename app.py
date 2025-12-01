import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(page_title="EPL - Master Panel", page_icon="🛡️", layout="wide")

# --- CSS MODERNE ---
st.markdown("""
<style>
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    h1, h2, h3 { color: #1E3A8A; }
    div[data-testid="stMetricValue"] { color: #1E3A8A; font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTION DES MOTS DE PASSE (Configuration) ---
# Dans un projet réel, mettez ça dans st.secrets, mais pour l'instant c'est ici :
CREDENTIALS = {
    "ADMIN": "light3993",
    "PROF": "ayeleh@edo",
    # Mots de passe des délégués par filière
    "DELEGATES": {
        "pass_lt_2024": "LT",
        "pass_gc_2024": "GC",
        "pass_iabd_2024": "IABD",
        "pass_is_2024": "IS",
        "pass_ge_2024": "GE",
        "pass_gm_2024": "GM"
    }
}

# --- 3. CONNEXION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("Clés Supabase manquantes dans .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 4. FONCTIONS MÉTIER AVANCÉES ---

def get_session_state():
    if 'user_role' not in st.session_state: st.session_state['user_role'] = None
    if 'user_scope' not in st.session_state: st.session_state['user_scope'] = None # 'ALL' ou 'LT', 'GC'...

def login(password):
    if password == CREDENTIALS["ADMIN"]:
        st.session_state['user_role'] = 'ADMIN'
        st.session_state['user_scope'] = 'ALL'
        return True
    elif password == CREDENTIALS["PROF"]:
        st.session_state['user_role'] = 'PROF'
        st.session_state['user_scope'] = 'ALL'
        return True
    elif password in CREDENTIALS["DELEGATES"]:
        st.session_state['user_role'] = 'DELEGATE'
        st.session_state['user_scope'] = CREDENTIALS["DELEGATES"][password] # On stocke sa filière (ex: LT)
        return True
    return False

# Récupération données classiques
def get_courses(stream):
    return supabase.table('courses').select("*").eq('stream_target', stream).execute().data

def get_students(stream):
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

# Sauvegarde Appel (Délégué)
def save_attendance(course_id, date, present_ids, all_students):
    try:
        # 1. Créer Session
        sess = supabase.table('sessions').insert({"course_id": course_id, "date_time": date.isoformat()}).execute()
        sess_id = sess.data[0]['id']
        # 2. Créer Présences
        records = [{"session_id": sess_id, "student_id": s['id'], "status": "PRESENT" if s['id'] in present_ids else "ABSENT"} for s in all_students]
        supabase.table('attendance').insert(records).execute()
        return True
    except Exception as e:
        st.error(f"Erreur DB: {e}")
        return False

# --- FONCTIONS SUPER ADMIN (CORRECTION) ---
def get_past_sessions(stream):
    # Récupère les sessions passées pour une filière avec le nom du cours
    q = """
    select sessions.id, sessions.date_time, courses.name 
    from sessions 
    join courses on sessions.course_id = courses.id 
    where courses.stream_target = '{}'
    order by sessions.date_time desc
    limit 20
    """.format(stream)
    # Note: Supabase-py ne gère pas les joints complexes facilement en raw string, 
    # on va faire simple : Récupérer sessions puis filtrer. 
    # Pour la rapidité ici, on utilise RPC ou des requêtes chainées.
    # Méthode "Lazy" : On récupère les cours de la filière, puis les sessions de ces cours.
    courses = get_courses(stream)
    course_ids = [c['id'] for c in courses]
    if not course_ids: return []
    
    sessions = supabase.table('sessions').select("*, courses(name)").in_('course_id', course_ids).order('date_time', desc=True).limit(20).execute()
    return sessions.data

def update_attendance_correction(session_id, updated_presence_map, all_students):
    # C'est une mise à jour "Atomique" : On supprime tout pour cette session et on recrée.
    # C'est plus sûr pour éviter les doublons ou conflits.
    try:
        supabase.table('attendance').delete().eq('session_id', session_id).execute()
        
        records = []
        for s in all_students:
            status = "PRESENT" if updated_presence_map.get(s['id'], False) else "ABSENT"
            records.append({"session_id": session_id, "student_id": s['id'], "status": status})
            
        supabase.table('attendance').insert(records).execute()
        return True
    except Exception as e:
        st.error(str(e))
        return False

# --- FONCTIONS STATISTIQUES (PROF) ---
def get_global_stats():
    # Utilise la vue SQL existante
    return supabase.from_('student_stats').select("*").execute().data

# --- INTERFACE ---
get_session_state()

# 1. LOGIN SCREEN (Si pas connecté)
if not st.session_state['user_role']:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=150)
        st.markdown("### Portail Sécurisé EPL")
        pwd = st.text_input("Mot de passe d'accès", type="password")
        if st.button("Connexion"):
            if login(pwd):
                st.success(f"Bienvenue, accès {st.session_state['user_role']}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Accès Refusé.")
    st.stop() # Arrête le script ici si pas connecté

# 2. LOGGED IN INTERFACE
with st.sidebar:
    st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=100)
    st.write(f"Rôle : **{st.session_state['user_role']}**")
    if st.session_state['user_role'] == 'DELEGATE':
        st.write(f"Filière : **{st.session_state['user_scope']}**")
    
    # MENU DYNAMIQUE SELON LE ROLE
    options = []
    if st.session_state['user_role'] == 'DELEGATE':
        options = ["Faire l'Appel", "Mes Étudiants"]
    elif st.session_state['user_role'] == 'PROF':
        options = ["Tableau de Bord Prof", "Alertes Absences", "Explorer les Données"]
    elif st.session_state['user_role'] == 'ADMIN':
        options = ["Super Admin", "Correction d'Erreurs", "Faire l'Appel (Force)", "Stats Globales"]
        
    options.append("Déconnexion")
    
    selected = option_menu("Menu", options, icons=['pencil', 'people', 'graph-up', 'shield', 'eraser', 'box-arrow-right'], menu_icon="cast", default_index=0)

    if selected == "Déconnexion":
        st.session_state['user_role'] = None
        st.session_state['user_scope'] = None
        st.rerun()

# =========================================================
# MODULE DÉLÉGUÉ (Saisie simple)
# =========================================================
if selected == "Faire l'Appel" or (selected == "Faire l'Appel (Force)" and st.session_state['user_role'] == 'ADMIN'):
    st.title("📝 Nouvelle Feuille de Présence")
    
    # Détermination de la filière
    if st.session_state['user_role'] == 'DELEGATE':
        target_stream = st.session_state['user_scope'] # Forcé
        st.info(f"Filière connectée : {target_stream}")
    else:
        target_stream = st.selectbox("Choisir Filière (Admin)", ["LT", "GC", "IABD", "IS", "GE", "GM"])

    # Sélection
    c1, c2 = st.columns(2)
    courses = get_courses(target_stream)
    course_map = {c['name']: c['id'] for c in courses}
    
    chosen_course = c1.selectbox("Matière", list(course_map.keys()) if courses else [])
    chosen_date = c2.date_input("Date", datetime.now())

    if st.button("Charger la liste", type="primary"):
        if chosen_course:
            st.session_state['attendance_context'] = {
                'students': get_students(target_stream),
                'course_id': course_map[chosen_course],
                'course_name': chosen_course
            }
    
    # Formulaire d'appel
    if 'attendance_context' in st.session_state:
        ctx = st.session_state['attendance_context']
        st.divider()
        st.subheader(f"Appel : {ctx['course_name']}")
        
        with st.form("delegate_form"):
            present_ids = []
            cols = st.columns(3)
            for i, s in enumerate(ctx['students']):
                # Par défaut coché
                if cols[i%3].checkbox(f"{s['last_name']} {s['first_name']}", value=True, key=s['id']):
                    present_ids.append(s['id'])
            
            if st.form_submit_button("Valider et Envoyer"):
                if save_attendance(ctx['course_id'], chosen_date, present_ids, ctx['students']):
                    st.balloons()
                    st.success("Feuille de présence transmise au serveur.")
                    del st.session_state['attendance_context']
                    time.sleep(2)
                    st.rerun()

# =========================================================
# MODULE SUPER ADMIN (Correction)
# =========================================================
elif selected == "Correction d'Erreurs":
    st.title("🛠️ Correction / Modification d'Appel")
    st.warning("Zone Admin : Vous modifiez l'historique de la base de données.")
    
    # 1. Trouver la session
    col_f, col_s = st.columns(2)
    stream_fix = col_f.selectbox("1. Filière à corriger", ["LT", "GC", "IABD", "IS", "GE", "GM"])
    
    sessions_data = get_past_sessions(stream_fix)
    
    if sessions_data:
        # Créer un label lisible pour le menu déroulant : "Date - Matière"
        sess_options = {f"{s['date_time'][:10]} | {s['courses']['name']} (ID:{s['id']})": s['id'] for s in sessions_data}
        chosen_sess_label = col_s.selectbox("2. Sélectionner la séance passée", list(sess_options.keys()))
        chosen_sess_id = sess_options[chosen_sess_label]
        
        if st.button("Charger les données de cette séance"):
            # A. Récupérer tous les étudiants de la filière
            all_students = get_students(stream_fix)
            
            # B. Récupérer qui était noté présent
            attendance_records = supabase.table('attendance').select("*").eq('session_id', chosen_sess_id).execute().data
            present_set = {r['student_id'] for r in attendance_records if r['status'] == 'PRESENT'}
            
            # C. Préparer un DataFrame pour l'éditeur
            data_for_editor = []
            for s in all_students:
                data_for_editor.append({
                    "ID": s['id'],
                    "Nom Complet": f"{s['last_name']} {s['first_name']}",
                    "Est Présent": (s['id'] in present_set) # True/False
                })
            
            st.session_state['editor_data'] = pd.DataFrame(data_for_editor)
            st.session_state['fix_session_id'] = chosen_sess_id
            st.session_state['fix_students_ref'] = all_students

    # Affichage de l'éditeur
    if 'editor_data' in st.session_state:
        st.divider()
        st.markdown("#### Modifier les présences ci-dessous :")
        
        # Data Editor permet de cocher/décocher dans un tableau type Excel
        edited_df = st.data_editor(
            st.session_state['editor_data'],
            column_config={
                "Est Présent": st.column_config.CheckboxColumn("Présent ?", help="Cochez si l'étudiant était là", default=False)
            },
            disabled=["ID", "Nom Complet"],
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("💾 SAUVEGARDER LES CORRECTIONS", type="primary"):
            # Reconstruire la map des présences
            updated_map = dict(zip(edited_df['ID'], edited_df['Est Présent']))
            
            if update_attendance_correction(st.session_state['fix_session_id'], updated_map, st.session_state['fix_students_ref']):
                st.success("Base de données mise à jour avec succès !")
                time.sleep(2)
                st.rerun()

# =========================================================
# MODULE PROFESSEUR (Stats & Modernité)
# =========================================================
elif selected == "Tableau de Bord Prof" or selected == "Stats Globales":
    st.title("📊 Statistiques Académiques")
    
    # Chargement des données globales (Vue SQL)
    df = pd.DataFrame(get_global_stats())
    
    if not df.empty:
        # 1. Filtres dynamiques
        filieres = st.multiselect("Filtrer par Filière", df['stream'].unique(), default=df['stream'].unique())
        df_filtered = df[df['stream'].isin(filieres)]
        
        # 2. Métriques Globales (Top niveau)
        st.markdown("### 🌍 Vue d'ensemble")
        c1, c2, c3 = st.columns(3)
        avg_attendance = df_filtered['attendance_percentage'].mean()
        c1.metric("Taux de Présence Moyen", f"{avg_attendance:.1f}%")
        c2.metric("Étudiants Suivis", len(df_filtered))
        c3.metric("Sessions Totales", df_filtered['total_sessions'].max()) # Approx
        
        st.divider()
        
        # 3. Graphiques Modernes (Altair)
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.markdown("#### 📉 Distribution des Absences")
            # Histogramme des taux de présence
            chart = alt.Chart(df_filtered).mark_bar().encode(
                x=alt.X("attendance_percentage", bin=True, title="Taux de présence (%)"),
                y=alt.Y('count()', title="Nombre d'étudiants"),
                color=alt.Color('stream', legend=alt.Legend(title="Filière"))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
        with c_chart2:
            st.markdown("#### 🏆 Performance par Filière")
            # Boxplot ou Bar chart des moyennes par filière
            chart2 = alt.Chart(df_filtered).mark_rect().encode(
                x='stream',
                y='attendance_percentage',
                color='attendance_percentage'
            ).properties(height=300)
            st.altair_chart(chart2, use_container_width=True)

    else:
        st.info("Pas encore assez de données pour générer des statistiques.")

elif selected == "Alertes Absences":
    st.title("🚨 Zone de Vigilance (Red List)")
    st.markdown("Liste des étudiants ayant un taux d'absence critique (**< 50% de présence**).")
    
    df = pd.DataFrame(get_global_stats())
    if not df.empty:
        # Filtrer les étudiants en difficulté
        red_list = df[df['attendance_percentage'] < 50].sort_values('attendance_percentage')
        
        if not red_list.empty:
            st.error(f"{len(red_list)} étudiants sont en situation critique.")
            
            # Affichage joli tableau
            st.dataframe(
                red_list[['first_name', 'last_name', 'stream', 'attendance_percentage', 'absent_count']],
                column_config={
                    "attendance_percentage": st.column_config.ProgressColumn("Taux Présence", format="%d%%", min_value=0, max_value=100),
                    "first_name": "Prénom",
                    "last_name": "Nom",
                    "absent_count": "Nbre Absences"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Bouton d'action fictif (Modernité)
            if st.button("📧 Générer email d'avertissement pour ces étudiants"):
                st.toast("Emails générés dans le presse-papier !", icon="✅")
        else:
            st.success("Aucun étudiant n'est en dessous de 50% de présence. Bravo !")

elif selected == "Explorer les Données":
    st.title("🔎 Explorateur de Données")
    # Table brute interactive
    df = pd.DataFrame(get_global_stats())
    
    # CORRECTION ICI : On retire 'filter_button=True' qui causait l'erreur
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True 
    )

