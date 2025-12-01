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
if app_mode == "Espace Étudiant":
    
    # --- HERO SECTION (Bannière d'accueil) ---
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0; background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(30,58,138,0.05) 100%); border-radius: 20px; margin-bottom: 30px;">
        <h1 style="color: #1E3A8A; font-size: 3.5rem; margin-bottom: 10px;">🎓 Portail Étudiant EPL</h1>
        <p style="font-size: 1.3rem; color: #64748B; max-width: 600px; margin: 0 auto;">
            Accédez à votre dossier académique, surveillez votre assiduité et restez informé de votre situation en temps réel.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- BARRE DE RECHERCHE ---
    c_spacer1, c_main, c_spacer2 = st.columns([1, 2, 1])
    with c_main:
        st.markdown("##### 🔍 Identification")
        search = st.text_input("Rechercher", placeholder="Entrez votre Matricule (ex: LF-LT-001) ou Nom de famille", label_visibility="collapsed")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
        with col_btn2:
            btn_check = st.button("Accéder à mon Profil", type="primary", use_container_width=True)
    
    st.markdown("---")

    # --- RÉSULTATS ---
    if search and btn_check:
        with st.spinner("🔄 Recherche dans la base académique..."):
            results = get_student_details(search.strip())
            time.sleep(0.8) # Petit délai pour l'effet UX
            
            if results:
                student = results[0] # On prend le premier résultat trouvé
                
                st.success(f"Dossier trouvé : {student['first_name']} {student['last_name']}")
                
                # --- BLOC 1 : PROFIL & STATS ---
                c_profile, c_kpi = st.columns([1, 2], gap="large")
                
                with c_profile:
                    # Avatar dynamique basé sur le genre (si dispo dans la base)
                    # Par défaut on check 'gender' ou on met neutre
                    gender = str(student.get('gender', 'M')).upper()
                    if 'F' in gender:
                        avatar_url = "https://img.icons8.com/color/480/student-female--v1.png"
                    else:
                        avatar_url = "https://img.icons8.com/color/480/student-male--v1.png"
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <img src="{avatar_url}" width="120" style="border-radius:50%; margin-bottom:15px; border: 3px solid #1E3A8A;">
                        <h3 style="margin:0; color:#1E3A8A; font-size: 1.5rem;">{student['first_name']}</h3>
                        <h2 style="margin:0; font-weight:800; font-size: 2rem; color:#0f172a;">{student['last_name']}</h2>
                        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                            <p style="color:#64748B; font-size:1rem; margin-bottom: 5px;">Matricule : <strong style="color:#1E3A8A;">{student['student_id']}</strong></p>
                            <p style="color:#64748B; font-size:1rem;">Filière : <span style="background-color:#eff6ff; color:#1E3A8A; padding: 4px 12px; border-radius: 15px; font-weight:bold;">{student['stream']}</span></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with c_kpi:
                    st.markdown("#### 📈 Indicateurs de Performance")
                    
                    # Grands Indicateurs (Metrics)
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Taux de Présence", f"{student['attendance_percentage']}%")
                    k2.metric("Sessions Suivies", f"{student['present_count']} / {student['total_sessions']}")
                    k3.metric("Absences", student['absent_count'], delta_color="inverse")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Barre de progression visuelle HTML/CSS
                    pct = float(student['attendance_percentage'])
                    
                    # Logique de couleur
                    if pct >= 75:
                        bar_color = "#22c55e" # Vert
                        msg_class = "success"
                        msg_text = "✅ **Excellent !** Votre assiduité est exemplaire."
                    elif pct >= 50:
                        bar_color = "#f59e0b" # Orange
                        msg_class = "warning"
                        msg_text = "⚠️ **Attention.** Votre taux est moyen. Restez vigilant."
                    else:
                        bar_color = "#ef4444" # Rouge
                        msg_class = "error"
                        msg_text = "🚨 **Critique.** Vous êtes en dessous du seuil autorisé. Contactez l'administration."

                    st.markdown(f"""
                    <p style="margin-bottom:8px; font-weight:600; color:#475569;">Jauge d'Assiduité :</p>
                    <div style="background-color: #f1f5f9; border-radius: 10px; height: 24px; width: 100%; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="background-color: {bar_color}; height: 100%; width: {pct}%; transition: width 1s ease-in-out;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if msg_class == "success": st.success(msg_text)
                    elif msg_class == "warning": st.warning(msg_text)
                    else: st.error(msg_text)

                # --- BLOC 2 : GRAPHIQUE & INFO ---
                st.markdown("### 📊 Analyse Graphique")
                g1, g2 = st.columns([1, 1])
                
                with g1:
                    # Donut Chart via Altair
                    source = pd.DataFrame({
                        "Statut": ["Présent", "Absent"],
                        "Valeur": [student['present_count'], student['absent_count']]
                    })
                    
                    base = alt.Chart(source).encode(theta=alt.Theta("Valeur", stack=True))
                    pie = base.mark_arc(outerRadius=100, innerRadius=60).encode(
                        color=alt.Color("Statut", scale=alt.Scale(domain=["Présent", "Absent"], range=["#22c55e", "#ef4444"])),
                        tooltip=["Statut", "Valeur"],
                        order=alt.Order("Statut", sort="descending")
                    )
                    text = base.mark_text(radius=120).encode(
                        text="Valeur",
                        order=alt.Order("Statut", sort="descending"),
                        color=alt.value("black")  
                    )
                    st.altair_chart(pie + text, use_container_width=True)
                    
                with g2:
                    st.info("""
                    💡 **Le saviez-vous ?**
                    
                    L'assiduité est le premier facteur de réussite à l'EPL.
                    * **> 75%** : Zone de réussite optimale.
                    * **< 50%** : Risque élevé d'échec ou d'exclusion aux examens.
                    
                    Si vous constatez une erreur dans vos relevés, veuillez vous rapprocher de votre délégué de filière sous 48h.
                    """)
                    
            else:
                st.error("❌ Étudiant introuvable.")
                st.markdown("""
                * Vérifiez l'orthographe de votre nom.
                * Vérifiez le format de votre matricule (ex: LF-GC-003).
                * Si le problème persiste, contactez l'administration.
                """)

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
