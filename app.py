import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(
    page_title="EPL - Master Panel", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS MODERNE ---
st.markdown("""
<style>
    /* Variables de couleurs */
    :root {
        --dark-primary: #0f172a;
        --dark-secondary: #1e293b;
        --dark-accent: #334155;
        --primary-blue: #3b82f6;
        --blue-light: #60a5fa;
        --green-accent: #10b981;
        --red-accent: #ef4444;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
    }
    
    /* Fond principal */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: var(--text-primary);
    }
    
    /* LOGO STYLES */
    .logo-frame {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 20px;
        border-radius: 20px;
        border: 2px solid #475569;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .logo-frame::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #10b981);
    }
    
    .logo-frame:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
        border-color: #3b82f6;
    }
    
    .logo-frame-small {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #475569;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .logo-frame-login {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 25px;
        border-radius: 20px;
        border: 2px solid #475569;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 2rem auto;
        max-width: 150px;
    }
    
    .logo-corner {
        position: absolute;
        width: 15px;
        height: 15px;
        border: 2px solid #3b82f6;
    }
    
    .logo-corner-tl {
        top: 5px;
        left: 5px;
        border-right: none;
        border-bottom: none;
    }
    
    .logo-corner-tr {
        top: 5px;
        right: 5px;
        border-left: none;
        border-bottom: none;
    }
    
    .logo-corner-bl {
        bottom: 5px;
        left: 5px;
        border-right: none;
        border-top: none;
    }
    
    .logo-corner-br {
        bottom: 5px;
        right: 5px;
        border-left: none;
        border-top: none;
    }
    
    /* En-tête principal */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 3rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        border: 1px solid #475569;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #10b981);
    }
    
    /* Cartes */
    .home-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        margin: 1rem 0;
        transition: all 0.3s ease;
        border: 1px solid #334155;
    }
    
    .home-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.3);
        border-color: #3b82f6;
    }
    
    .metric-card { 
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 25px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: center; 
        border-left: 5px solid var(--primary-blue);
        border: 1px solid #334155;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Profil étudiant */
    .student-profile {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid #475569;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        position: relative;
        overflow: hidden;
    }
    
    .student-profile::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
    }
    
    /* Statistiques */
    .highlight-stat {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-family: 'Arial Black', sans-serif;
    }
    
    /* Barre de recherche */
    .search-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        margin-bottom: 2rem;
        border: 1px solid #475569;
        position: relative;
    }
    
    .search-box::before {
        content: '🔍';
        position: absolute;
        top: -15px;
        left: 30px;
        font-size: 2rem;
        background: var(--dark-primary);
        padding: 0 10px;
    }
    
    /* Boutons */
    .stButton>button { 
        border-radius: 12px; 
        font-weight: bold; 
        padding: 0.8rem 2rem;
        border: none;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
    }
    
    /* Inputs */
    .stTextInput>div>div>input {
        background: #0f172a !important;
        color: var(--text-primary) !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    /* Titres */
    h1, h2, h3, h4 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }
    
    h1 {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem !important;
    }
    
    h2 {
        color: var(--text-primary) !important;
        font-size: 2.2rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Texte */
    p, li, .stMarkdown {
        color: var(--text-secondary) !important;
    }
    
    /* Progress bar */
    progress {
        width: 100%;
        height: 12px;
        border-radius: 6px;
        background: #334155;
        overflow: hidden;
    }
    
    progress::-webkit-progress-bar {
        background: #334155;
        border-radius: 6px;
    }
    
    progress::-webkit-progress-value {
        background: linear-gradient(90deg, #3b82f6, #10b981);
        border-radius: 6px;
    }
    
    /* Tableaux */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #475569;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-12oz5g7 {
        background: var(--dark-primary) !important;
    }
    
    .sidebar-content {
        padding: 1.5rem;
        background: var(--dark-secondary);
        border-radius: 15px;
        border: 1px solid #334155;
    }
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #1e293b;
        padding: 5px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 10px 20px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #3b82f6, #60a5fa) !important;
    }
    
    /* Badges */
    .stream-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        background: linear-gradient(90deg, #3b82f6, #10b981);
        color: white;
    }
    
    /* Animation subtile */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Éléments spécifiques */
    .logo-container {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        display: inline-block;
        backdrop-filter: blur(10px);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--dark-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #3b82f6, #10b981);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #60a5fa, #34d399);
    }
    
    /* Badge Licence */
    .licence-badge {
        background: linear-gradient(90deg, #8B5CF6, #3B82F6);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
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
    st.error("🚨 Clés Supabase manquantes ! Ajoutez-les dans .streamlit/secrets.toml")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 4. FONCTIONS MÉTIER (BACKEND) ---

def get_session_state():
    if 'user_role' not in st.session_state: 
        st.session_state['user_role'] = None
    if 'user_scope' not in st.session_state: 
        st.session_state['user_scope'] = None

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

# --- FONCTIONS POUR PAGE PUBLIQUE ---

@st.cache_data(ttl=600)
def search_student(identifier):
    """
    Recherche un étudiant par:
    - Matricule exact
    - Nom/prénom (recherche partielle insensible à la casse)
    """
    try:
        # Vérifier si c'est un matricule (supposé numérique)
        if identifier.isdigit():
            # Recherche par matricule exact
            result = supabase.table('students')\
                .select("*")\
                .eq('id', identifier)\
                .execute()
        else:
            # Recherche par nom/prénom (insensible à la casse)
            result = supabase.table('students')\
                .select("*")\
                .or_(f"last_name.ilike.%{identifier}%,first_name.ilike.%{identifier}%")\
                .limit(10)\
                .execute()
        
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Erreur lors de la recherche: {e}")
        return []

@st.cache_data(ttl=300)
def get_student_stats(student_id):
    """
    Récupère les statistiques d'un étudiant spécifique
    """
    try:
        # Requête pour obtenir les stats de présence
        stats = supabase.table('attendance')\
            .select("status, sessions(date_time, courses(name, stream_target))")\
            .eq('student_id', student_id)\
            .execute()
        
        return process_student_stats(stats.data) if stats.data else None
    except Exception as e:
        st.error(f"Erreur lors du chargement des stats: {e}")
        return None

def process_student_stats(attendance_data):
    """
    Traite les données brutes pour calculer les statistiques
    """
    if not attendance_data:
        return None
    
    # Initialisation des compteurs
    total_sessions = len(attendance_data)
    present_count = sum(1 for item in attendance_data if item['status'] == 'PRESENT')
    absent_count = total_sessions - present_count
    
    # Calcul du pourcentage
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Groupement par matière
    courses_stats = {}
    for item in attendance_data:
        course = item.get('sessions', {}).get('courses', {})
        if course:
            course_name = course.get('name', 'Inconnu')
            if course_name not in courses_stats:
                courses_stats[course_name] = {'present': 0, 'total': 0}
            
            courses_stats[course_name]['total'] += 1
            if item['status'] == 'PRESENT':
                courses_stats[course_name]['present'] += 1
    
    # Préparation des données retour
    return {
        'total_sessions': total_sessions,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': round(attendance_percentage, 1),
        'courses_stats': courses_stats,
        'last_updated': datetime.now().strftime("%d/%m/%Y %H:%M")
    }

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
    if not courses: 
        return []
    course_ids = [c['id'] for c in courses]
    
    # 2. Récupérer les sessions liées (avec le nom du cours via la relation)
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

# --- PAGE D'ACCUEIL PUBLIQUE (si non connecté) ---
if not st.session_state['user_role']:
    # Option pour la page publique ou login
    if 'show_login' not in st.session_state:
        st.session_state['show_login'] = False
    
    if not st.session_state['show_login']:
        # ============ PAGE D'ACCUEIL PUBLIQUE ============
        
        # En-tête principal avec logo encadré
        col1, col2 = st.columns([1, 3])
        with col1:
            # URL de l'image (EPL Logo ou similaire)
            img_url = "https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3"
            st.markdown(f"""
            <div class='logo-frame'>
                <div class='logo-corner logo-corner-tl'></div>
                <div class='logo-corner logo-corner-tr'></div>
                <div class='logo-corner logo-corner-bl'></div>
                <div class='logo-corner logo-corner-br'></div>
                <img src="{img_url}" class="logo-img">
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class='main-header animate-fade-in'>
                <h1 style='color: white; margin: 0;'>📊 Portail de Suivi Académique EPL</h1>
                <p style='color: rgba(255,255,255,0.9); font-size: 1.2rem; margin-top: 0.5rem;'>
                    Université de Lomé - École Polytechnique
                </p>
                <div style='margin-top: 1rem;'>
                    <span class='licence-badge'>Programme Licence</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Section de recherche
        st.markdown("""
        <div class='search-box animate-fade-in'>
            <h2 style='color: #f1f5f9;'>🔍 Consultez vos statistiques de présence</h2>
            <p style='color: #cbd5e1;'>Recherchez votre profil en entrant votre ID (matricule), nom ou prénom</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Barre de recherche
        search_col1, search_col2 = st.columns([4, 1])
        with search_col1:
            search_query = st.text_input(
                "Recherche",
                placeholder="Ex: 12345 ou 'Koffi' ou 'Ama'...",
                label_visibility="collapsed"
            )
        with search_col2:
            search_button = st.button("Rechercher", use_container_width=True, type="primary")
        
        # Résultats de recherche
        if search_query and search_button:
            with st.spinner("Recherche en cours..."):
                results = search_student(search_query)
                
                if results:
                    if len(results) == 1:
                        # Affichage direct du profil unique
                        student = results[0]
                        st.session_state['selected_student'] = student
                    else:
                        # Sélection parmi plusieurs résultats
                        st.markdown(f"**{len(results)} résultats trouvés**")
                        
                        options = [f"{s['last_name']} {s['first_name']} - ID: {s['id']} ({s['stream']}) - Licence" 
                                  for s in results]
                        
                        selected_option = st.selectbox(
                            "Sélectionnez votre profil:",
                            options,
                            index=0
                        )
                        
                        if st.button("Voir les statistiques", type="primary"):
                            selected_index = options.index(selected_option)
                            student = results[selected_index]
                            st.session_state['selected_student'] = student
        
        # Affichage du profil étudiant
        if 'selected_student' in st.session_state:
            student = st.session_state['selected_student']
            
            st.markdown("---")
            st.markdown(f"""
            <div class='student-profile animate-fade-in'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem;'>
                    <div>
                        <h2 style='margin: 0 0 0.5rem 0;'>👤 Profil Étudiant</h2>
                        <p style='color: #cbd5e1; margin: 0;'>Informations académiques</p>
                    </div>
                    <span class='licence-badge'>Licence</span>
                </div>
                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0;'>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Nom Complet</h4>
                        <p style='font-size: 1.3rem; font-weight: bold; margin: 0; color: #f1f5f9;'>
                            {student['last_name']} {student['first_name']}
                        </p>
                    </div>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Matricule (ID)</h4>
                        <p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #3B82F6;'>
                            {student['id']}
                        </p>
                        <small style='color: #64748b;'>Identifiant unique</small>
                    </div>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Filière</h4>
                        <p style='font-size: 1.3rem; font-weight: bold; margin: 0; color: #10B981;'>
                            {student['stream']}
                        </p>
                    </div>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Niveau</h4>
                        <p style='font-size: 1.3rem; font-weight: bold; margin: 0; color: #8B5CF6;'>
                            Licence
                        </p>
                        <small style='color: #64748b;'>Cycle académique</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Chargement des statistiques
            with st.spinner("Chargement de vos statistiques..."):
                stats = get_student_stats(student['id'])
                
                if stats:
                    # Section statistiques principales
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class='metric-card animate-fade-in'>
                            <h4 style='color: #cbd5e1;'>Taux de Présence</h4>
                            <div class='highlight-stat'>{stats['attendance_percentage']}%</div>
                            <progress value="{stats['attendance_percentage']}" max="100" style="width: 100%; height: 12px;"></progress>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class='metric-card animate-fade-in'>
                            <h4 style='color: #cbd5e1;'>Séances totales</h4>
                            <div class='highlight-stat'>{stats['total_sessions']}</div>
                            <p style='color: #94a3b8;'>Sessions enregistrées</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class='metric-card animate-fade-in'>
                            <h4 style='color: #cbd5e1;'>Présences</h4>
                            <div class='highlight-stat' style='background: linear-gradient(90deg, #10B981, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{stats['present_count']}</div>
                            <p style='color: #94a3b8;'>Séances suivies</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class='metric-card animate-fade-in'>
                            <h4 style='color: #cbd5e1;'>Absences</h4>
                            <div class='highlight-stat' style='background: linear-gradient(90deg, #EF4444, #F87171); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{stats['absent_count']}</div>
                            <p style='color: #94a3b8;'>Séances manquées</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Statistiques par matière
                    if stats['courses_stats']:
                        st.markdown("### 📚 Détail par matière")
                        
                        courses_df = []
                        for course_name, course_stats in stats['courses_stats'].items():
                            course_percentage = (course_stats['present'] / course_stats['total'] * 100) if course_stats['total'] > 0 else 0
                            courses_df.append({
                                'Matière': course_name,
                                'Séances': course_stats['total'],
                                'Présences': course_stats['present'],
                                'Taux': f"{round(course_percentage, 1)}%"
                            })
                        
                        courses_data = pd.DataFrame(courses_df)
                        
                        # Affichage sous forme de graphique et tableau
                        tab1, tab2 = st.tabs(["📈 Visualisation", "📋 Détails"])
                        
                        with tab1:
                            # Graphique des taux par matière
                            chart_data = pd.DataFrame(courses_df)
                            chart_data['Taux_num'] = chart_data['Taux'].str.replace('%', '').astype(float)
                            
                            chart = alt.Chart(chart_data).mark_bar().encode(
                                x=alt.X('Matière', sort='-y', axis=alt.Axis(labelColor='#f1f5f9', titleColor='#f1f5f9')),
                                y=alt.Y('Taux_num', title='Taux de présence (%)', axis=alt.Axis(labelColor='#f1f5f9', titleColor='#f1f5f9')),
                                color=alt.Color('Taux_num', scale=alt.Scale(scheme='blues')),
                                tooltip=['Matière', 'Taux', 'Séances', 'Présences']
                            ).properties(
                                height=300,
                                background='transparent'
                            ).configure(
                                background='transparent'
                            )
                            
                            st.altair_chart(chart, use_container_width=True)
                        
                        with tab2:
                            st.dataframe(
                                courses_data,
                                column_config={
                                    "Taux": st.column_config.ProgressColumn(
                                        "Taux",
                                        format="%s",
                                        min_value=0,
                                        max_value=100
                                    )
                                },
                                use_container_width=True,
                                hide_index=True
                            )
                    
                    # Dernière mise à jour
                    st.caption(f"🔄 Dernière mise à jour: {stats['last_updated']}")
                    
                    # Bouton pour nouvelle recherche
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    with col_btn2:
                        if st.button("🔁 Nouvelle recherche", type="secondary", use_container_width=True):
                            del st.session_state['selected_student']
                            st.rerun()
                    
                else:
                    st.info("📊 Aucune statistique disponible pour cet étudiant pour le moment.")
        
        # Section informative
        st.markdown("---")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown("""
            <div class='home-card animate-fade-in'>
                <h3>🎯 Objectif du Portail</h3>
                <p>Suivez votre assiduité et progressez dans votre parcours académique en Licence en toute transparence.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info2:
            st.markdown("""
            <div class='home-card animate-fade-in'>
                <h3>📈 Avantages</h3>
                <ul style='padding-left: 20px;'>
                    <li>Statistiques en temps réel</li>
                    <li>Détail par matière</li>
                    <li>Accès 24h/24</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info3:
            st.markdown("""
            <div class='home-card animate-fade-in'>
                <h3>🔐 Accès Staff</h3>
                <p>Les enseignants et délégués peuvent accéder au panel d'administration.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Bouton accès administration avec logo encadré
        st.markdown("---")
        col_admin1, col_admin2, col_admin3 = st.columns([2, 1, 2])
        with col_admin2:
            st.markdown("""
            <div class='logo-frame-small' style='margin-bottom: 1rem;'>
            """, unsafe_allow_html=True)
            st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=60)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("🔑 Accès Administration", use_container_width=True, type="secondary"):
                st.session_state['show_login'] = True
                st.rerun()
    
    else:
        # ============ FORMULAIRE DE LOGIN ============
        st.markdown("<div style='height: 50px'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Logo encadré pour la page de login
            st.markdown("""
            <div class='logo-frame-login animate-fade-in'>
                <div class='logo-corner logo-corner-tl'></div>
                <div class='logo-corner logo-corner-tr'></div>
                <div class='logo-corner logo-corner-bl'></div>
                <div class='logo-corner logo-corner-br'></div>
            """, unsafe_allow_html=True)
            st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=80)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>Connexion Administration</h2>", unsafe_allow_html=True)
            
            login_card = st.container()
            with login_card:
                st.markdown("""
                <div style='
                    background: linear-gradient(145deg, #1e293b, #0f172a);
                    padding: 2.5rem;
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    border: 1px solid #475569;
                '>
                """, unsafe_allow_html=True)
                
                pwd = st.text_input("Mot de passe d'accès", type="password")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("Se connecter", use_container_width=True, type="primary"):
                        if login(pwd):
                            st.success("Connexion réussie !")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Accès refusé. Vérifiez vos identifiants.")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("← Retour à l'accueil public", type="secondary", use_container_width=True):
                st.session_state['show_login'] = False
                if 'selected_student' in st.session_state:
                    del st.session_state['selected_student']
                st.rerun()
    
    st.stop()

# =========================================================
# INTERFACE CONNECTÉE (RESTE DU CODE EXISTANT)
# =========================================================

with st.sidebar:
    st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
    
    # Logo encadré dans la sidebar
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1.5rem;'>
        <div class='logo-frame-small'>
            <div class='logo-corner logo-corner-tl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-tr' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-bl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-br' style='width: 10px; height: 10px;'></div>
    """, unsafe_allow_html=True)
    st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=70)
    st.markdown("</div></div>", unsafe_allow_html=True)
    
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
        st.session_state['show_login'] = False
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- PAGE: FAIRE L'APPEL ---
if selected == "Faire l'Appel" or (selected == "Faire l'Appel (Force)" and st.session_state['user_role'] == 'ADMIN'):
    # En-tête avec logo encadré
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.markdown("""
        <div class='logo-frame-small'>
            <div class='logo-corner logo-corner-tl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-tr' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-bl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-br' style='width: 10px; height: 10px;'></div>
        """, unsafe_allow_html=True)
        st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=60)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_title:
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
    # En-tête avec logo encadré
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.markdown("""
        <div class='logo-frame-small'>
            <div class='logo-corner logo-corner-tl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-tr' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-bl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-br' style='width: 10px; height: 10px;'></div>
        """, unsafe_allow_html=True)
        st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=60)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_title:
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
    
    # En-tête avec logo encadré
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.markdown("""
        <div class='logo-frame-small'>
            <div class='logo-corner logo-corner-tl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-tr' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-bl' style='width: 10px; height: 10px;'></div>
            <div class='logo-corner logo-corner-br' style='width: 10px; height: 10px;'></div>
        """, unsafe_allow_html=True)
        st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=60)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_title:
        if selected == "Tableau de Bord Prof":
            st.title("📊 Tableau de Bord Académique")
        elif selected == "Stats Globales":
            st.title("📈 Statistiques Globales")
        elif selected == "Alertes Absences":
            st.title("🚨 Alertes Absences")
        elif selected == "Explorer les Données":
            st.title("🔎 Explorateur de Données")
    
    # Chargement unique des données
    df = pd.DataFrame(get_global_stats())
    
    if df.empty:
        st.warning("Pas de données statistiques disponibles (Vue SQL vide ou inexistante).")
    else:
        # --- SOUS-PAGE : DASHBOARD ---
        if selected in ["Tableau de Bord Prof", "Stats Globales"]:
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


