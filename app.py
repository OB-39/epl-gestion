import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(
    page_title="EPL - Portail de Présence", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME & CSS MODERNE ---
st.markdown("""
<style>
    /* Palette de couleurs EPL: Bleu Nuit (#1E3A8A) et Blanc */
    :root {
        --primary-color: #1E3A8A;
        --background-light: #F8FAFC;
    }
    
    .main {
        background-color: var(--background-light);
    }
    
    /* Cards stylisées */
    .css-card {
        border-radius: 12px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    
    /* Titres */
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #0F172A;
        font-weight: 700;
    }
    
    h1 { margin-bottom: 0.5rem; }
    
    /* Métriques personnalisées */
    .stat-label { font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .stat-value { font-size: 2rem; color: #1E3A8A; font-weight: 800; }
    
    /* Boutons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
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
    st.error("⚠️ Configuration manquante : Vérifiez .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 4. FONCTIONS MÉTIER (INCHANGÉES) ---

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

def get_courses(stream):
    return supabase.table('courses').select("*").eq('stream_target', stream).execute().data

def get_students(stream):
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

def get_student_details(search_term):
    response = supabase.from_('student_stats').select("*").eq('student_id', search_term).execute()
    if not response.data:
        response = supabase.from_('student_stats').select("*").ilike('last_name', f"%{search_term}%").execute()
    return response.data

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

# --- 5. INTERFACE UTILISATEUR PRINCIPALE ---
get_session_state()

# -- Sidebar Moderne --
with st.sidebar:
    st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=100)
    st.markdown("### École Polytechnique de Lomé")
    st.markdown("<div style='font-size: 0.8rem; color: gray; margin-bottom: 20px;'>Gestion de Présence • L2</div>", unsafe_allow_html=True)
    
    app_mode = option_menu(
        "Navigation", 
        ["Espace Étudiant", "Espace Staff"],
        icons=["mortarboard", "shield-lock"],
        menu_icon="list",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#1E3A8A", "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#1E3A8A", "color": "white"},
        }
    )
    
    st.divider()
    if st.session_state['user_role']:
         st.caption(f"👤 Connecté: **{st.session_state['user_role']}**")

# =========================================================
# MODE 1 : ESPACE ÉTUDIANT (PUBLIC)
# =========================================================
# =========================================================
# MODE 1 : ESPACE ÉTUDIANT (PUBLIC) - VERSION MODERNISÉE
# =========================================================
if app_mode == "Espace Étudiant":
    st.markdown("# 🎓 Mon Espace")
    st.markdown("Consultez votre profil et vos statistiques de présence en temps réel.")
    
    # Barre de recherche flottante
    with st.container(border=True):
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1:
            search = st.text_input("Recherche", placeholder="Entrez votre Matricule (ex: LF-LT-001) ou Nom", label_visibility="collapsed")
        with col_s2:
            st.write("") # Spacer alignement

    if search:
        with st.spinner("Chargement du profil..."):
            results = get_student_details(search.strip())
            time.sleep(0.3)
            
            if results:
                for student in results:
                    # Calcul des initiales pour l'avatar
                    initials = f"{student['first_name'][0]}{student['last_name'][0]}".upper()
                    
                    # --- 1. CARTE D'IDENTITÉ AVEC AVATAR ---
                    st.markdown(f"""
                    <style>
                        .profile-card {{
                            background-color: white;
                            border-radius: 16px;
                            padding: 24px;
                            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
                            border: 1px solid #f1f5f9;
                            margin-bottom: 20px;
                            display: flex;
                            align-items: center;
                            gap: 24px;
                        }}
                        .avatar {{
                            width: 80px;
                            height: 80px;
                            background: linear-gradient(135deg, #4f46e5 0%, #818cf8 100%);
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 28px;
                            font-weight: 700;
                            box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3);
                        }}
                        .info-badge {{
                            background-color: #f1f5f9;
                            color: #475569;
                            padding: 4px 12px;
                            border-radius: 9999px;
                            font-size: 0.85rem;
                            font-weight: 600;
                            display: inline-block;
                            margin-right: 8px;
                        }}
                        .stream-badge {{
                            background-color: #eff6ff;
                            color: #1d4ed8;
                        }}
                    </style>
                    
                    <div class="profile-card">
                        <div class="avatar">{initials}</div>
                        <div>
                            <h2 style="margin: 0; color: #1e293b; font-size: 1.8rem; font-family: 'Segoe UI', sans-serif;">
                                {student['first_name']} <span style="font-weight: 800;">{student['last_name']}</span>
                            </h2>
                            <div style="margin-top: 10px;">
                                <span class="info-badge stream-badge">Filière {student['stream']}</span>
                                <span class="info-badge">🆔 {student['student_id']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # --- 2. STATISTIQUES EN COLONNES ---
                    c1, c2, c3 = st.columns([1, 1, 1.2])

                    # Taux de présence
                    with c1:
                        st.markdown("""
                        <div style="background:white; padding:20px; border-radius:12px; border:1px solid #e2e8f0; text-align:center; height:100%;">
                            <div style="color:#64748B; font-size:0.9rem; font-weight:600; text-transform:uppercase; margin-bottom:5px;">Assiduité</div>
                            <div style="font-size:2.5rem; font-weight:800; color:#1E3A8A;">
                                {0}%
                            </div>
                        </div>
                        """.format(student['attendance_percentage']), unsafe_allow_html=True)
                        
                        # Barre de progression native Streamlit en dessous
                        st.write("")
                        val_float = float(student['attendance_percentage']) / 100
                        st.progress(val_float)

                    # Compteur Absences
                    with c2:
                        st.markdown("""
                        <div style="background:white; padding:20px; border-radius:12px; border:1px solid #e2e8f0; text-align:center; height:100%;">
                            <div style="color:#64748B; font-size:0.9rem; font-weight:600; text-transform:uppercase; margin-bottom:5px;">Absences</div>
                            <div style="font-size:2.5rem; font-weight:800; color:#ef4444;">
                                {0}
                            </div>
                            <div style="font-size:0.8rem; color:#94a3b8;">sur {1} cours total</div>
                        </div>
                        """.format(student['absent_count'], student['total_sessions']), unsafe_allow_html=True)

                    # Graphique Donut (Couleurs Modernes)
                    with c3:
                        with st.container(border=True):
                            source = pd.DataFrame({
                                "État": ["Présent", "Absent"],
                                "Valeur": [student['present_count'], student['absent_count']]
                            })
                            
                            # Palette moderne : Emerald (Succès) & Rose (Danger)
                            base = alt.Chart(source).encode(theta=alt.Theta("Valeur", stack=True))
                            pie = base.mark_arc(innerRadius=40, outerRadius=70).encode(
                                color=alt.Color("État", 
                                    scale=alt.Scale(domain=["Présent", "Absent"], range=["#10b981", "#f43f5e"]),
                                    legend=alt.Legend(orient="bottom", title=None)
                                ),
                                tooltip=["État", "Valeur"]
                            )
                            st.altair_chart(pie, use_container_width=True)
            else:
                st.warning("🔍 Aucun étudiant trouvé avec ces informations. Vérifiez le matricule.")

# =========================================================
# MODE 2 : ESPACE STAFF (PRIVÉ & SÉCURISÉ)
# =========================================================
elif app_mode == "Espace Staff":
    
    # A. ÉCRAN DE CONNEXION
    if not st.session_state['user_role']:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h3 style='text-align: center;'>🔐 Accès Réservé</h3>", unsafe_allow_html=True)
                pwd = st.text_input("Mot de passe", type="password", placeholder="Entrez vos identifiants...")
                
                if st.button("Se Connecter", type="primary", use_container_width=True):
                    if login(pwd):
                        st.toast(f"Bienvenue {st.session_state['user_role']} !", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Mot de passe invalide.")
    
    # B. DASHBOARD STAFF
    else:
        # Sous-menu Staff
        with st.sidebar:
            st.markdown("---")
            staff_options = []
            if st.session_state['user_role'] == 'DELEGATE':
                staff_options = ["Faire l'Appel"]
            elif st.session_state['user_role'] == 'PROF':
                staff_options = ["Tableau de Bord Prof", "Alertes Absences", "Explorer les Données"]
            elif st.session_state['user_role'] == 'ADMIN':
                staff_options = ["Correction d'Erreurs", "Faire l'Appel (Force)", "Stats Globales"]
            
            staff_options.append("Déconnexion")
            
            selected_staff = option_menu(
                "Menu Actions", 
                staff_options, 
                icons=['pen', 'bar-chart', 'exclamation-triangle', 'table', 'box-arrow-right'], 
                menu_icon="grid-fill", 
                default_index=0,
                styles={"nav-link": {"font-size": "13px"}}
            )
            
            if selected_staff == "Déconnexion":
                st.session_state['user_role'] = None
                st.session_state['user_scope'] = None
                st.rerun()

        # --- LOGIQUE DÉLÉGUÉ / APPEL ---
        if selected_staff in ["Faire l'Appel", "Faire l'Appel (Force)"]:
            st.title("📝 Nouvelle Feuille de Présence")
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                
                if st.session_state['user_role'] == 'DELEGATE':
                    target_stream = st.session_state['user_scope']
                    c1.success(f"Filière : {target_stream}")
                else:
                    target_stream = c1.selectbox("Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])

                courses = get_courses(target_stream)
                course_map = {c['name']: c['id'] for c in courses}
                chosen_course = c2.selectbox("Matière", list(course_map.keys()) if courses else [])
                chosen_date = c3.date_input("Date", datetime.now())

                if st.button("Charger la liste des étudiants ⬇️", type="primary"):
                    if chosen_course:
                        st.session_state['attendance_context'] = {
                            'students': get_students(target_stream),
                            'course_id': course_map[chosen_course],
                            'course_name': chosen_course
                        }
            
            if 'attendance_context' in st.session_state:
                ctx = st.session_state['attendance_context']
                st.info(f"Appel en cours : **{ctx['course_name']}**")
                
                with st.form("delegate_form"):
                    present_ids = []
                    
                    # Grille responsive pour les checkboxes
                    st.write("Cochez les étudiants présents :")
                    cols = st.columns(3)
                    for i, s in enumerate(ctx['students']):
                        if cols[i%3].checkbox(f"{s['last_name']} {s['first_name']}", value=True, key=s['id']):
                            present_ids.append(s['id'])
                    
                    st.divider()
                    submit = st.form_submit_button("Valider et Enregistrer", type="primary", use_container_width=True)
                    
                    if submit:
                        if save_attendance(ctx['course_id'], chosen_date, present_ids, ctx['students']):
                            st.balloons()
                            st.toast("Feuille de présence enregistrée avec succès !", icon="🎉")
                            del st.session_state['attendance_context']
                            time.sleep(2)
                            st.rerun()

        # --- LOGIQUE ADMIN CORRECTION ---
        elif selected_staff == "Correction d'Erreurs":
            st.title("🛠️ Gestion des Erreurs")
            st.markdown("Modifiez le statut de présence d'une session passée.")
            
            with st.container(border=True):
                col_f, col_s = st.columns(2)
                stream_fix = col_f.selectbox("Choisir la Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
                sessions_data = get_past_sessions(stream_fix)
                
                if sessions_data:
                    sess_options = {f"{s['date_time'][:10]} | {s['courses']['name']}": s['id'] for s in sessions_data}
                    chosen_lbl = col_s.selectbox("Sélectionner la Séance", list(sess_options.keys()))
                    chosen_id = sess_options[chosen_lbl]
                    
                    if st.button("Charger les données de la séance", type="secondary"):
                        all_studs = get_students(stream_fix)
                        recs = supabase.table('attendance').select("*").eq('session_id', chosen_id).execute().data
                        pres_set = {r['student_id'] for r in recs if r['status'] == 'PRESENT'}
                        data_edit = [{"ID": s['id'], "Nom": f"{s['last_name']} {s['first_name']}", "Présent": (s['id'] in pres_set)} for s in all_studs]
                        st.session_state['edit_data'] = pd.DataFrame(data_edit)
                        st.session_state['edit_sess_id'] = chosen_id
                        st.session_state['edit_ref_studs'] = all_studs

            if 'edit_data' in st.session_state:
                st.subheader("Modification")
                edited_df = st.data_editor(
                    st.session_state['edit_data'],
                    column_config={"Présent": st.column_config.CheckboxColumn(default=False)},
                    disabled=["ID", "Nom"],
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
                
                col_btn1, col_btn2 = st.columns([1, 4])
                if col_btn2.button("Sauvegarder les Corrections", type="primary"):
                    upd_map = dict(zip(edited_df['ID'], edited_df['Présent']))
                    if update_attendance_correction(st.session_state['edit_sess_id'], upd_map, st.session_state['edit_ref_studs']):
                        st.toast("Mise à jour effectuée !", icon="💾")
                        time.sleep(1)
                        st.rerun()

        # --- LOGIQUE PROF/STATS ---
        elif selected_staff in ["Tableau de Bord Prof", "Stats Globales"]:
            st.title("📊 Vue d'ensemble")
            df = pd.DataFrame(get_global_stats())
            
            if not df.empty:
                with st.expander("🔎 Filtres", expanded=True):
                    filieres = st.multiselect("Filtrer par Filière", df['stream'].unique(), default=df['stream'].unique())
                
                dff = df[df['stream'].isin(filieres)]
                
                # KPIs Globaux
                st.markdown("### Indicateurs Clés")
                k1, k2, k3 = st.columns(3)
                k1.metric("Moyenne Présence", f"{dff['attendance_percentage'].mean():.1f}%", delta="Global")
                k2.metric("Sessions Totales", dff['total_sessions'].max())
                k3.metric("Étudiants Suivis", len(dff))
                
                # Chart Distribution
                st.markdown("### Distribution des taux de présence")
                chart = alt.Chart(dff).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X("attendance_percentage", bin=alt.Bin(maxbins=20), title="Taux de Présence (%)"),
                    y=alt.Y('count()', title="Nombre d'étudiants"),
                    color=alt.Color('stream', legend=alt.Legend(title="Filière")),
                    tooltip=['stream', 'count()']
                ).properties(height=350)
                
                st.altair_chart(chart, use_container_width=True)

        elif selected_staff == "Alertes Absences":
            st.title("🚨 Zone d'Alerte")
            st.caption("Étudiants ayant un taux de présence inférieur à 50%")
            
            df = pd.DataFrame(get_global_stats())
            if not df.empty:
                red = df[df['attendance_percentage'] < 50]
                if not red.empty:
                    st.dataframe(
                        red[['last_name', 'first_name', 'stream', 'attendance_percentage', 'absent_count']], 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "attendance_percentage": st.column_config.ProgressColumn("Taux", format="%d%%", min_value=0, max_value=100),
                            "absent_count": "Nbre Absences"
                        }
                    )
                else:
                    st.success("✅ Aucun étudiant en situation critique.")

        elif selected_staff == "Explorer les Données":
            st.title("🔎 Explorateur de Données")
            df = pd.DataFrame(get_global_stats())
            st.dataframe(df, use_container_width=True, hide_index=True)

