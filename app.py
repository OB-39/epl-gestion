import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="EPL - Gestion de Présence", layout="centered")

# Récupération des clés secrètes (Configuration pour le Cloud)
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

# --- FONCTIONS ---
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
            attendance_records.append({
                "session_id": new_session_id,
                "student_id": student['id'],
                "status": status
            })
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

# --- INTERFACE ---
menu = st.sidebar.radio("Navigation", ["🔍 Espace Étudiant", "🔐 Espace Professeur"])

if menu == "🔍 Espace Étudiant":
    st.title("🎓 Mon Suivi de Présence")
    search = st.text_input("Votre Matricule ou Nom :")
    if st.button("Rechercher") and search:
        results = get_student_stats(search.strip())
        if results:
            for student in results:
                st.divider()
                st.subheader(f"{student['first_name']} {student['last_name']}")
                st.caption(f"Filière : {student['stream']} | ID : {student['student_id']}")
                c1, c2 = st.columns(2)
                c1.metric("Présences", student['present_count'])
                c2.metric("Taux Global", f"{student['attendance_percentage']}%")
        else:
            st.warning("Aucun étudiant trouvé.")

elif menu == "🔐 Espace Professeur":
    st.title("📋 Faire l'Appel")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    if pwd == "EPL2024":
        c1, c2 = st.columns(2)
        filiere = c1.selectbox("Filière", ["LT", "GC", "IABD", "IS", "GE", "GM"])
        courses = get_courses_by_stream(filiere)
        if courses:
            course_map = {c['name']: c['id'] for c in courses}
            c_name = c2.selectbox("Matière", list(course_map.keys()))
            if st.button("Charger la liste"):
                st.session_state['students'] = get_students_by_stream(filiere)
                st.session_state['course_id'] = course_map[c_name]
            
            if 'students' in st.session_state:
                with st.form("appel"):
                    present = []
                    cols = st.columns(2)
                    for i, s in enumerate(st.session_state['students']):
                        if cols[i%2].checkbox(f"{s['last_name']} {s['first_name']}", True, key=s['id']):
                            present.append(s['id'])
                    if st.form_submit_button("Valider"):
                        save_attendance(st.session_state['course_id'], datetime.now(), present, st.session_state['students'])
                        st.success("Enregistré !")
                        del st.session_state['students']
                        time.sleep(2)
                        st.rerun()
        else:
            st.warning("Aucun cours pour cette filière.")