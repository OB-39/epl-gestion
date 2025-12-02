import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu
import altair as alt

# =========================================================
# 1. CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="EPL - Portail Académique", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

# =========================================================
# 2. CSS MODERNE RESPONSIVE
# =========================================================
st.markdown("""
<style>
    /* Variables CSS */
    :root {
        --dark-primary: #0f172a;
        --dark-secondary: #1e293b;
        --dark-accent: #334155;
        --primary-blue: #3b82f6;
        --blue-light: #60a5fa;
        --green-accent: #10b981;
        --red-accent: #ef4444;
        --purple-accent: #8b5cf6;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --border-color: #475569;
    }
    
    /* Reset & Base */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: var(--text-primary);
        min-height: 100vh;
    }
    
    /* Container Responsive */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    /* === LOGO RESPONSIVE === */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto;
    }
    
    .logo-frame {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(12px, 2vw, 20px);
        border-radius: 20px;
        border: 2px solid var(--border-color);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        width: fit-content;
        margin: 0 auto;
    }
    
    .logo-frame img {
        width: clamp(70px, 14vw, 130px);
        height: auto;
        object-fit: contain;
    }
    
    .logo-frame-small {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(8px, 1.5vw, 15px);
        border-radius: 15px;
        border: 1px solid var(--border-color);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        margin: 0 auto;
    }
    
    .logo-frame-small img {
        width: clamp(35px, 7vw, 60px);
        height: auto;
    }
    
    .logo-frame-login {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(15px, 3vw, 25px);
        border-radius: 20px;
        border: 2px solid var(--border-color);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 2rem auto;
        max-width: clamp(100px, 22vw, 160px);
    }
    
    .logo-frame-login img {
        width: clamp(50px, 10vw, 80px);
        height: auto;
    }
    
    /* Coins décoratifs */
    .logo-corner {
        position: absolute;
        width: clamp(8px, 1.3vw, 12px);
        height: clamp(8px, 1.3vw, 12px);
        border: 2px solid var(--primary-blue);
    }
    
    .logo-corner-tl { top: 4px; left: 4px; border-right: none; border-bottom: none; }
    .logo-corner-tr { top: 4px; right: 4px; border-left: none; border-bottom: none; }
    .logo-corner-bl { bottom: 4px; left: 4px; border-right: none; border-top: none; }
    .logo-corner-br { bottom: 4px; right: 4px; border-left: none; border-top: none; }
    
    /* === BARRE DE NAVIGATION === */
    .nav-bar {
        background: linear-gradient(90deg, #1e293b, #0f172a);
        padding: 0.8rem 1.5rem;
        border-bottom: 1px solid var(--border-color);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 1000;
        backdrop-filter: blur(10px);
    }
    
    .nav-title {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .nav-logo {
        width: 35px;
        height: 35px;
        border-radius: 8px;
        background: linear-gradient(135deg, var(--primary-blue), var(--purple-accent));
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .nav-actions {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    /* === EN-TÊTE PRINCIPAL === */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: clamp(1.2rem, 3vw, 2.5rem);
        border-radius: 20px;
        color: white;
        margin: 1.5rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        border: 1px solid var(--border-color);
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
        background: linear-gradient(90deg, var(--primary-blue), var(--green-accent));
    }
    
    /* === CARTES RESPONSIVES === */
    .home-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(0.8rem, 1.8vw, 1.3rem);
        border-radius: 15px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        margin: 0.8rem 0;
        transition: all 0.3s ease;
        border: 1px solid var(--dark-accent);
        height: 100%;
    }
    
    .home-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.3);
        border-color: var(--primary-blue);
    }
    
    .metric-card { 
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(0.8rem, 1.8vw, 1.3rem); 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: center; 
        border-left: 4px solid var(--primary-blue);
        border: 1px solid var(--dark-accent);
        transition: transform 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
    }
    
    /* === PROFIL ÉTUDIANT === */
    .student-profile {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(1.2rem, 2.5vw, 2rem);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        position: relative;
        overflow: hidden;
        margin: 1.5rem 0;
    }
    
    .student-profile::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: clamp(50px, 12vw, 80px);
        height: clamp(50px, 12vw, 80px);
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
    }
    
    /* === STATISTIQUES === */
    .highlight-stat {
        font-size: clamp(1.8rem, 5vw, 2.8rem);
        font-weight: bold;
        background: linear-gradient(90deg, var(--primary-blue), var(--blue-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        line-height: 1.2;
        margin: 0.5rem 0;
    }
    
    /* === BARRE DE RECHERCHE === */
    .search-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: clamp(1.2rem, 2.5vw, 2rem);
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        margin: 1.5rem 0;
        border: 1px solid var(--border-color);
        position: relative;
    }
    
    /* === BOUTONS === */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: clamp(0.5rem, 1.2vw, 0.7rem) clamp(1rem, 2.5vw, 1.5rem) !important;
        border: none !important;
        transition: all 0.3s ease !important;
        font-size: clamp(0.85rem, 1.8vw, 0.95rem) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* === INPUTS === */
    .stTextInput > div > div > input {
        background: #0f172a !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: clamp(0.6rem, 1.3vw, 0.75rem) clamp(0.8rem, 1.8vw, 1rem) !important;
        font-size: clamp(0.85rem, 1.8vw, 0.95rem) !important;
    }
    
    /* === TITRES RESPONSIVES === */
    h1 {
        background: linear-gradient(90deg, var(--primary-blue), var(--blue-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: clamp(1.5rem, 4.55vw, 2.7rem) !important;
        line-height: 1.2 !important;
        margin-bottom: 0.8rem !important;
    }
    
    h2 {
        color: var(--text-primary) !important;
        font-size: clamp(1.4rem, 3.8vw, 2rem) !important;
        margin-bottom: 1.2rem !important;
        line-height: 1.3 !important;
    }
    
    h3 {
        font-size: clamp(1.1rem, 3vw, 1.4rem) !important;
        line-height: 1.3 !important;
    }
    
    h4 {
        font-size: clamp(1rem, 2.4vw, 1.15rem) !important;
        line-height: 1.3 !important;
    }
    
    /* === TEXTE === */
    p, li, .stMarkdown {
        color: var(--text-secondary) !important;
        font-size: clamp(1rem, 2.6vw, 2rem) !important;
        line-height: 1.5 !important;
    }
    
    /* === GRID RESPONSIVE === */
    .responsive-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr));
        gap: clamp(0.8rem, 1.8vw, 1.2rem);
        margin: 1.2rem 0;
    }
    
    /* === BADGES === */
    .licence-badge {
        background: linear-gradient(90deg, var(--purple-accent), var(--primary-blue));
        color: white;
        padding: clamp(0.3rem, 0.8vw, 0.4rem) clamp(0.8rem, 1.8vw, 1.2rem);
        border-radius: 25px;
        font-weight: 600;
        font-size: clamp(0.75rem, 1.6vw, 0.85rem);
        display: inline-block;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        white-space: nowrap;
    }
    
    /* === ANIMATIONS === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .animate-pulse {
        animation: pulse 2s infinite;
    }
    
    /* === MEDIA QUERIES MOBILE === */
    @media (max-width: 768px) {
        .nav-bar {
            padding: 0.6rem 1rem;
            flex-direction: column;
            gap: 0.8rem;
        }
        
        .nav-title {
            width: 100%;
            justify-content: center;
        }
        
        .nav-actions {
            width: 100%;
            justify-content: center;
        }
        
        .main-header {
            padding: 1.2rem;
            text-align: center;
        }
        
        .search-box {
            padding: 1.2rem;
        }
        
        .student-profile {
            padding: 1.2rem;
        }
        
        [data-testid="column"] {
            width: 100% !important;
            padding: 0.3rem !important;
        }
        
        .responsive-grid {
            grid-template-columns: 1fr;
            gap: 0.8rem;
        }
        
        .stButton > button {
            padding: 0.8rem !important;
            font-size: 0.95rem !important;
        }
        
        .stTextInput > div > div > input {
            padding: 0.8rem !important;
            font-size: 0.95rem !important;
        }
        
        /* Optimisation pour touch */
        button, input, select, textarea {
            font-size: 16px !important; /* Évite le zoom sur iOS */
        }
    }
    
    @media (max-width: 480px) {
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.1rem !important; }
        
        .highlight-stat {
            font-size: 1.8rem !important;
        }
        
        .licence-badge {
            font-size: 0.75rem !important;
            padding: 0.3rem 0.8rem !important;
        }
    }
    
    /* Optimisation tactile */
    @media (hover: none) and (pointer: coarse) {
        .home-card:hover, .metric-card:hover {
            transform: none;
        }
        
        .stButton > button:active {
            transform: scale(0.98) !important;
        }
        
        /* Augmenter la zone cliquable */
        button, [role="button"] {
            min-height: 44px;
            min-width: 44px;
        }
    }
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--dark-secondary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--primary-blue), var(--green-accent));
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--blue-light), #34d399);
    }
    
    /* Optimisation des images */
    img {
        max-width: 100%;
        height: auto;
        display: block;
    }
    
    /* Loading states */
    .loading-shimmer {
        background: linear-gradient(90deg, 
            rgba(255,255,255,0.05) 25%, 
            rgba(255,255,255,0.1) 50%, 
            rgba(255,255,255,0.05) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. CONFIGURATION SUPABASE
# =========================================================
LOGO_URL = "https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3"

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

# =========================================================
# 4. FONCTIONS BACKEND
# =========================================================
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

@st.cache_data(ttl=600)
def search_student(identifier):
    try:
        if identifier.isdigit():
            result = supabase.table('students')\
                .select("*")\
                .eq('id', identifier)\
                .execute()
        else:
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
    try:
        stats = supabase.table('attendance')\
            .select("status, sessions(date_time, courses(name, stream_target))")\
            .eq('student_id', student_id)\
            .execute()
        
        if not stats.data:
            return None
            
        total_sessions = len(stats.data)
        present_count = sum(1 for item in stats.data if item['status'] == 'PRESENT')
        absent_count = total_sessions - present_count
        attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
        
        courses_stats = {}
        for item in stats.data:
            course = item.get('sessions', {}).get('courses', {})
            if course:
                course_name = course.get('name', 'Inconnu')
                if course_name not in courses_stats:
                    courses_stats[course_name] = {'present': 0, 'total': 0}
                courses_stats[course_name]['total'] += 1
                if item['status'] == 'PRESENT':
                    courses_stats[course_name]['present'] += 1
        
        return {
            'total_sessions': total_sessions,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': round(attendance_percentage, 1),
            'courses_stats': courses_stats,
            'last_updated': datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    except Exception as e:
        st.error(f"Erreur lors du chargement des stats: {e}")
        return None

@st.cache_data(ttl=600)
def get_courses(stream):
    try:
        return supabase.table('courses').select("*").eq('stream_target', stream).execute().data
    except Exception:
        return []

@st.cache_data(ttl=60)
def get_students(stream):
    return supabase.table('students').select("*").eq('stream', stream).order('last_name').execute().data

def save_attendance(course_id, date_obj, present_ids, all_students):
    try:
        date_iso = date_obj.isoformat()
        existing_session = supabase.table('sessions')\
            .select("id")\
            .eq("course_id", course_id)\
            .eq("date_time", date_iso)\
            .execute()

        if existing_session.data:
            sess_id = existing_session.data[0]['id']
        else:
            new_sess = supabase.table('sessions').insert({
                "course_id": course_id, 
                "date_time": date_iso
            }).execute()
            sess_id = new_sess.data[0]['id']

        records = []
        for s in all_students:
            status = "PRESENT" if s['id'] in present_ids else "ABSENT"
            records.append({
                "session_id": sess_id,
                "student_id": s['id'],
                "status": status
            })

        supabase.table('attendance').upsert(records, on_conflict='session_id, student_id').execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur Technique : {e}")
        return False

def get_past_sessions(stream):
    courses = get_courses(stream)
    if not courses: 
        return []
    course_ids = [c['id'] for c in courses]
    
    try:
        response = supabase.table('sessions')\
            .select("*, courses(name)")\
            .in_('course_id', course_ids)\
            .order('date_time', desc=True)\
            .limit(20)\
            .execute()
        return response.data
    except Exception as e:
        st.warning(f"Impossible de charger l'historique: {e}")
        return []

def update_attendance_correction(session_id, updated_presence_map, all_students):
    try:
        records = []
        for s in all_students:
            status = "PRESENT" if updated_presence_map.get(s['id'], False) else "ABSENT"
            records.append({
                "session_id": session_id, 
                "student_id": s['id'], 
                "status": status
            })
        supabase.table('attendance').upsert(records, on_conflict='session_id, student_id').execute()
        return True
    except Exception as e:
        st.error(str(e))
        return False

def get_global_stats():
    try:
        return supabase.from_('student_stats').select("*").execute().data
    except Exception:
        st.warning("La vue SQL 'student_stats' n'est pas trouvée.")
        return []

# =========================================================
# 5. INTERFACE UTILISATEUR
# =========================================================
get_session_state()

# --- PAGE D'ACCUEIL PUBLIQUE ---
if not st.session_state['user_role']:
    if 'show_login' not in st.session_state:
        st.session_state['show_login'] = False
    
    if not st.session_state['show_login']:
        # BARRE DE NAVIGATION
        st.markdown("""
        <div class="nav-bar animate-fade-in">
            <div class="nav-title">
                <div class="nav-logo">🎓</div>
                <span style="font-weight: bold; color: #f1f5f9; font-size: clamp(0.95rem, 2vw, 1.1rem);">
                    Portail Académique EPL
                </span>
            </div>
            <div class="nav-actions">
        """, unsafe_allow_html=True)
        
        # Bouton d'accès admin
        if st.button("🔐 Accès Staff", key="nav_admin_access", type="secondary"):
            st.session_state['show_login'] = True
            st.rerun()
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # CONTENU PRINCIPAL
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # EN-TÊTE
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div class="logo-frame animate-fade-in">
                <div class='logo-corner logo-corner-tl'></div>
                <div class='logo-corner logo-corner-tr'></div>
                <div class='logo-corner logo-corner-bl'></div>
                <div class='logo-corner logo-corner-br'></div>
                <img src="{LOGO_URL}" alt="Logo EPL">
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class='main-header animate-fade-in'>
                <h1 style='margin: 0;'>Suivi Académique en Temps Réel</h1>
                <p style='color: rgba(255,255,255,0.9); font-size: clamp(0.95rem, 2.2vw, 1.1rem); margin-top: 0.5rem;'>
                    Université de Lomé • École Polytechnique
                </p>
                <div style='margin-top: 1rem;'>
                    <span class='licence-badge animate-pulse'>Programme Licence</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # SECTION RECHERCHE
        st.markdown("""
        <div class='search-box animate-fade-in'>
            <h2 style='color: #f1f5f9; margin-bottom: 1rem;'>🔍 Vérifiez vos présences</h2>
            <p style='color: #cbd5e1;'>Recherchez votre profil avec votre ID, nom ou prénom</p>
        </div>
        """, unsafe_allow_html=True)
        
        # BARRE DE RECHERCHE
        search_container = st.container()
        with search_container:
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_query = st.text_input(
                    " ",
                    placeholder="Ex: 12345 ou 'Koffi' ou 'Ama'...",
                    label_visibility="collapsed",
                    key="main_search"
                )
            with search_col2:
                search_clicked = st.button("🔍 Rechercher", use_container_width=True, type="primary", key="search_btn")
        
        # RÉSULTATS DE RECHERCHE
        if search_query and search_clicked:
            with st.spinner("Recherche en cours..."):
                results = search_student(search_query)
                
                if results:
                    if len(results) == 1:
                        student = results[0]
                        st.session_state['selected_student'] = student
                    else:
                        st.markdown(f"**{len(results)} résultat(s) trouvé(s)**")
                        
                        options = [f"{s['last_name']} {s['first_name']} • ID: {s['id']} • {s['stream']}" 
                                  for s in results]
                        
                        selected_option = st.selectbox(
                            "Sélectionnez votre profil:",
                            options,
                            index=0,
                            key="student_select"
                        )
                        
                        if st.button("📊 Voir les statistiques", type="primary", key="view_stats"):
                            selected_index = options.index(selected_option)
                            student = results[selected_index]
                            st.session_state['selected_student'] = student
        
        # PROFIL ÉTUDIANT
        if 'selected_student' in st.session_state:
            student = st.session_state['selected_student']
            
            st.markdown("---")
            st.markdown(f"""
            <div class='student-profile animate-fade-in'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;'>
                    <div>
                        <h2 style='margin: 0 0 0.5rem 0;'>👤 Votre Profil Académique</h2>
                        <p style='color: #cbd5e1; margin: 0;'>Informations personnelles et statistiques</p>
                    </div>
                    <span class='licence-badge'>Licence • {student['stream']}</span>
                </div>
                <div class='responsive-grid'>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Nom Complet</h4>
                        <p style='font-size: clamp(1rem, 2.2vw, 1.2rem); font-weight: bold; margin: 0; color: #f1f5f9;'>
                            {student['last_name'].upper()} {student['first_name']}
                        </p>
                    </div>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Matricule</h4>
                        <p style='font-size: clamp(1.2rem, 2.8vw, 1.4rem); font-weight: bold; margin: 0; color: #3B82F6;'>
                            {student['id']}
                        </p>
                        <small style='color: #64748b;'>Identifiant unique</small>
                    </div>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Filière</h4>
                        <p style='font-size: clamp(1rem, 2.2vw, 1.2rem); font-weight: bold; margin: 0; color: #10B981;'>
                            {student['stream']}
                        </p>
                    </div>
                    <div class='metric-card'>
                        <h4 style='color: #94a3b8; margin-bottom: 0.5rem;'>Niveau</h4>
                        <p style='font-size: clamp(1rem, 2.2vw, 1.2rem); font-weight: bold; margin: 0; color: #8B5CF6;'>
                            Licence
                        </p>
                        <small style='color: #64748b;'>Cycle académique</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # STATISTIQUES
            with st.spinner("Chargement de vos statistiques..."):
                stats = get_student_stats(student['id'])
                
                if stats:
                    # KPI CARDS
                    cols = st.columns(4)
                    metrics = [
                        (f"{stats['attendance_percentage']}%", "Taux de Présence", "#3B82F6"),
                        (stats['total_sessions'], "Séances Total", "#60A5FA"),
                        (stats['present_count'], "Présences", "#10B981"),
                        (stats['absent_count'], "Absences", "#EF4444")
                    ]
                    
                    for idx, (value, title, color) in enumerate(metrics):
                        with cols[idx]:
                            progress_html = f'<progress value="{stats["attendance_percentage"]}" max="100" style="width: 100%; height: 8px; margin-top: 0.5rem;"></progress>' if idx == 0 else ''
                            st.markdown(f"""
                            <div class='metric-card animate-fade-in'>
                                <h4 style='color: #cbd5e1; margin-bottom: 0.5rem;'>{title}</h4>
                                <div class='highlight-stat' style='color: {color};'>{value}</div>
                                {progress_html}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # DÉTAIL PAR MATIÈRE
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
                        
                        tab1, tab2 = st.tabs(["📈 Graphique", "📋 Tableau"])
                        
                        with tab1:
                            chart_data = pd.DataFrame(courses_df)
                            chart_data['Taux_num'] = chart_data['Taux'].str.replace('%', '').astype(float)
                            
                            chart = alt.Chart(chart_data).mark_bar().encode(
                                x=alt.X('Matière', sort='-y', title='Matière'),
                                y=alt.Y('Taux_num', title='Taux de présence (%)'),
                                color=alt.Color('Taux_num', scale=alt.Scale(scheme='blues')),
                                tooltip=['Matière', 'Taux', 'Séances', 'Présences']
                            ).properties(height=300)
                            
                            st.altair_chart(chart, use_container_width=True)
                        
                        with tab2:
                            st.dataframe(
                                courses_data.sort_values('Taux', ascending=False),
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
                    
                    # ACTIONS
                    st.caption(f"🔄 Dernière mise à jour: {stats['last_updated']}")
                    
                    col_reset1, col_reset2, col_reset3 = st.columns([1, 2, 1])
                    with col_reset2:
                        if st.button("🔁 Nouvelle recherche", type="secondary", use_container_width=True):
                            del st.session_state['selected_student']
                            st.rerun()
                    
                else:
                    st.info("📊 Aucune donnée de présence disponible pour le moment.")
        
        # SECTION INFORMATIVE
        st.markdown("---")
        st.markdown("### 💡 Fonctionnalités du Portail")
        
        cols_info = st.columns(3)
        features = [
            ("📱", "Accès Mobile", "Consultez vos stats depuis votre smartphone", "#3B82F6"),
            ("📈", "Statistiques Détaillées", "Visualisez vos progrès par matière", "#10B981"),
            ("🔒", "Données Sécurisées", "Vos informations sont protégées", "#8B5CF6")
        ]
        
        for idx, (icon, title, desc, color) in enumerate(features):
            with cols_info[idx]:
                st.markdown(f"""
                <div class='home-card animate-fade-in'>
                    <div style='color: {color}; font-size: 2rem; margin-bottom: 1rem;'>{icon}</div>
                    <h4 style='color: {color};'>{title}</h4>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # FOOTER
        st.markdown("---")
        col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])
        with col_footer2:
            st.markdown(f"""
            <div style='text-align: center; padding: 1.5rem 0;'>
                <div class='logo-frame-small' style='margin: 0 auto 1rem auto;'>
                    <img src="{LOGO_URL}" alt="Logo EPL">
                </div>
                <p style='color: #94a3b8; font-size: 0.85rem; margin: 0; line-height: 1.5;'>
                    © 2024 École Polytechnique de Lomé<br>
                    <span style='font-size: 0.8rem; color: #64748b;'>Portail Académique v2.0 • Responsive Design</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # ============ PAGE DE CONNEXION ============
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Logo
            st.markdown(f"""
            <div class='logo-frame-login animate-fade-in'>
                <div class='logo-corner logo-corner-tl'></div>
                <div class='logo-corner logo-corner-tr'></div>
                <div class='logo-corner logo-corner-bl'></div>
                <div class='logo-corner logo-corner-br'></div>
                <img src="{LOGO_URL}" alt="Logo EPL">
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<h2 style='text-align: center; margin-bottom: 1.5rem;'>Accès Administration</h2>", unsafe_allow_html=True)
            
            # Carte de connexion
            with st.container():
                st.markdown("""
                <div style='
                    background: linear-gradient(145deg, #1e293b, #0f172a);
                    padding: clamp(1.2rem, 2.5vw, 2rem);
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    border: 1px solid #475569;
                '>
                """, unsafe_allow_html=True)
                
                pwd = st.text_input("Mot de passe", type="password", key="login_password", 
                                   placeholder="Entrez le mot de passe d'accès")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("🔐 Se connecter", use_container_width=True, type="primary"):
                        if login(pwd):
                            st.success("✅ Connexion réussie !")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Accès refusé. Vérifiez vos identifiants.")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Bouton retour
            if st.button("← Retour à l'accueil", type="secondary", use_container_width=True):
                st.session_state['show_login'] = False
                if 'selected_student' in st.session_state:
                    del st.session_state['selected_student']
                st.rerun()
    
    st.stop()

# =========================================================
# 6. INTERFACE ADMIN
# =========================================================
with st.sidebar:
    st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
    
    # Logo sidebar
    st.markdown(f"""
    <div style='text-align: center; margin-bottom: 1.2rem;'>
        <div class='logo-frame-small'>
            <div class='logo-corner logo-corner-tl'></div>
            <div class='logo-corner logo-corner-tr'></div>
            <div class='logo-corner logo-corner-bl'></div>
            <div class='logo-corner logo-corner-br'></div>
            <img src="{LOGO_URL}" alt="Logo EPL">
        </div>
        <p style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>Panel d'administration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Infos utilisateur
    st.markdown(f"**👤 Rôle :** `{st.session_state['user_role']}`")
    if st.session_state['user_scope'] != 'ALL':
        st.markdown(f"**🎯 Filière :** `{st.session_state['user_scope']}`")
    
    st.divider()
    
    # Menu dynamique
    options = []
    if st.session_state['user_role'] == 'DELEGATE':
        options = ["📝 Faire l'Appel"]
    elif st.session_state['user_role'] == 'PROF':
        options = ["📊 Tableau de Bord", "🚨 Alertes Absences", "🔎 Explorer les Données"]
    elif st.session_state['user_role'] == 'ADMIN':
        options = ["🛡️ Super Admin", "✏️ Correction d'Erreurs", "📝 Faire l'Appel (Admin)", "📈 Stats Globales"]
    
    options.append("🚪 Déconnexion")
    
    selected = option_menu(
        "Menu Principal", 
        options,
        icons=[option.split()[0] for option in options],
        menu_icon="menu-up",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#60a5fa", "font-size": "1.1rem"},
            "nav-link": {
                "font-size": "0.9rem",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#334155",
            },
            "nav-link-selected": {"background-color": "#3b82f6", "font-weight": "600"},
        }
    )
    
    if selected == "🚪 Déconnexion":
        st.session_state['user_role'] = None
        st.session_state['user_scope'] = None
        st.session_state['show_login'] = False
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Fonction header pour pages admin
def admin_header(title, icon):
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.markdown(f"""
        <div class='logo-frame-small'>
            <div class='logo-corner logo-corner-tl'></div>
            <div class='logo-corner logo-corner-tr'></div>
            <div class='logo-corner logo-corner-bl'></div>
            <div class='logo-corner logo-corner-br'></div>
            <img src="{LOGO_URL}" alt="Logo EPL">
        </div>
        """, unsafe_allow_html=True)
    with col_title:
        st.title(f"{icon} {title}")
    return col_title

# --- PAGE: FAIRE L'APPEL ---
if selected in ["📝 Faire l'Appel", "📝 Faire l'Appel (Admin)"]:
    admin_header("Nouvelle Feuille de Présence", "📝")
    
    if st.session_state['user_role'] == 'DELEGATE':
        target_stream = st.session_state['user_scope']
        st.info(f"📍 **Filière assignée :** `{target_stream}`")
    else:
        target_stream = st.selectbox("Sélectionner la filière", ["LT", "GC", "IABD", "IS", "GE", "GM"], key="stream_select")
    
    c1, c2 = st.columns(2)
    courses = get_courses(target_stream)
    
    if not courses:
        st.warning("⚠️ Aucun cours trouvé pour cette filière.")
    else:
        course_map = {c['name']: c['id'] for c in courses}
        chosen_course = c1.selectbox("Matière", list(course_map.keys()), key="course_select")
        chosen_date = c2.date_input("Date du cours", datetime.now(), key="date_select")
        
        if st.button("📋 Charger la liste des étudiants", type="primary", key="load_students"):
            st.session_state['attendance_context'] = {
                'students': get_students(target_stream),
                'course_id': course_map[chosen_course],
                'course_name': chosen_course
            }
    
    if 'attendance_context' in st.session_state:
        ctx = st.session_state['attendance_context']
        st.divider()
        st.subheader(f"Appel : {ctx['course_name']} ({len(ctx['students'])} étudiants)")
        
        with st.form("attendance_form"):
            present_ids = []
            
            # Grille responsive selon taille écran
            cols_per_row = 3  # Desktop
            if st.session_state.get('screen_width', 0) < 768:
                cols_per_row = 2  # Mobile
            
            cols = st.columns(cols_per_row)
            for i, s in enumerate(ctx['students']):
                col_idx = i % cols_per_row
                with cols[col_idx]:
                    is_checked = st.checkbox(
                        f"**{s['last_name']}** {s['first_name']}", 
                        value=True, 
                        key=f"chk_{s['id']}",
                        help=f"ID: {s['id']}"
                    )
                    if is_checked:
                        present_ids.append(s['id'])
            
            st.markdown("---")
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            with col_submit2:
                submitted = st.form_submit_button("✅ Enregistrer l'appel", use_container_width=True, type="primary")
            
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
                        st.success("✅ Appel enregistré avec succès !")
                        del st.session_state['attendance_context']
                        time.sleep(1.5)
                        st.rerun()

# --- PAGE: CORRECTION D'ERREURS ---
elif selected == "✏️ Correction d'Erreurs":
    admin_header("Correction d'Appel", "✏️")
    st.info("Modifier rétroactivement les présences d'une session passée.")
    
    col_f, col_s = st.columns(2)
    stream_fix = col_f.selectbox("1. Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"], key="fix_stream")
    
    sessions_data = get_past_sessions(stream_fix)
    
    if sessions_data:
        sess_options = {}
        for s in sessions_data:
            course_name = s['courses']['name'] if s.get('courses') else "Matière Inconnue"
            label = f"{s['date_time'][:10]} | {course_name}"
            sess_options[label] = s['id']
            
        chosen_sess_label = col_s.selectbox("2. Sélectionner la séance", list(sess_options.keys()), key="session_select")
        
        if st.button("📥 Charger les données", type="primary", key="load_session"):
            chosen_sess_id = sess_options[chosen_sess_label]
            
            all_students = get_students(stream_fix)
            attendance_records = supabase.table('attendance').select("*").eq('session_id', chosen_sess_id).execute().data
            present_set = {r['student_id'] for r in attendance_records if r['status'] == 'PRESENT'}
            
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
    
    if 'editor_data' in st.session_state:
        st.divider()
        st.markdown("#### Modifier les présences :")
        
        edited_df = st.data_editor(
            st.session_state['editor_data'],
            column_config={
                "Présent": st.column_config.CheckboxColumn("Présent", help="Cocher si présent"),
                "ID": st.column_config.Column(disabled=True),
                "Nom": st.column_config.Column(disabled=True),
                "Prénom": st.column_config.Column(disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )
        
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        with col_save2:
            if st.button("💾 Enregistrer les corrections", type="primary", use_container_width=True):
                updated_map = dict(zip(edited_df['ID'], edited_df['Présent']))
                
                if update_attendance_correction(st.session_state['fix_session_id'], updated_map, st.session_state['fix_students_ref']):
                    st.success("✅ Modifications enregistrées !")
                    time.sleep(1.5)
                    del st.session_state['editor_data']
                    st.rerun()

# --- PAGES STATISTIQUES ---
elif selected in ["📊 Tableau de Bord", "📈 Stats Globales", "🚨 Alertes Absences", "🔎 Explorer les Données"]:
    
    if selected == "📊 Tableau de Bord":
        admin_header("Tableau de Bord Académique", "📊")
    elif selected == "📈 Stats Globales":
        admin_header("Statistiques Globales", "📈")
    elif selected == "🚨 Alertes Absences":
        admin_header("Alertes Absences", "🚨")
    elif selected == "🔎 Explorer les Données":
        admin_header("Explorateur de Données", "🔎")
    
    df = pd.DataFrame(get_global_stats())
    
    if df.empty:
        st.warning("📭 Aucune donnée statistique disponible.")
    else:
        if selected in ["📊 Tableau de Bord", "📈 Stats Globales"]:
            filieres_dispo = df['stream'].unique()
            filieres = st.multiselect("Filtrer par filière", filieres_dispo, default=filieres_dispo, key="filter_stream")
            df_filtered = df[df['stream'].isin(filieres)]
            
            col1, col2, col3 = st.columns(3)
            avg = df_filtered['attendance_percentage'].mean()
            col1.metric("🎯 Taux Moyen", f"{avg:.1f}%")
            col2.metric("👥 Étudiants", len(df_filtered))
            max_sess = df_filtered['total_sessions'].max() if 'total_sessions' in df_filtered.columns else 0
            col3.metric("📅 Sessions Max", max_sess)
            
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Distribution des taux**")
                chart = alt.Chart(df_filtered).mark_bar().encode(
                    x=alt.X("attendance_percentage", bin=True, title="Taux (%)"),
                    y=alt.Y('count()', title="Nombre d'étudiants"),
                    color='stream'
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                
            with c2:
                st.markdown("**Comparatif par filière**")
                chart2 = alt.Chart(df_filtered).mark_boxplot().encode(
                    x='stream',
                    y=alt.Y('attendance_percentage', title="Taux de présence (%)"),
                    color='stream'
                )
                st.altair_chart(chart2, use_container_width=True)
        
        elif selected == "🚨 Alertes Absences":
            red_list = df[df['attendance_percentage'] < 50].sort_values('attendance_percentage')
            
            if red_list.empty:
                st.success("✅ Aucun étudiant en dessous de 50%.")
            else:
                st.error(f"⚠️ {len(red_list)} étudiant(s) nécessite(nt) une attention.")
                
                st.dataframe(
                    red_list[['first_name', 'last_name', 'stream', 'attendance_percentage', 'absent_count']],
                    column_config={
                        "attendance_percentage": st.column_config.ProgressColumn("Taux", format="%.1f%%", min_value=0, max_value=100),
                        "absent_count": st.column_config.NumberColumn("Absences totales"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
        
        elif selected == "🔎 Explorer les Données":
            st.dataframe(
                df,
                column_config={
                    "attendance_percentage": st.column_config.ProgressColumn("Taux", format="%.1f%%", min_value=0, max_value=100),
                },
                use_container_width=True,
                hide_index=True
            )

# ----------------------------------------------------------------------------------
# NOUVELLE SECTION : SUPER ADMIN
# ----------------------------------------------------------------------------------
elif selected == "🛡️ Super Admin":
    admin_header("Super Admin & Outils Avancés", "🛡️")
    
    # Onglets de fonctionnalités
    tab_etudiant, tab_export, tab_autres = st.tabs([
        "👨‍🎓 Gestion des Étudiants", 
        "📥 Exporter les Données", 
        "⚙️ Maintenance"
    ])
    
    # =========================================================
    # 1.1. Onglet Gestion des Étudiants
    # =========================================================
    with tab_etudiant:
        st.subheader("👤 Ajouter un Nouvel Étudiant")
        st.info("Utilisez les filières existantes (LT, GC, IABD, IS, GE, GM). L'ID doit être unique.")
        
        # Formulaire d'ajout
        with st.form("add_student_form", clear_on_submit=True):
            col_id, col_filiere = st.columns(2)
            new_id = col_id.text_input("Matricule (ID Unique)*", placeholder="Ex: LF-LT-019", help="Doit être unique")
            new_stream = col_filiere.selectbox("Filière*", ["LT", "GC", "IABD", "IS", "GE", "GM"])
            
            col_nom, col_prenom = st.columns(2)
            new_last_name = col_nom.text_input("Nom de Famille*").upper()
            new_first_name = col_prenom.text_input("Prénom*")
            
            # Champs optionnels
            col_phone, col_email = st.columns(2)
            new_phone = col_phone.text_input("📞 Téléphone (Optionnel)")
            new_email = col_email.text_input("📧 Email (Optionnel)")
            
            col_submit1, col_submit2 = st.columns([1, 2])
            with col_submit2:
                submitted = st.form_submit_button("➕ Enregistrer l'étudiant", type="primary", use_container_width=True)
            
            if submitted:
                if new_id and new_last_name and new_first_name and new_stream:
                    # Vérifier si l'ID existe déjà
                    existing_student = supabase.table('students')\
                        .select("id")\
                        .eq('id', new_id)\
                        .execute()
                    
                    if existing_student.data:
                        st.error(f"❌ L'ID '{new_id}' existe déjà. Veuillez en choisir un autre.")
                    else:
                        try:
                            # Préparer les données
                            student_data = {
                                "id": new_id,
                                "last_name": new_last_name,
                                "first_name": new_first_name,
                                "stream": new_stream
                            }
                            
                            # Ajouter les champs optionnels s'ils sont remplis
                            if new_phone:
                                student_data["phone"] = new_phone
                            if new_email:
                                student_data["email"] = new_email
                            
                            # Insertion dans Supabase
                            response = supabase.table('students').insert(student_data).execute()
                            
                            if response.data:
                                st.success(f"✅ Étudiant {new_last_name} {new_first_name} ajouté avec succès !")
                                st.balloons()
                                # Nettoyer le cache pour que le nouvel étudiant apparaisse dans l'appel
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de l'ajout de l'étudiant.")
                                
                        except Exception as e:
                            st.error(f"❌ Erreur technique : {str(e)}")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs obligatoires (*).")
        
        st.divider()
        
        # Rechercher et modifier un étudiant
        st.subheader("🔍 Rechercher et Modifier un Étudiant")
        
        col_search, col_action = st.columns([3, 1])
        with col_search:
            search_term = st.text_input("Rechercher par ID, nom ou prénom", 
                                       placeholder="Entrez un ID, nom ou prénom...",
                                       key="student_search")
        
        if search_term:
            try:
                # Recherche dans la base de données
                search_results = supabase.table('students')\
                    .select("*")\
                    .or_(f"id.ilike.%{search_term}%,last_name.ilike.%{search_term}%,first_name.ilike.%{search_term}%")\
                    .limit(10)\
                    .execute()
                
                if search_results.data:
                    students_df = pd.DataFrame(search_results.data)
                    
                    st.markdown(f"**📋 {len(search_results.data)} résultat(s) trouvé(s)**")
                    
                    # Afficher les résultats dans un data editor
                    edited_df = st.data_editor(
                        students_df[['id', 'last_name', 'first_name', 'stream', 'phone', 'email']],
                        column_config={
                            "id": st.column_config.TextColumn("Matricule", disabled=True),
                            "last_name": st.column_config.TextColumn("Nom"),
                            "first_name": st.column_config.TextColumn("Prénom"),
                            "stream": st.column_config.SelectboxColumn(
                                "Filière",
                                options=["LT", "GC", "IABD", "IS", "GE", "GM"]
                            ),
                            "phone": st.column_config.TextColumn("Téléphone"),
                            "email": st.column_config.TextColumn("Email")
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic",
                        key="student_editor"
                    )
                    
                    if st.button("💾 Enregistrer les modifications", type="primary", use_container_width=True):
                        try:
                            # Mettre à jour chaque étudiant modifié
                            for index, row in edited_df.iterrows():
                                supabase.table('students')\
                                    .update({
                                        'last_name': row['last_name'],
                                        'first_name': row['first_name'],
                                        'stream': row['stream'],
                                        'phone': row['phone'] if pd.notna(row['phone']) else None,
                                        'email': row['email'] if pd.notna(row['email']) else None
                                    })\
                                    .eq('id', row['id'])\
                                    .execute()
                            
                            st.success("✅ Modifications enregistrées avec succès !")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la mise à jour : {str(e)}")
                            
                else:
                    st.info("ℹ️ Aucun étudiant trouvé avec ce critère de recherche.")
                    
            except Exception as e:
                st.error(f"❌ Erreur de recherche : {str(e)}")
    
    # =========================================================
    # 1.2. Onglet Exporter les Données
    # =========================================================
    with tab_export:
        st.subheader("📊 Téléchargement des Enregistrements")
        st.info("Exportez les données brutes pour l'analyse ou l'archivage.")
        
        # Options d'export
        export_type = st.radio(
            "Type d'exportation :",
            ["📋 Toutes les présences", "👨‍🎓 Liste des étudiants", "📚 Liste des cours"],
            horizontal=True
        )
        
        # Fonction pour récupérer toutes les présences avec jointures
        @st.cache_data(ttl=3600)
        def get_all_attendance_export():
            try:
                result = supabase.table('attendance')\
                    .select("*, students(id, last_name, first_name, stream), sessions(date_time, courses(name))")\
                    .execute()
                
                data = result.data
                if not data:
                    return pd.DataFrame()

                export_data = []
                for row in data:
                    export_data.append({
                        'session_id': row['session_id'],
                        'student_id': row['students']['id'],
                        'last_name': row['students']['last_name'],
                        'first_name': row['students']['first_name'],
                        'stream': row['students']['stream'],
                        'course_name': row['sessions']['courses']['name'] if row['sessions'] and row['sessions']['courses'] else 'Inconnu',
                        'date_time': row['sessions']['date_time'] if row['sessions'] else 'Inconnu',
                        'status': row['status']
                    })
                
                return pd.DataFrame(export_data)
            except Exception as e:
                st.error(f"Erreur d'exportation: {e}")
                return pd.DataFrame()
        
        # Fonction pour récupérer la liste des étudiants
        @st.cache_data(ttl=3600)
        def get_all_students_export():
            try:
                result = supabase.table('students').select("*").execute()
                return pd.DataFrame(result.data)
            except Exception as e:
                st.error(f"Erreur d'exportation étudiants: {e}")
                return pd.DataFrame()
        
        # Fonction pour récupérer la liste des cours
        @st.cache_data(ttl=3600)
        def get_all_courses_export():
            try:
                result = supabase.table('courses').select("*").execute()
                return pd.DataFrame(result.data)
            except Exception as e:
                st.error(f"Erreur d'exportation cours: {e}")
                return pd.DataFrame()
        
        # Exécuter l'export selon le type sélectionné
        if export_type == "📋 Toutes les présences":
            df_export = get_all_attendance_export()
            export_name = "presences"
        elif export_type == "👨‍🎓 Liste des étudiants":
            df_export = get_all_students_export()
            export_name = "etudiants"
        else:  # Liste des cours
            df_export = get_all_courses_export()
            export_name = "cours"

        if df_export.empty:
            st.warning(f"📭 Aucune donnée de {export_name} à exporter.")
        else:
            st.markdown(f"**Aperçu des {len(df_export)} enregistrements :**")
            st.dataframe(df_export.head(), hide_index=True)
            
            # Préparer le fichier CSV
            csv = df_export.to_csv(index=False, encoding='utf-8-sig')
            
            current_time = datetime.now().strftime("%Y%m%d_%H%M")
            
            # Bouton de téléchargement
            col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
            with col_dl2:
                st.download_button(
                    label=f"⬇️ Télécharger ({len(df_export)} enregistrements)",
                    data=csv,
                    file_name=f'EPL_{export_name}_export_{current_time}.csv',
                    mime='text/csv',
                    use_container_width=True,
                    type="primary",
                    key=f"download_{export_name}"
                )
            
            # Option d'export JSON
            if st.checkbox("Exporter également en format JSON"):
                json_data = df_export.to_json(orient='records', force_ascii=False, indent=2)
                
                st.download_button(
                    label="⬇️ Télécharger en JSON",
                    data=json_data,
                    file_name=f'EPL_{export_name}_export_{current_time}.json',
                    mime='application/json',
                    use_container_width=True,
                    type="secondary"
                )
    
    # =========================================================
    # 1.3. Onglet Maintenance
    # =========================================================
    with tab_autres:
        st.subheader("⚙️ Outils de Maintenance")
        
        col_maint1, col_maint2 = st.columns(2)
        
        with col_maint1:
            st.markdown("#### 🔄 Gestion des Caches")
            if st.button("🗑️ Purger tous les caches", 
                        help="Force le rechargement de toutes les données depuis Supabase",
                        use_container_width=True,
                        type="secondary"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Caches purgés. Les prochaines requêtes rechargeront les données.")
                time.sleep(1)
                st.rerun()
            
            st.markdown("---")
            
            st.markdown("#### 📊 Statistiques Base de Données")
            try:
                # Compter les étudiants
                students_count = supabase.table('students').select("*", count="exact").execute().count
                # Compter les présences
                attendance_count = supabase.table('attendance').select("*", count="exact").execute().count
                # Compter les sessions
                sessions_count = supabase.table('sessions').select("*", count="exact").execute().count
                
                st.metric("👨‍🎓 Étudiants", students_count or 0)
                st.metric("📋 Enregistrements de présence", attendance_count or 0)
                st.metric("📅 Sessions de cours", sessions_count or 0)
                
            except Exception as e:
                st.error(f"❌ Erreur de statistiques: {str(e)}")
        
        with col_maint2:
            st.markdown("#### 🔑 Gestion des Accès")
            
            st.info("Mots de passe des délégués (lecture seule) :")
            
            # Afficher les mots de passe des délégués (sécurisé - en lecture seule)
            delegates_data = []
            for pass_key, stream in CREDENTIALS["DELEGATES"].items():
                delegates_data.append({
                    "Filière": stream,
                    "Mot de passe": pass_key,
                    "Rôle": "Délégué"
                })
            
            if delegates_data:
                delegates_df = pd.DataFrame(delegates_data)
                st.dataframe(
                    delegates_df,
                    column_config={
                        "Mot de passe": st.column_config.TextColumn(
                            "Mot de passe",
                            help="Mot de passe d'accès pour les délégués"
                        )
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Aucun délégué configuré.")
            
            st.markdown("---")
            
            st.markdown("#### 🧹 Nettoyage des Données")
            st.warning("⚠️ Actions irréversibles")
            
            # Option pour supprimer les données de test
            if st.button("🧪 Supprimer données de test", 
                        help="À utiliser avec précaution !",
                        use_container_width=True,
                        type="secondary",
                        disabled=True):  # Désactivé par sécurité
                st.info("Cette fonctionnalité est désactivée pour des raisons de sécurité.")

# ----------------------------------------------------------------------------------
# FIN DE LA SECTION SUPER ADMIN
# ----------------------------------------------------------------------------------
     
# =========================================================
# 7. SCRIPT POUR DÉTECTION D'ÉCRAN (optionnel)
# =========================================================
st.markdown("""
<script>
// Détection de la largeur d'écran pour Streamlit
function updateScreenSize() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // Envoyer à Streamlit
    if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: width,
            key: 'screen_width'
        }, '*');
    }
}

// Mettre à jour au chargement et au redimensionnement
window.addEventListener('load', updateScreenSize);
window.addEventListener('resize', updateScreenSize);
</script>
""", unsafe_allow_html=True)

# =========================================================
# 8. FIN DU CODE
# =========================================================







