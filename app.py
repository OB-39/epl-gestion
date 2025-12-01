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
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    h1, h2, h3 { color: #1E3A8A; }
    div[data-testid="stMetricValue"] { color: #1E3A8A; font-size: 24px; }
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
    st.error("Clés Supabase manquantes dans .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 4. FONCTIONS MÉTIER ---

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

# Récupération données classiques
def get_courses(stream):
    return supabase.table('courses').select("*").eq('stream_target', stream).execute().data

def get_students(stream):
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

# Récupération stats individuelles (Pour la partie publique)
def get_student_details(search_term):
    # Cherche par ID exact
    response = supabase.from_('student_stats').select("*").eq('student_id', search_term).execute()
    # Si pas trouvé, cherche par nom
    if not response.data:
        response = supabase.from_('student_stats').select("*").ilike('last_name', f"%{search_term}%").execute()
    return response.data

# Sauvegarde Appel (Délégué)
def save_attendance(course_id, date, present_ids, all_students):
    try:
        sess = supabase.table('sessions').insert({"course_id": course_id, "date_time": date.isoformat()}).execute()
        sess_id = sess.data[0]['id']
        records = [{"session_id": sess_id, "student_id": s['id'], "status": "PRESENT" if s['id'] in present_ids else "ABSENT"} for s in all_students]
        supabase.table('attendance').insert(records).execute()
        return True
    except Exception as e:
        st.error(f"Erreur DB: {e}")
        return False

# Fonctions Super Admin & Stats
def get_past_sessions(stream):
    courses = get_courses(stream)
    course_ids = [c['id'] for c in courses]
    if not course_ids: return []
    sessions = supabase.table('sessions').select("*, courses(name)").in_('course_id', course_ids).order('date_time', desc=True).limit(20).execute()
    return sessions.data

def update_attendance_correction(session_id, updated_presence_map, all_students):
    try:
        supabase.table('attendance').delete().eq('session_id', session_id).execute()
        records = []
        for s in all_students:
            status = "PRESENT" if updated_presence_map.get(s['id'], False) else "ABSENT"
            records.append({"session_id": session_id, "student_id": s['id'], "status": status})
        supabase.table('attendance').insert(records).execute()
        return True
    except Exception as e:
        return False

def get_global_stats():
    return supabase.from_('student_stats').select("*").execute().data

# --- 5. LOGIQUE D'INTERFACE PRINCIPALE ---
get_session_state()

# Navigation Principale (Sidebar)
with st.sidebar:
    st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=120)
    
    # Choix du Mode : Public ou Privé
    app_mode = option_menu(
        "Navigation", 
        ["Espace Étudiant", "Espace Staff"],
        icons=["person-circle", "lock-fill"],
        menu_icon="list",
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#1E3A8A"}}
    )

# =========================================================
# MODE 1 : ESPACE ÉTUDIANT (PUBLIC)
# =========================================================
if app_mode == "Espace Étudiant":
    st.title("🎓 Mon Portail de Présence")
    st.info("Consultez vos statistiques en temps réel.")
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        search = st.text_input("🔍 Entrez votre Matricule ou Nom :", placeholder="Ex: LF-LT-001")
    
    if search:
        with st.spinner("Recherche..."):
            results = get_student_details(search.strip())
            time.sleep(0.3)
            
            if results:
                for student in results:
                    st.success("Dossier trouvé !")
                    
                    # Carte d'identité
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2 style="margin:0;">{student['first_name']} {student['last_name']}</h2>
                        <p style="color:gray;">{student['stream']} | {student['student_id']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Graphiques
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Taux de Présence", f"{student['attendance_percentage']}%")
                        val = float(student['attendance_percentage']) / 100
                        st.progress(val, text="Niveau de présence")
                    
                    with c2:
                        st.metric("Absences", student['absent_count'], delta_color="inverse")
                        st.metric("Cours Total", student['total_sessions'])
                        
                    with c3:
                        # Donut Chart
                        source = pd.DataFrame({
                            "État": ["Présent", "Absent"],
                            "Valeur": [student['present_count'], student['absent_count']]
                        })
                        base = alt.Chart(source).encode(theta=alt.Theta("Valeur", stack=True))
                        pie = base.mark_arc(outerRadius=45).encode(
                            color=alt.Color("État", scale=alt.Scale(domain=["Présent", "Absent"], range=["#22c55e", "#ef4444"])),
                            tooltip=["État", "Valeur"]
                        )
                        st.altair_chart(pie, use_container_width=True)
            else:
                st.warning("Aucun étudiant trouvé.")

# =========================================================
# MODE 2 : ESPACE STAFF (PRIVÉ & SÉCURISÉ)
# =========================================================
elif app_mode == "Espace Staff":
    
    # A. ÉCRAN DE CONNEXION (Si pas connecté)
    if not st.session_state['user_role']:
        st.title("🔐 Accès Réservé")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.markdown("### Identification")
            pwd = st.text_input("Mot de passe", type="password")
            if st.button("Se Connecter", type="primary"):
                if login(pwd):
                    st.success(f"Bienvenue {st.session_state['user_role']}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Mot de passe invalide.")
    
    # B. TABLEAU DE BORD (Si connecté)
    else:
        # Menu contextuel Staff
        with st.sidebar:
            st.divider()
            st.write(f"Connecté en tant que : **{st.session_state['user_role']}**")
            
            staff_options = []
            if st.session_state['user_role'] == 'DELEGATE':
                staff_options = ["Faire l'Appel"]
            elif st.session_state['user_role'] == 'PROF':
                staff_options = ["Tableau de Bord Prof", "Alertes Absences", "Explorer les Données"]
            elif st.session_state['user_role'] == 'ADMIN':
                staff_options = ["Correction d'Erreurs", "Faire l'Appel (Force)", "Stats Globales"]
            
            staff_options.append("Déconnexion")
            
            selected_staff = option_menu("Menu Staff", staff_options, icons=['grid', 'list-task', 'people', 'x-circle'], menu_icon="gear", default_index=0)
            
            if selected_staff == "Déconnexion":
                st.session_state['user_role'] = None
                st.session_state['user_scope'] = None
                st.rerun()

        # --- LOGIQUE DÉLÉGUÉ / APPEL ---
        if selected_staff == "Faire l'Appel" or selected_staff == "Faire l'Appel (Force)":
            st.title("📝 Nouvelle Feuille de Présence")
            if st.session_state['user_role'] == 'DELEGATE':
                target_stream = st.session_state['user_scope']
                st.info(f"Filière : {target_stream}")
            else:
                target_stream = st.selectbox("Choisir Filière (Admin)", ["LT", "GC", "IABD", "IS", "GE", "GM"])

            c1, c2 = st.columns(2)
            courses = get_courses(target_stream)
            course_map = {c['name']: c['id'] for c in courses}
            chosen_course = c1.selectbox("Matière", list(course_map.keys()) if courses else [])
            chosen_date = c2.date_input("Date", datetime.now())

            if st.button("Charger la liste"):
                if chosen_course:
                    st.session_state['attendance_context'] = {
                        'students': get_students(target_stream),
                        'course_id': course_map[chosen_course],
                        'course_name': chosen_course
                    }
            
            if 'attendance_context' in st.session_state:
                ctx = st.session_state['attendance_context']
                st.divider()
                st.subheader(f"Appel : {ctx['course_name']}")
                with st.form("delegate_form"):
                    present_ids = []
                    cols = st.columns(3)
                    for i, s in enumerate(ctx['students']):
                        if cols[i%3].checkbox(f"{s['last_name']} {s['first_name']}", value=True, key=s['id']):
                            present_ids.append(s['id'])
                    if st.form_submit_button("Valider et Envoyer"):
                        if save_attendance(ctx['course_id'], chosen_date, present_ids, ctx['students']):
                            st.balloons()
                            st.success("Enregistré !")
                            del st.session_state['attendance_context']
                            time.sleep(2)
                            st.rerun()

        # --- LOGIQUE ADMIN CORRECTION ---
        elif selected_staff == "Correction d'Erreurs":
            st.title("🛠️ Correction Admin")
            col_f, col_s = st.columns(2)
            stream_fix = col_f.selectbox("Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
            sessions_data = get_past_sessions(stream_fix)
            
            if sessions_data:
                sess_options = {f"{s['date_time'][:10]} | {s['courses']['name']}": s['id'] for s in sessions_data}
                chosen_lbl = col_s.selectbox("Séance", list(sess_options.keys()))
                chosen_id = sess_options[chosen_lbl]
                
                if st.button("Charger données"):
                    all_studs = get_students(stream_fix)
                    recs = supabase.table('attendance').select("*").eq('session_id', chosen_id).execute().data
                    pres_set = {r['student_id'] for r in recs if r['status'] == 'PRESENT'}
                    data_edit = [{"ID": s['id'], "Nom": f"{s['last_name']} {s['first_name']}", "Présent": (s['id'] in pres_set)} for s in all_studs]
                    st.session_state['edit_data'] = pd.DataFrame(data_edit)
                    st.session_state['edit_sess_id'] = chosen_id
                    st.session_state['edit_ref_studs'] = all_studs

            if 'edit_data' in st.session_state:
                st.divider()
                edited_df = st.data_editor(
                    st.session_state['edit_data'],
                    column_config={"Présent": st.column_config.CheckboxColumn(default=False)},
                    disabled=["ID", "Nom"],
                    hide_index=True,
                    use_container_width=True
                )
                if st.button("Sauvegarder Corrections"):
                    upd_map = dict(zip(edited_df['ID'], edited_df['Présent']))
                    if update_attendance_correction(st.session_state['edit_sess_id'], upd_map, st.session_state['edit_ref_studs']):
                        st.success("Mis à jour !")
                        time.sleep(1)
                        st.rerun()

        # --- LOGIQUE PROF/STATS ---
        elif selected_staff == "Tableau de Bord Prof" or selected_staff == "Stats Globales":
            st.title("📊 Statistiques")
            df = pd.DataFrame(get_global_stats())
            if not df.empty:
                filieres = st.multiselect("Filtrer", df['stream'].unique(), default=df['stream'].unique())
                dff = df[df['stream'].isin(filieres)]
                c1, c2 = st.columns(2)
                c1.metric("Moyenne Présence", f"{dff['attendance_percentage'].mean():.1f}%")
                c2.metric("Sessions", dff['total_sessions'].max())
                
                chart = alt.Chart(dff).mark_bar().encode(
                    x=alt.X("attendance_percentage", bin=True),
                    y='count()',
                    color='stream'
                )
                st.altair_chart(chart, use_container_width=True)

        elif selected_staff == "Alertes Absences":
            st.title("🚨 Zone Rouge (< 50%)")
            df = pd.DataFrame(get_global_stats())
            if not df.empty:
                red = df[df['attendance_percentage'] < 50]
                if not red.empty:
                    st.dataframe(red[['last_name', 'first_name', 'stream', 'attendance_percentage']], use_container_width=True, hide_index=True)
                else:
                    st.success("Aucun étudiant en danger.")

        elif selected_staff == "Explorer les Données":
            st.title("🔎 Explorateur")
            df = pd.DataFrame(get_global_stats())
            st.dataframe(df, use_container_width=True, hide_index=True)
