import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# ==============================================================================
# 1. CONFIGURATION GÉNÉRALE & DESIGN
# ==============================================================================
st.set_page_config(
    page_title="EPL - Master Panel",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS AVANCÉ & MODERNE ---
# --- CSS PREMIUM & DESIGN SYSTEM ---
st.markdown("""
<style>
    /* 1. TYPOGRAPHIE & COULEURS GLOBALES */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b; 
    }
    
    /* 2. ARRIÈRE-PLAN MODERNE */
    .stApp {
        background-color: #f8fafc; /* Gris très pâle bleuté */
        background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
        background-size: 20px 20px; /* Effet "Papier millimétré" subtil */
    }

    /* 3. HERO SECTION (BANNIÈRE) */
    .hero-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        padding: 4rem 2rem;
        border-radius: 0 0 2rem 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.2);
        margin: -6rem -4rem 2rem -4rem; /* Pour coller aux bords */
    }
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
    }

    /* 4. CARTES & CONTENEURS */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: #bfdbfe;
    }

    /* 5. CHAMPS DE SAISIE STYLISÉS */
    .stTextInput input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 12px 20px;
        font-size: 1rem;
        transition: all 0.3s;
    }
    .stTextInput input:focus {
        border-color: #2563EB;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
    }

    /* 6. BOUTONS PRIMAIRES */
    .stButton>button {
        background: linear-gradient(to right, #1E3A8A, #2563EB);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SÉCURITÉ & CONNEXION BDD
# ==============================================================================

# Gestion des Mots de Passe (RBAC)
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

# Connexion Supabase
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("🚨 ERREUR CRITIQUE : Les clés Supabase sont manquantes dans .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==============================================================================
# 3. FONCTIONS MÉTIER (BACKEND LOGIC)
# ==============================================================================

def get_session_state():
    """Initialise les variables de session utilisateur"""
    if 'user_role' not in st.session_state: st.session_state['user_role'] = None
    if 'user_scope' not in st.session_state: st.session_state['user_scope'] = None

def login(password):
    """Gère l'authentification hiérarchique"""
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

# --- Fonctions de Récupération de Données ---

def get_courses(stream):
    return supabase.table('courses').select("*").eq('stream_target', stream).execute().data

def get_students(stream):
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

def get_student_details(search_term):
    """Recherche intelligente pour le portail étudiant (ID ou Nom)"""
    # 1. Essai par Matricule exact
    response = supabase.from_('student_stats').select("*").eq('student_id', search_term).execute()
    # 2. Essai par Nom de famille (approximatif)
    if not response.data:
        response = supabase.from_('student_stats').select("*").ilike('last_name', f"%{search_term}%").execute()
    return response.data

def get_global_stats():
    """Récupère la vue SQL complète pour les stats profs/admin"""
    return supabase.from_('student_stats').select("*").execute().data

def get_past_sessions(stream):
    """Pour la correction d'erreurs : récupère l'historique"""
    courses = get_courses(stream)
    course_ids = [c['id'] for c in courses]
    if not course_ids: return []
    sessions = supabase.table('sessions').select("*, courses(name)").in_('course_id', course_ids).order('date_time', desc=True).limit(20).execute()
    return sessions.data

# --- Fonctions d'Écriture (Transactions) ---

def save_attendance(course_id, date, present_ids, all_students):
    """Enregistre une nouvelle feuille d'appel"""
    try:
        # 1. Création de la session
        sess = supabase.table('sessions').insert({"course_id": course_id, "date_time": date.isoformat()}).execute()
        sess_id = sess.data[0]['id']
        
        # 2. Préparation des lignes de présence
        records = []
        for s in all_students:
            status = "PRESENT" if s['id'] in present_ids else "ABSENT"
            records.append({"session_id": sess_id, "student_id": s['id'], "status": status})
            
        # 3. Insertion en masse
        supabase.table('attendance').insert(records).execute()
        return True
    except Exception as e:
        st.error(f"Erreur Database: {e}")
        return False

def update_attendance_correction(session_id, updated_presence_map, all_students):
    """Correction Admin : Écrase et remplace les présences d'une session"""
    try:
        # Suppression ancienne liste
        supabase.table('attendance').delete().eq('session_id', session_id).execute()
        
        # Création nouvelle liste
        records = []
        for s in all_students:
            status = "PRESENT" if updated_presence_map.get(s['id'], False) else "ABSENT"
            records.append({"session_id": session_id, "student_id": s['id'], "status": status})
            
        # Insertion
        supabase.table('attendance').insert(records).execute()
        return True
    except Exception as e:
        return False

# ==============================================================================
# 4. INTERFACE UTILISATEUR (FRONTEND)
# ==============================================================================

# Initialisation
get_session_state()

# --- BARRE LATÉRALE (NAVIGATION) ---
with st.sidebar:
    # Logo
    st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=140)
    st.markdown("### EPL - Gestion Présence")
    st.caption("Année Académique 2025-2026")
    
    # Menu Principal de Navigation
    app_mode = option_menu(
        menu_title=None,
        options=["Espace Étudiant", "Espace Staff"],
        icons=["person-circle", "shield-lock-fill"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#1E3A8A"},
        }
    )
    
    st.divider()
    st.markdown("conçu par OB")


# =========================================================
# MODE 1 : ESPACE ÉTUDIANT (PUBLIC & ACCUEIL)
# =========================================================
# =========================================================
# MODE 1 : ESPACE ÉTUDIANT (DESIGN PREMIUM)
# =========================================================
if app_mode == "Espace Étudiant":
    
    # --- 1. HERO BANNER (HTML Pur pour le design) ---
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🎓 Portail Étudiant</div>
        <div class="hero-subtitle">
            Bienvenue sur l'espace numérique de l'EPL. 
            Consultez votre assiduité en temps réel et accédez à votre dossier académique.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- 2. BARRE DE RECHERCHE CENTRÉE ---
    # On utilise des colonnes vides pour centrer la barre au milieu de l'écran
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        # On met le tout dans une carte blanche pour faire ressortir la recherche
        st.markdown('<div style="background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: -50px; position: relative; z-index: 10;">', unsafe_allow_html=True)
        st.markdown("##### 🔎 Identifiez-vous")
        search = st.text_input("Recherche", placeholder="Votre Matricule (ex: LF-LT-001) ou Nom", label_visibility="collapsed")
        
        # Bouton pleine largeur
        st.markdown("<br>", unsafe_allow_html=True)
        btn_check = st.button("Accéder à mon Espace", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. RÉSULTATS DYNAMIQUES ---
    if search and btn_check:
        st.markdown("<br><br>", unsafe_allow_html=True) # Espacement
        
        with st.spinner("Connexion au serveur académique..."):
            results = get_student_details(search.strip())
            time.sleep(0.8) # Délai esthétique
            
            if results:
                student = results[0]
                
                # --- EN-TÊTE DU DOSSIER ---
                # Avatar basé sur le genre
                avatar = "https://img.icons8.com/3d-fluency/375/student-male--v3.png" if "M" in str(student.get('gender', 'M')).upper() else "https://img.icons8.com/3d-fluency/375/student-female--v3.png"
                
                c_header1, c_header2 = st.columns([1, 4])
                with c_header1:
                    st.image(avatar, width=150)
                with c_header2:
                    st.markdown(f"""
                    <h1 style="color:#1e293b; margin-bottom:0;">{student['first_name']} <span style="color:#2563EB;">{student['last_name']}</span></h1>
                    <div style="display:flex; gap: 15px; margin-top: 10px;">
                        <span style="background:#eff6ff; color:#2563EB; padding:5px 15px; border-radius:20px; font-weight:bold; border:1px solid #bfdbfe;">{student['stream']}</span>
                        <span style="background:#f1f5f9; color:#64748B; padding:5px 15px; border-radius:20px; font-weight:bold; border:1px solid #e2e8f0;">Matricule: {student['student_id']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # --- STATISTIQUES (CARTES DESIGN) ---
                col1, col2, col3 = st.columns(3)
                
                # Carte 1 : Taux Global
                with col1:
                    pct = float(student['attendance_percentage'])
                    color_status = "#22c55e" if pct >= 75 else "#f59e0b" if pct >= 50 else "#ef4444"
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="font-size:0.9rem; font-weight:600; color:#64748B; text-transform:uppercase;">Assiduité Globale</p>
                        <h2 style="font-size:3rem; color:{color_status}; margin:10px 0;">{pct}%</h2>
                        <div style="background:#f1f5f9; height:10px; border-radius:5px; overflow:hidden;">
                            <div style="background:{color_status}; width:{pct}%; height:100%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Carte 2 : Compteurs
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="font-size:0.9rem; font-weight:600; color:#64748B; text-transform:uppercase;">Sessions</p>
                        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:15px;">
                            <div>
                                <div style="font-size:2rem; font-weight:800; color:#1e293b;">{student['present_count']}</div>
                                <div style="font-size:0.8rem; color:#22c55e;">Présences</div>
                            </div>
                            <div style="width:1px; height:40px; background:#e2e8f0;"></div>
                            <div>
                                <div style="font-size:2rem; font-weight:800; color:#1e293b;">{student['total_sessions']}</div>
                                <div style="font-size:0.8rem; color:#64748B;">Total</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Carte 3 : Absences
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p style="font-size:0.9rem; font-weight:600; color:#64748B; text-transform:uppercase;">Absences</p>
                        <h2 style="font-size:3rem; color:#ef4444; margin:10px 0;">{student['absent_count']}</h2>
                        <p style="font-size:0.8rem; color:#ef4444;">Justifiées ou non</p>
                    </div>
                    """, unsafe_allow_html=True)

                # --- GRAPHIQUE & INFO ---
                st.markdown("<br>", unsafe_allow_html=True)
                c_graph, c_info = st.columns([1, 1])
                
                with c_graph:
                    st.markdown("#### 📊 Répartition visuelle")
                    source = pd.DataFrame({
                        "Type": ["Présence", "Absence"],
                        "Valeur": [student['present_count'], student['absent_count']]
                    })
                    
                    # Graphique Donut épuré
                    base = alt.Chart(source).encode(theta=alt.Theta("Valeur", stack=True))
                    pie = base.mark_arc(innerRadius=60, outerRadius=100).encode(
                        color=alt.Color("Type", scale=alt.Scale(domain=["Présence", "Absence"], range=["#22c55e", "#ef4444"])),
                        tooltip=["Type", "Valeur"],
                        order=alt.Order("Type", sort="descending")
                    )
                    st.altair_chart(pie, use_container_width=True)
                
                with c_info:
                    st.markdown("#### 💡 Note d'information")
                    st.info("""
                    **Important :** Les statistiques affichées sont mises à jour en temps réel par les délégués de filière.
                    
                    * Un taux **inférieur à 50%** entraîne une convocation automatique.
                    * Pour justifier une absence, veuillez déposer vos justificatifs au secrétariat académique sous 48h.
                    """)

            else:
                st.error("❌ Dossier introuvable.")
                st.caption("Vérifiez la saisie ou contactez l'administration.")

# =========================================================
# MODE 2 : ESPACE STAFF (PRIVÉ & SÉCURISÉ)
# =========================================================
elif app_mode == "Espace Staff":
    
    # A. ÉCRAN DE CONNEXION (Si pas encore connecté)
    if not st.session_state['user_role']:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns([1,1,1])
        with col_c2:
            st.markdown("""
            <div class="metric-card">
                <h3>🔐 Accès Réservé</h3>
                <p>Espace Professeurs, Délégués et Administration</p>
            </div>
            """, unsafe_allow_html=True)
            
            pwd = st.text_input("Mot de passe d'accès", type="password")
            
            if st.button("Se Connecter", type="primary", use_container_width=True):
                with st.spinner("Vérification des accréditations..."):
                    time.sleep(0.5)
                    if login(pwd):
                        st.success(f"Bienvenue ! Accès accordé : {st.session_state['user_role']}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Mot de passe invalide. Accès refusé.")
    
    # B. TABLEAU DE BORD STAFF (Une fois connecté)
    else:
        # -- Menu Contextuel Staff --
        with st.sidebar:
            st.success(f"👤 **{st.session_state['user_role']}** Connecté")
            if st.session_state['user_scope'] != 'ALL':
                st.info(f"Filière : {st.session_state['user_scope']}")
            
            # Définition des options selon le rôle
            staff_options = []
            if st.session_state['user_role'] == 'DELEGATE':
                staff_options = ["Faire l'Appel"]
            elif st.session_state['user_role'] == 'PROF':
                staff_options = ["Tableau de Bord Prof", "Alertes Absences", "Explorer les Données"]
            elif st.session_state['user_role'] == 'ADMIN':
                staff_options = ["Correction d'Erreurs", "Faire l'Appel (Force)", "Stats Globales"]
            
            staff_options.append("Déconnexion")
            
            selected_staff = option_menu("Menu Staff", staff_options, icons=['pencil-square', 'exclamation-triangle', 'table', 'door-open'], menu_icon="gear", default_index=0)
            
            if selected_staff == "Déconnexion":
                st.session_state['user_role'] = None
                st.session_state['user_scope'] = None
                st.rerun()

        # -----------------------------------------------------
        # 1. MODULE DÉLÉGUÉ / APPEL
        # -----------------------------------------------------
        if selected_staff == "Faire l'Appel" or selected_staff == "Faire l'Appel (Force)":
            st.title("📝 Nouvelle Feuille de Présence")
            
            # Contexte Filière
            if st.session_state['user_role'] == 'DELEGATE':
                target_stream = st.session_state['user_scope']
            else:
                target_stream = st.selectbox("Choisir Filière (Admin)", ["LT", "GC", "IABD", "IS", "GE", "GM"])

            # Sélection Cours/Date
            c1, c2 = st.columns(2)
            courses = get_courses(target_stream)
            course_map = {c['name']: c['id'] for c in courses}
            
            with c1:
                chosen_course = st.selectbox("Matière", list(course_map.keys()) if courses else [])
            with c2:
                chosen_date = st.date_input("Date de la séance", datetime.now())

            # Chargement Liste
            if st.button("Charger la liste des étudiants", type="primary"):
                if chosen_course:
                    st.session_state['attendance_context'] = {
                        'students': get_students(target_stream),
                        'course_id': course_map[chosen_course],
                        'course_name': chosen_course
                    }
            
            # Formulaire
            if 'attendance_context' in st.session_state:
                ctx = st.session_state['attendance_context']
                st.divider()
                st.markdown(f"### 📋 Appel : {ctx['course_name']}")
                
                with st.form("delegate_form"):
                    st.write("Cochez les étudiants **PRÉSENTS** :")
                    present_ids = []
                    cols = st.columns(3)
                    for i, s in enumerate(ctx['students']):
                        if cols[i%3].checkbox(f"{s['last_name']} {s['first_name']}", value=True, key=s['id']):
                            present_ids.append(s['id'])
                    
                    st.markdown("---")
                    submit = st.form_submit_button("💾 Valider et Envoyer", type="primary", use_container_width=True)
                    
                    if submit:
                        if save_attendance(ctx['course_id'], chosen_date, present_ids, ctx['students']):
                            st.balloons()
                            st.success(f"✅ Feuille de présence enregistrée ! ({len(present_ids)} présents)")
                            del st.session_state['attendance_context']
                            time.sleep(2)
                            st.rerun()

        # -----------------------------------------------------
        # 2. MODULE ADMIN / CORRECTION
        # -----------------------------------------------------
        elif selected_staff == "Correction d'Erreurs":
            st.title("🛠️ Correction Admin")
            st.info("Ce module permet de modifier rétroactivement une feuille de présence erronée.")
            
            col_f, col_s = st.columns(2)
            stream_fix = col_f.selectbox("Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
            
            sessions_data = get_past_sessions(stream_fix)
            
            if sessions_data:
                # Création labels lisibles
                sess_options = {f"{s['date_time'][:10]} | {s['courses']['name']}": s['id'] for s in sessions_data}
                chosen_lbl = col_s.selectbox("Sélectionner la séance", list(sess_options.keys()))
                chosen_id = sess_options[chosen_lbl]
                
                if st.button("Charger les données"):
                    all_studs = get_students(stream_fix)
                    recs = supabase.table('attendance').select("*").eq('session_id', chosen_id).execute().data
                    pres_set = {r['student_id'] for r in recs if r['status'] == 'PRESENT'}
                    
                    # Préparation Dataframe Éditable
                    data_edit = [{"ID": s['id'], "Nom": f"{s['last_name']} {s['first_name']}", "Présent": (s['id'] in pres_set)} for s in all_studs]
                    st.session_state['edit_data'] = pd.DataFrame(data_edit)
                    st.session_state['edit_sess_id'] = chosen_id
                    st.session_state['edit_ref_studs'] = all_studs

            # Éditeur
            if 'edit_data' in st.session_state:
                st.divider()
                st.markdown("#### Modification en cours...")
                edited_df = st.data_editor(
                    st.session_state['edit_data'],
                    column_config={"Présent": st.column_config.CheckboxColumn(default=False)},
                    disabled=["ID", "Nom"],
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
                
                if st.button("💾 Sauvegarder les Corrections", type="primary"):
                    upd_map = dict(zip(edited_df['ID'], edited_df['Présent']))
                    if update_attendance_correction(st.session_state['edit_sess_id'], upd_map, st.session_state['edit_ref_studs']):
                        st.success("✅ Base de données mise à jour avec succès !")
                        time.sleep(1.5)
                        st.rerun()

        # -----------------------------------------------------
        # 3. MODULE PROF / STATS
        # -----------------------------------------------------
        elif selected_staff == "Tableau de Bord Prof" or selected_staff == "Stats Globales":
            st.title("📊 Statistiques Académiques")
            df = pd.DataFrame(get_global_stats())
            
            if not df.empty:
                # Filtres
                filieres = st.multiselect("Filtrer par Filière", df['stream'].unique(), default=df['stream'].unique())
                dff = df[df['stream'].isin(filieres)]
                
                # KPIs
                c1, c2, c3 = st.columns(3)
                c1.metric("Moyenne Présence", f"{dff['attendance_percentage'].mean():.1f}%")
                c2.metric("Sessions Totales", dff['total_sessions'].max())
                c3.metric("Étudiants Suivis", len(dff))
                
                st.divider()
                
                # Graphique Distribution
                st.markdown("#### Distribution des Taux de Présence")
                chart = alt.Chart(dff).mark_bar().encode(
                    x=alt.X("attendance_percentage", bin=True, title="Taux (%)"),
                    y=alt.Y('count()', title="Nombre d'étudiants"),
                    color='stream',
                    tooltip=['stream', 'count()']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)

        # -----------------------------------------------------
        # 4. MODULE ALERTES
        # -----------------------------------------------------
        elif selected_staff == "Alertes Absences":
            st.title("🚨 Zone de Vigilance")
            st.warning("Étudiants ayant un taux de présence inférieur à 50%.")
            
            df = pd.DataFrame(get_global_stats())
            if not df.empty:
                red = df[df['attendance_percentage'] < 50].sort_values('attendance_percentage')
                if not red.empty:
                    st.dataframe(
                        red[['last_name', 'first_name', 'stream', 'attendance_percentage', 'absent_count']],
                        column_config={
                            "attendance_percentage": st.column_config.ProgressColumn("Taux", format="%d%%", min_value=0, max_value=100),
                            "absent_count": "Absences"
                        },
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.success("Aucun étudiant en situation critique. Bravo !")

        # -----------------------------------------------------
        # 5. MODULE EXPLORATEUR
        # -----------------------------------------------------
        elif selected_staff == "Explorer les Données":
            st.title("🔎 Explorateur de Données")
            df = pd.DataFrame(get_global_stats())
            # Affichage corrigé sans paramètre invalide
            st.dataframe(df, use_container_width=True, hide_index=True)



