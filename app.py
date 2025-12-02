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
    /* Amélioration visuelle des tableaux */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTION DES MOTS DE PASSE ---
CREDENTIALS = {
    "ADMIN": "light3993",
    "PROF": "ayeleh@edo",
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
    st.error("🚨 Clés Supabase manquantes ! Ajoutez-les dans .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 4. FONCTIONS MÉTIER (BACKEND) ---

def get_session_state():
    if 'user_role' not in st.session_state: st.session_state['user_role'] = None
    if 'user_scope' not in st.session_state: st.session_state['user_scope'] = None

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
        st.session_state['user_scope'] = CREDENTIALS["DELEGATES"][password]
        return True
    return False

# -- Lectures de données (avec Cache pour performance) --

@st.cache_data(ttl=600)
def get_courses(stream):
    """Récupère les cours pour une filière donnée"""
    try:
        return supabase.table('courses').select("*").eq('stream_target', stream).execute().data
    except Exception:
        return []

@st.cache_data(ttl=60) # Cache court pour avoir les étudiants à jour
def get_students(stream):
    """Récupère la liste des étudiants"""
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

# -- Écritures de données (Critique) --

def save_attendance(course_id, date_obj, present_ids, all_students):
    """
    Logique robuste :
    1. Vérifie si une session existe pour ce cours à cette date.
    2. Sinon, la crée.
    3. Enregistre les présences via UPSERT (mise à jour si existant).
    """
    try:
        date_iso = date_obj.isoformat()

        # 1. Gestion de la Session (Get or Create)
        # On cherche si la session existe déjà
        existing_session = supabase.table('sessions')\
            .select("id")\
            .eq("course_id", course_id)\
            .eq("date_time", date_iso)\
            .execute()

        if existing_session.data:
            sess_id = existing_session.data[0]['id']
        else:
            # Création nouvelle session
            new_sess = supabase.table('sessions').insert({
                "course_id": course_id, 
                "date_time": date_iso
            }).execute()
            sess_id = new_sess.data[0]['id']

        # 2. Préparation des données de présence
        records = []
        for s in all_students:
            status = "PRESENT" if s['id'] in present_ids else "ABSENT"
            records.append({
                "session_id": sess_id,
                "student_id": s['id'],
                "status": status
            })

        # 3. Batch Upsert (Rapide et Sûr)
        supabase.table('attendance').upsert(
            records, 
            on_conflict='session_id, student_id'
        ).execute()

        return True

    except Exception as e:
        st.error(f"❌ Erreur Technique : {e}")
        return False

# --- FONCTIONS SUPER ADMIN ---

def get_past_sessions(stream):
    """Récupère l'historique des sessions pour correction"""
    # 1. Récupérer les ID des cours de la filière
    courses = get_courses(stream)
    if not courses: return []
    course_ids = [c['id'] for c in courses]
    
    # 2. Récupérer les sessions liées (avec le nom du cours via la relation)
    # Note : Assurez-vous d'avoir une Foreign Key 'course_id' dans Supabase
    try:
        response = supabase.table('sessions')\
            .select("*, courses(name)")\
            .in_('course_id', course_ids)\
            .order('date_time', desc=True)\
            .limit(20)\
            .execute()
        return response.data
    except Exception as e:
        st.warning(f"Impossible de charger l'historique (vérifiez les FK): {e}")
        return []

def update_attendance_correction(session_id, updated_presence_map, all_students):
    """Met à jour une session passée via Upsert"""
    try:
        records = []
        for s in all_students:
            # Si True dans la map -> PRESENT, Sinon -> ABSENT
            status = "PRESENT" if updated_presence_map.get(s['id'], False) else "ABSENT"
            records.append({
                "session_id": session_id, 
                "student_id": s['id'], 
                "status": status
            })
            
        supabase.table('attendance').upsert(
            records,
            on_conflict='session_id, student_id'
        ).execute()
        return True
    except Exception as e:
        st.error(str(e))
        return False

# --- STATISTIQUES (Vue SQL) ---
def get_global_stats():
    """Appelle la vue SQL 'student_stats' pré-calculée dans Supabase"""
    try:
        return supabase.from_('student_stats').select("*").execute().data
    except Exception:
        # Fallback si la vue n'existe pas encore
        st.warning("La vue SQL 'student_stats' n'est pas trouvée dans Supabase.")
        return []

# =========================================================
# INTERFACE UTILISATEUR
# =========================================================

get_session_state()

# 1. LOGIN SCREEN
if not st.session_state['user_role']:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=150)
        st.markdown("<h3 style='text-align: center;'>Portail Sécurisé EPL</h3>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe d'accès", type="password")
        if st.button("Connexion", use_container_width=True):
            if login(pwd):
                st.success(f"Bienvenue, accès {st.session_state['user_role']}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Accès Refusé.")
    st.stop()

# 2. LOGGED IN INTERFACE
with st.sidebar:
    st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=80)
    st.markdown(f"**Rôle :** {st.session_state['user_role']}")
    if st.session_state['user_scope'] != 'ALL':
        st.markdown(f"**Filière :** {st.session_state['user_scope']}")
    
    st.divider()
    
    # MENU DYNAMIQUE
    options = []
    if st.session_state['user_role'] == 'DELEGATE':
        options = ["Faire l'Appel"]
    elif st.session_state['user_role'] == 'PROF':
        options = ["Tableau de Bord Prof", "Alertes Absences", "Explorer les Données"]
    elif st.session_state['user_role'] == 'ADMIN':
        options = ["Super Admin", "Correction d'Erreurs", "Faire l'Appel (Force)", "Stats Globales"]
        
    options.append("Déconnexion")
    
    selected = option_menu("Menu Principal", options, 
        icons=['pencil', 'people', 'graph-up', 'shield', 'eraser', 'box-arrow-right'], 
        menu_icon="cast", default_index=0)

    if selected == "Déconnexion":
        st.session_state['user_role'] = None
        st.session_state['user_scope'] = None
        st.rerun()

# --- PAGE: FAIRE L'APPEL ---
if selected == "Faire l'Appel" or (selected == "Faire l'Appel (Force)" and st.session_state['user_role'] == 'ADMIN'):
    st.title("📝 Nouvelle Feuille de Présence")
    
    # Sélecteur de filière
    if st.session_state['user_role'] == 'DELEGATE':
        target_stream = st.session_state['user_scope']
        st.info(f"📍 Filière : **{target_stream}**")
    else:
        target_stream = st.selectbox("Choisir Filière (Mode Admin)", ["LT", "GC", "IABD", "IS", "GE", "GM"])

    # Sélecteurs Matière / Date
    c1, c2 = st.columns(2)
    courses = get_courses(target_stream)
    
    if not courses:
        st.warning("Aucun cours trouvé pour cette filière.")
    else:
        course_map = {c['name']: c['id'] for c in courses}
        chosen_course = c1.selectbox("Matière", list(course_map.keys()))
        chosen_date = c2.date_input("Date du cours", datetime.now())

        if st.button("Charger la liste des étudiants", type="primary"):
            st.session_state['attendance_context'] = {
                'students': get_students(target_stream),
                'course_id': course_map[chosen_course],
                'course_name': chosen_course
            }

    # Formulaire de Coche
    if 'attendance_context' in st.session_state:
        ctx = st.session_state['attendance_context']
        st.divider()
        st.subheader(f"Appel : {ctx['course_name']} ({len(ctx['students'])} étudiants)")
        
        with st.form("delegate_form"):
            present_ids = []
            
            # Grille responsive
            cols = st.columns(3)
            for i, s in enumerate(ctx['students']):
                # Case cochée par défaut (Présomption de présence)
                is_checked = cols[i%3].checkbox(f"{s['last_name']} {s['first_name']}", value=True, key=f"chk_{s['id']}")
                if is_checked:
                    present_ids.append(s['id'])
            
            st.markdown("---")
            submitted = st.form_submit_button("✅ Valider et Envoyer", use_container_width=True)
            
            if submitted:
                with st.spinner("Enregistrement en cours..."):
                    success = save_attendance(
                        ctx['course_id'], 
                        chosen_date, 
                        present_ids, 
                        ctx['students']
                    )
                    
                    if success:
                        st.balloons()
                        st.success("Appel enregistré avec succès dans la base de données !")
                        del st.session_state['attendance_context']
                        time.sleep(2)
                        st.rerun()

# --- PAGE: CORRECTION D'ERREURS ---
elif selected == "Correction d'Erreurs":
    st.title("🛠️ Correction d'Appel (Admin)")
    st.info("Permet de modifier rétroactivement les présences d'une session passée.")
    
    col_f, col_s = st.columns(2)
    stream_fix = col_f.selectbox("1. Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
    
    sessions_data = get_past_sessions(stream_fix)
    
    if sessions_data:
        # Création des labels pour le menu déroulant
        sess_options = {}
        for s in sessions_data:
            # Gestion sécurisée si le join a échoué
            course_name = s['courses']['name'] if s.get('courses') else "Matière Inconnue"
            label = f"{s['date_time'][:10]} | {course_name}"
            sess_options[label] = s['id']
            
        chosen_sess_label = col_s.selectbox("2. Sélectionner la séance", list(sess_options.keys()))
        
        if st.button("Charger les données"):
            chosen_sess_id = sess_options[chosen_sess_label]
            
            # Récupération données pour éditeur
            all_students = get_students(stream_fix)
            
            # Récupération état actuel
            attendance_records = supabase.table('attendance').select("*").eq('session_id', chosen_sess_id).execute().data
            present_set = {r['student_id'] for r in attendance_records if r['status'] == 'PRESENT'}
            
            # Dataframe pour l'éditeur
            data_for_editor = []
            for s in all_students:
                data_for_editor.append({
                    "ID": s['id'],
                    "Nom": s['last_name'],
                    "Prénom": s['first_name'],
                    "Présent": (s['id'] in present_set)
                })
            
            st.session_state['editor_data'] = pd.DataFrame(data_for_editor)
            st.session_state['fix_session_id'] = chosen_sess_id
            st.session_state['fix_students_ref'] = all_students

    # Affichage Éditeur
    if 'editor_data' in st.session_state:
        st.divider()
        st.markdown("#### Modifier les états :")
        
        edited_df = st.data_editor(
            st.session_state['editor_data'],
            column_config={
                "Présent": st.column_config.CheckboxColumn("Présence", help="Cocher si présent"),
                "ID": st.column_config.Column(disabled=True),
                "Nom": st.column_config.Column(disabled=True),
                "Prénom": st.column_config.Column(disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
        
        if st.button("💾 SAUVEGARDER CORRECTIONS", type="primary", use_container_width=True):
            # Mapping ID -> Boolean
            updated_map = dict(zip(edited_df['ID'], edited_df['Présent']))
            
            if update_attendance_correction(st.session_state['fix_session_id'], updated_map, st.session_state['fix_students_ref']):
                st.success("Modifications enregistrées !")
                time.sleep(1.5)
                del st.session_state['editor_data']
                st.rerun()

# --- PAGES STATISTIQUES (PROF & ADMIN) ---
elif selected in ["Tableau de Bord Prof", "Stats Globales", "Alertes Absences", "Explorer les Données"]:
    
    # Chargement unique des données
    df = pd.DataFrame(get_global_stats())
    
    if df.empty:
        st.warning("Pas de données statistiques disponibles (Vue SQL vide ou inexistante).")
    else:
        # --- SOUS-PAGE : DASHBOARD ---
        if selected in ["Tableau de Bord Prof", "Stats Globales"]:
            st.title("📊 Tableau de Bord Académique")
            
            # Filtres
            filieres_dispo = df['stream'].unique()
            filieres = st.multiselect("Filtrer par Filière", filieres_dispo, default=filieres_dispo)
            df_filtered = df[df['stream'].isin(filieres)]
            
            # KPIs
            col1, col2, col3 = st.columns(3)
            avg = df_filtered['attendance_percentage'].mean()
            col1.metric("Taux de Présence Moyen", f"{avg:.1f}%")
            col2.metric("Étudiants Suivis", len(df_filtered))
            # Calcul approximatif sessions max
            max_sess = df_filtered['total_sessions'].max() if 'total_sessions' in df_filtered.columns else 0
            col3.metric("Sessions de Cours (Max)", max_sess)
            
            st.divider()
            
            # Graphes Altair
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Distribution des Taux de Présence**")
                chart = alt.Chart(df_filtered).mark_bar().encode(
                    x=alt.X("attendance_percentage", bin=True, title="Taux %"),
                    y=alt.Y('count()', title="Nb Étudiants"),
                    color='stream'
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                
            with c2:
                st.markdown("**Comparatif par Filière**")
                chart2 = alt.Chart(df_filtered).mark_boxplot().encode(
                    x='stream',
                    y=alt.Y('attendance_percentage', title="Taux %"),
                    color='stream'
                )
                st.altair_chart(chart2, use_container_width=True)

        # --- SOUS-PAGE : ALERTES ---
        elif selected == "Alertes Absences":
            st.title("🚨 Étudiants en Difficulté (< 50%)")
            
            red_list = df[df['attendance_percentage'] < 50].sort_values('attendance_percentage')
            
            if red_list.empty:
                st.success("Aucun étudiant en dessous de 50%.")
            else:
                st.error(f"{len(red_list)} étudiants nécessitent une attention particulière.")
                
                st.dataframe(
                    red_list[['first_name', 'last_name', 'stream', 'attendance_percentage', 'absent_count']],
                    column_config={
                        "attendance_percentage": st.column_config.ProgressColumn("Taux", format="%.1f%%", min_value=0, max_value=100),
                        "absent_count": st.column_config.NumberColumn("Absences Total"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.button("Copier la liste pour email"):
                    st.toast("Liste copiée (simulation)", icon="📧")

        # --- SOUS-PAGE : EXPLORATEUR ---
        elif selected == "Explorer les Données":
            st.title("🔎 Explorateur Brut")
            st.dataframe(df, use_container_width=True, hide_index=True)
