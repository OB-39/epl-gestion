import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time
from streamlit_option_menu import option_menu # Nouveau menu
import altair as alt # Pour les graphiques

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="EPL - Portail de Présence",
    page_icon="🎓",
    layout="wide", # Utilise toute la largeur de l'écran
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ (Pour le look "App") ---
st.markdown("""
<style>
    /* Carte blanche avec ombre */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    /* Titre principal coloré */
    h1 {
        color: #1E3A8A; /* Bleu EPL */
        font-weight: 700;
    }
    /* Boutons stylisés */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except FileNotFoundError:
    st.error("Les clés de sécurité ne sont pas configurées.")
    st.stop()

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase = init_connection()

# --- FONCTIONS MÉTIER (Inchangées) ---
def get_courses_by_stream(stream):
    response = supabase.table('courses').select("*").eq('stream_target', stream).execute()
    return response.data

def get_students_by_stream(stream):
    response = supabase.table('students').select("*").eq('stream', stream).order('last_name').execute()
    return response.data

def save_attendance(course_id, date, present_students_ids, all_students):
    try:
        session_data = {"course_id": course_id, "date_time": date.isoformat()}
        res_session = supabase.table('sessions').insert(session_data).execute()
        new_session_id = res_session.data[0]['id']
        attendance_records = []
        for student in all_students:
            status = "PRESENT" if student['id'] in present_students_ids else "ABSENT"
            attendance_records.append({"session_id": new_session_id, "student_id": student['id'], "status": status})
        supabase.table('attendance').insert(attendance_records).execute()
        return True
    except Exception as e:
        st.error(f"Erreur : {e}")
        return False

def get_student_stats(search_term):
    response = supabase.from_('student_stats').select("*").eq('student_id', search_term).execute()
    if not response.data:
        response = supabase.from_('student_stats').select("*").ilike('last_name', f"%{search_term}%").execute()
    return response.data

# --- INTERFACE PRINCIPALE ---

# Menu latéral moderne
with st.sidebar:
    # Logo EPL (ou placeholder)
    st.image("https://tse4.mm.bing.net/th/id/OIP.AQ-vlqgp9iyDGW8ag9oCsgHaHS?rs=1&pid=ImgDetMain&o=7&rm=3", width=150) 
    st.markdown("### EPL - Gestion")
    
    selected = option_menu(
        menu_title=None,
        options=["Espace Étudiant", "Espace Professeur"],
        icons=["person-badge", "pencil-square"], # Icônes Bootstrap
        menu_icon="cast",
        default_index=0,
        styles={
            "nav-link-selected": {"background-color": "#1E3A8A"}, # Bleu EPL
        }
    )
    st.info("Application de suivi des présences - Licence Fondamentale 2")

# === PAGE ÉTUDIANT ===
if selected == "Espace Étudiant":
    st.title("🎓 Mon Tableau de Bord")
    st.markdown("---")
    
    col_search, col_img = st.columns([2, 1])
    with col_search:
        st.markdown("#### Identification")
        search = st.text_input("🔍 Entrez votre Matricule ou votre Nom :", placeholder="Ex: LF-LT-001 ou ADONSOU")
        btn_search = st.button("Consulter mes stats", type="primary")

    if btn_search and search:
        with st.spinner("Analyse des données en cours..."):
            results = get_student_stats(search.strip())
            time.sleep(0.5) # Petit effet de chargement pour le "feeling"
            
            if results:
                for student in results:
                    st.success("Étudiant identifié !")
                    
                    # --- CARTE D'IDENTITÉ ---
                    with st.container():
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2 style="margin:0; color:#1E3A8A;">{student['first_name']} {student['last_name']}</h2>
                            <p style="color:gray;">Matricule : <b>{student['student_id']}</b> | Filière : <b>{student['stream']}</b></p>
                        </div>
                        """, unsafe_allow_html=True)

                    # --- KPI & GRAPHIQUES ---
                    col1, col2, col3 = st.columns(3)
                    
                    # KPI 1 : Présence
                    with col1:
                        st.metric("Taux de Présence", f"{student['attendance_percentage']}%")
                        # Barre de progression colorée
                        val = float(student['attendance_percentage']) / 100
                        if val >= 0.75:
                            st.progress(val, text="Excellent")
                        elif val >= 0.50:
                            st.progress(val, text="Attention")
                        else:
                            st.progress(val, text="Critique")

                    # KPI 2 : Sessions
                    with col2:
                        st.metric("Total Cours", student['total_sessions'])
                        st.metric("Cours Suivis", student['present_count'])

                    # Graphique Donut (Camembert)
                    with col3:
                        source = pd.DataFrame({
                            "État": ["Présent", "Absent"],
                            "Valeur": [student['present_count'], student['absent_count']]
                        })
                        base = alt.Chart(source).encode(
                            theta=alt.Theta("Valeur", stack=True)
                        )
                        pie = base.mark_arc(outerRadius=50).encode(
                            color=alt.Color("État", scale=alt.Scale(domain=["Présent", "Absent"], range=["#22c55e", "#ef4444"])),
                            tooltip=["État", "Valeur"]
                        )
                        st.altair_chart(pie, use_container_width=True)

            else:
                st.warning("⚠️ Aucun étudiant trouvé. Vérifiez l'orthographe.")

# === PAGE PROFESSEUR ===
elif selected == "Espace Professeur":
    st.title("📋 Module d'Appel")
    st.markdown("---")
    
    # --- EXPORT DES DONNÉES (Placé ici pour éviter l'erreur d'indentation) ---
    with st.sidebar:
        st.divider()
        st.markdown("### 📥 Rapports")
        if st.button("Télécharger les présences (CSV)"):
            st.info("Fonctionnalité d'export avancée à venir. Vous pouvez consulter la vue 'student_stats' sur Supabase.")

    # Zone de Login propre
    if "admin_logged" not in st.session_state:
        st.session_state["admin_logged"] = False

    if not st.session_state["admin_logged"]:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.markdown("### 🔒 Accès Sécurisé")
            pwd = st.text_input("Mot de passe", type="password")
            if st.button("Se Connecter"):
                if pwd == "EPL2024":
                    st.session_state["admin_logged"] = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
    
    else:
        # --- INTERFACE D'APPEL ---
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            filiere = st.selectbox("1️⃣ Choisir la Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
        
        with c2:
            courses = get_courses_by_stream(filiere)
            course_map = {c['name']: c['id'] for c in courses} if courses else {}
            c_name = st.selectbox("2️⃣ Choisir la Matière", list(course_map.keys()) if courses else ["Aucun cours"])
        
        with c3:
            date_cours = st.date_input("3️⃣ Date de la séance", datetime.now())
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Bouton de chargement
        if st.button("Charger la liste des étudiants ⬇️", type="primary", use_container_width=True):
            if courses:
                st.session_state['students_list'] = get_students_by_stream(filiere)
                st.session_state['current_course_id'] = course_map[c_name]
            else:
                st.warning("Aucun cours disponible.")

        # Affichage de la liste
        if 'students_list' in st.session_state:
            st.divider()
            st.subheader(f"👨‍🎓 Appel : {c_name}")
            
            with st.form("appel_form"):
                students = st.session_state['students_list']
                present = []
                
                # Grille responsive
                cols = st.columns(3)
                for i, s in enumerate(students):
                    # Style conditionnel pour les noms
                    with cols[i % 3]:
                        if st.checkbox(f"✅ {s['last_name']} {s['first_name']}", value=True, key=s['id']):
                            present.append(s['id'])
                
                st.markdown("---")
                submit = st.form_submit_button("💾 ENREGISTRER L'APPEL", type="primary", use_container_width=True)
                
                if submit:
                    success = save_attendance(st.session_state['current_course_id'], date_cours, present, students)
                    if success:
                        st.balloons() # ANIMATION !
                        st.success(f"✅ Appel enregistré avec succès ! ({len(present)}/{len(students)} présents)")
                        time.sleep(2)
                        del st.session_state['students_list']
                        st.rerun()
