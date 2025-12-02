import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# ==============================================================================
# 1. CONFIGURATION INITIALE & STYLE
# ==============================================================================
st.set_page_config(
    page_title="EPL - Gestion de Présence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personnalisé pour une interface professionnelle
st.markdown("""
<style>
    /* Style global */
    .main { background-color: #fcfcfc; }
    
    /* Carte Métrique (Dashboard) */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Hero Section (Page Publique) */
    .hero-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: white;
        padding: 60px 20px;
        border-radius: 0 0 20px 20px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);
    }
    .hero-title { font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; color: white; }
    .hero-subtitle { font-size: 1.2rem; opacity: 0.9; color: #e0e7ff; }
    
    /* Boutons et Inputs */
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .stTextInput>div>div>input { border-radius: 8px; }
    
    /* Indicateurs de statut */
    .status-good { color: #16a34a; font-weight: bold; }
    .status-warning { color: #ca8a04; font-weight: bold; }
    .status-critical { color: #dc2626; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. GESTION DE LA CONNEXION & SÉCURITÉ
# ==============================================================================

# Identifiants (En production, utilisez st.secrets)
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

# Initialisation Supabase
try:
    # Récupération sécurisée ou fallback pour éviter le crash immédiat si secrets absents
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    if not SUPABASE_URL:
        st.error("⚠️ Configuration Supabase manquante dans .streamlit/secrets.toml")
        st.stop()
except FileNotFoundError:
    st.error("⚠️ Fichier secrets.toml introuvable.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# Gestion de l'état de session (Session State)
if 'user_role' not in st.session_state: st.session_state['user_role'] = None
if 'user_scope' not in st.session_state: st.session_state['user_scope'] = None

# ==============================================================================
# 3. FONCTIONS MÉTIER (BACKEND)
# ==============================================================================

def login_user(password):
    """Vérifie le mot de passe et assigne le rôle."""
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
    """Récupère les cours pour une filière donnée."""
    response = supabase.table('courses').select("*").eq('stream_target', stream).execute()
    return response.data

def get_students(stream):
    """Récupère la liste des étudiants d'une filière."""
    response = supabase.table('students').select("*").eq('stream', stream).order('last_name').execute()
    return response.data

def search_student_public(name_query):
    """Recherche publique par nom (insensible à la casse)."""
    if not name_query or len(name_query) < 2:
        return []
    try:
        # Utilisation de ILIKE pour la recherche flexible
        response = supabase.table('students').select("*").ilike('last_name', f"%{name_query}%").execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur de recherche: {e}")
        return []

def get_student_stats_details(student_id):
    """Récupère les stats détaillées d'un étudiant via la Vue SQL."""
    try:
        # On suppose que la vue 'student_stats' existe
        response = supabase.from_('student_stats').select("*").eq('student_id', student_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception:
        return None

def save_attendance_session(course_id, date_obj, present_student_ids, all_students_list):
    """Enregistre une session et les présences associées."""
    try:
        # 1. Création de la session
        session_data = {
            "course_id": course_id,
            "date_time": date_obj.isoformat()
        }
        sess_res = supabase.table('sessions').insert(session_data).execute()
        
        if not sess_res.data:
            return False
            
        new_session_id = sess_res.data[0]['id']
        
        # 2. Préparation des enregistrements de présence
        attendance_records = []
        for student in all_students_list:
            status = "PRESENT" if student['id'] in present_student_ids else "ABSENT"
            attendance_records.append({
                "session_id": new_session_id,
                "student_id": student['id'],
                "status": status
            })
            
        # 3. Insertion en masse
        supabase.table('attendance').insert(attendance_records).execute()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
        return False

def get_all_stats_global():
    """Récupère les stats globales pour l'Admin/Prof."""
    return supabase.from_('student_stats').select("*").execute().data

# ==============================================================================
# 4. INTERFACE : LOGIQUE DE NAVIGATION
# ==============================================================================

# BARRE LATÉRALE : Contient le Login OU le Menu Principal
with st.sidebar:
    st.image("https://univ-lome.tg/sites/default/files/logo-ul.png", width=100)
    
    if st.session_state['user_role'] is None:
        # --- ZONE LOGIN (Si pas connecté) ---
        st.header("🔒 Accès Restreint")
        st.markdown("Espace réservé aux délégués, professeurs et administrateurs.")
        
        with st.form("login_form"):
            password_input = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se Connecter", use_container_width=True)
            
            if submitted:
                if login_user(password_input):
                    st.success("Connexion réussie !")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Accès refusé.")
        
        st.markdown("---")
        st.info("💡 Étudiants : Utilisez la recherche sur la page principale.")
        
    else:
        # --- MENU NAVIGATION (Si connecté) ---
        st.write(f"Bonjour, **{st.session_state['user_role']}**")
        if st.session_state['user_scope'] != 'ALL':
            st.caption(f"Filière : {st.session_state['user_scope']}")
            
        menu_options = []
        if st.session_state['user_role'] == 'DELEGATE':
            menu_options = ["Faire l'Appel", "Mes Étudiants"]
        elif st.session_state['user_role'] == 'PROF':
            menu_options = ["Vue d'ensemble", "Alertes Absences", "Données Brutes"]
        elif st.session_state['user_role'] == 'ADMIN':
            menu_options = ["Admin Panel", "Faire l'Appel (Admin)", "Correction Données"]
            
        menu_options.append("Déconnexion")
        
        selected_menu = option_menu(
            "Navigation", 
            menu_options, 
            icons=['pencil-square', 'people', 'bar-chart', 'shield-lock', 'box-arrow-right'], 
            menu_icon="cast", 
            default_index=0,
            styles={
                "nav-link-selected": {"background-color": "#1E3A8A"},
            }
        )
        
        if selected_menu == "Déconnexion":
            st.session_state['user_role'] = None
            st.session_state['user_scope'] = None
            st.rerun()

# ==============================================================================
# 5. PAGE PUBLIQUE (ETUDIANTS) - S'affiche si non connecté
# ==============================================================================

if st.session_state['user_role'] is None:
    # Header Hero
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">🎓 Portail Étudiant EPL</div>
            <div class="hero-subtitle">Licence Fondamentale Deuxième Année</div>
            <p style="margin-top:20px;">Vérifiez votre statut de présence en temps réel.</p>
        </div>
    """, unsafe_allow_html=True)

    # Zone de recherche
    col_spacer_l, col_main, col_spacer_r = st.columns([1, 2, 1])
    
    with col_main:
        st.markdown("#### 🔍 Rechercher mon dossier")
        search_term = st.text_input("Entrez votre Nom de famille", placeholder="Ex: KOMBATE")
        
        if search_term:
            with st.spinner("Recherche dans la base académique..."):
                results = search_student_public(search_term)
            
            if not results:
                st.warning("Aucun étudiant trouvé. Vérifiez l'orthographe.")
            else:
                st.success(f"{len(results)} dossier(s) trouvé(s).")
                
                for student in results:
                    # Conteneur pour chaque étudiant trouvé
                    with st.expander(f"👤 {student['last_name']} {student['first_name']} ({student['stream']})", expanded=True):
                        stats = get_student_stats_details(student['id'])
                        
                        if stats:
                            # Métriques
                            c1, c2, c3 = st.columns(3)
                            
                            # Logique de couleur
                            taux = stats['attendance_percentage']
                            color_status = "status-good" if taux >= 75 else ("status-warning" if taux >= 50 else "status-critical")
                            
                            c1.metric("Taux de Présence", f"{taux}%")
                            c2.metric("Sessions Totales", stats['total_sessions'])
                            c3.metric("Absences", stats['absent_count'], delta_color="inverse")
                            
                            st.write("### État du dossier")
                            st.progress(taux / 100)
                            
                            if taux < 50:
                                st.markdown(f"<span class='{color_status}'>⚠️ SITUATION CRITIQUE : Risque de non-validation.</span>", unsafe_allow_html=True)
                            elif taux < 75:
                                st.markdown(f"<span class='{color_status}'>⚠️ ATTENTION : Soyez plus régulier.</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span class='{color_status}'>✅ RAS : Assiduité satisfaisante.</span>", unsafe_allow_html=True)
                        else:
                            st.info("Aucune donnée de présence enregistrée pour le moment.")

    # Footer
    st.markdown("<br><br><br><div style='text-align:center; color:grey; font-size:0.8em;'>© 2025 École Polytechnique de Lomé - Système de Gestion Académique</div>", unsafe_allow_html=True)

# ==============================================================================
# 6. TABLEAUX DE BORD (CONNECTÉ)
# ==============================================================================

else:
    # --------------------------------------------------------------------------
    # MODULE : FAIRE L'APPEL (Délégué & Admin)
    # --------------------------------------------------------------------------
    if selected_menu == "Faire l'Appel" or selected_menu == "Faire l'Appel (Admin)":
        st.title("📝 Nouvelle Feuille de Présence")
        
        # Sélection de la filière
        if st.session_state['user_role'] == 'DELEGATE':
            target_stream = st.session_state['user_scope']
            st.info(f"Filière active : **{target_stream}**")
        else:
            target_stream = st.selectbox("Sélectionner la filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])

        # Chargement des cours
        courses_data = get_courses(target_stream)
        if not courses_data:
            st.warning("Aucun cours trouvé pour cette filière.")
        else:
            course_map = {c['name']: c['id'] for c in courses_data}
            
            c1, c2 = st.columns(2)
            chosen_course_name = c1.selectbox("Matière du cours", list(course_map.keys()))
            chosen_date = c2.date_input("Date de la séance", datetime.now())
            
            # Initialisation du formulaire
            if st.button("Démarrer l'appel", type="primary"):
                st.session_state['attendance_context'] = {
                    'students': get_students(target_stream),
                    'course_id': course_map[chosen_course_name],
                    'course_name': chosen_course_name,
                    'date': chosen_date
                }
            
            # Affichage de la liste à cocher
            if 'attendance_context' in st.session_state:
                ctx = st.session_state['attendance_context']
                st.divider()
                st.subheader(f"Appel : {ctx['course_name']} ({ctx['date']})")
                
                with st.form("attendance_form"):
                    present_ids = []
                    # Grille responsive pour les checkboxes
                    cols = st.columns(3)
                    
                    for i, student in enumerate(ctx['students']):
                        col = cols[i % 3]
                        # Par défaut, tout le monde est coché (plus rapide de décocher les absents)
                        is_present = col.checkbox(
                            f"{student['last_name']} {student['first_name']}", 
                            value=True, 
                            key=f"chk_{student['id']}"
                        )
                        if is_present:
                            present_ids.append(student['id'])
                    
                    st.markdown("---")
                    col_sub, col_cancel = st.columns([1, 4])
                    if col_sub.form_submit_button("💾 ENREGISTRER", type="primary"):
                        if save_attendance_session(ctx['course_id'], chosen_date, present_ids, ctx['students']):
                            st.balloons()
                            st.success(f"Présences enregistrées avec succès ! ({len(present_ids)} présents)")
                            del st.session_state['attendance_context']
                            time.sleep(2)
                            st.rerun()

    # --------------------------------------------------------------------------
    # MODULE : STATISTIQUES (Prof & Admin)
    # --------------------------------------------------------------------------
    elif selected_menu in ["Vue d'ensemble", "Admin Panel", "Stats Globales"]:
        st.title("📊 Tableau de Bord Analytique")
        
        # Récupération des données
        df = pd.DataFrame(get_all_stats_global())
        
        if df.empty:
            st.info("En attente de données...")
        else:
            # Filtres
            st.markdown("##### Filtres")
            streams_avail = df['stream'].unique()
            selected_streams = st.multiselect("Filtrer par Filière", streams_avail, default=streams_avail)
            
            df_filtered = df[df['stream'].isin(selected_streams)]
            
            # KPIs Globaux
            kpi1, kpi2, kpi3 = st.columns(3)
            avg_att = df_filtered['attendance_percentage'].mean()
            kpi1.metric("Taux de Présence Moyen", f"{avg_att:.1f}%")
            kpi2.metric("Étudiants Suivis", len(df_filtered))
            kpi3.metric("Absences Totales Cumulées", df_filtered['absent_count'].sum())
            
            st.divider()
            
            # Graphiques avec Altair
            c_chart1, c_chart2 = st.columns(2)
            
            with c_chart1:
                st.subheader("Distribution des taux de présence")
                chart_hist = alt.Chart(df_filtered).mark_bar().encode(
                    x=alt.X("attendance_percentage", bin=alt.Bin(maxbins=10), title="Taux de présence (%)"),
                    y=alt.Y('count()', title="Nombre d'étudiants"),
                    color=alt.Color('stream', legend=alt.Legend(title="Filière")),
                    tooltip=['stream', 'count()']
                ).properties(height=300)
                st.altair_chart(chart_hist, use_container_width=True)
                
            with c_chart2:
                st.subheader("Performance par Filière")
                chart_box = alt.Chart(df_filtered).mark_boxplot().encode(
                    x='stream:N',
                    y=alt.Y('attendance_percentage:Q', title="Taux (%)"),
                    color='stream:N'
                ).properties(height=300)
                st.altair_chart(chart_box, use_container_width=True)

    # --------------------------------------------------------------------------
    # MODULE : ALERTES (Prof)
    # --------------------------------------------------------------------------
    elif selected_menu == "Alertes Absences":
        st.title("🚨 Gestion des Risques")
        st.markdown("Étudiants nécessitant une intervention pédagogique immédiate (< 50% de présence).")
        
        df = pd.DataFrame(get_all_stats_global())
        if not df.empty:
            red_list = df[df['attendance_percentage'] < 50].sort_values('attendance_percentage')
            
            if red_list.empty:
                st.success("Aucun étudiant en situation critique. Excellent !")
            else:
                st.dataframe(
                    red_list[['last_name', 'first_name', 'stream', 'attendance_percentage', 'absent_count']],
                    column_config={
                        "attendance_percentage": st.column_config.ProgressColumn(
                            "Taux", format="%d%%", min_value=0, max_value=100
                        )
                    },
                    use_container_width=True,
                    hide_index=True
                )
