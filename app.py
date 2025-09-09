# app.py (ФИНАЛЬНАЯ ВЕРСИЯ - Возвращена стандартная карта st.map)

import streamlit as st
import pandas as pd
import os
import io
# import pydeck as pdk <-- УБРАЛИ ЭТУ СТРОКУ

# --- НАСТРОЙКИ ---
DATA_FILE = "data.parquet" 
ADMIN_PASSWORD = "ooh_dashboard_admin_123" 
USER_PASSWORD = "user_123"

# --- ОБЩИЕ НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    layout="wide",
    page_title="OOH Analytics",
    page_icon="https://emojigraph.org/media/google/chart-increasing_1f4c8.png"
)

# --- CSS СТИЛИ (без изменений) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; padding-left: 5rem; padding-right: 5rem; }
    .card { background-color: #FFFFFF; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.05); border: 1px solid #E6E6E6; height: 100%; }
    .card h3 { margin-top: 0; }
    .kpi-card { display: flex; align-items: center; }
    .kpi-icon { font-size: 2rem; padding: 20px; border-radius: 50%; color: white; margin-right: 20px; }
    .kpi-text { text-align: left; }
    .kpi-value { font-size: 2.2rem; font-weight: bold; }
    .kpi-title { font-size: 0.9rem; color: grey; }
    div[data-testid="stToolbar"] { display: flex; gap: 1rem; width: 100%; }
    header, #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ (без изменений) ---
@st.cache_data
def load_data(file_path):
    return pd.read_parquet(file_path)

def process_uploaded_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        df.rename(columns={'Город': 'city', 'Формат поверхности2': 'format', 'Продавец': 'seller', 'surface_id': 'surface_id', 'Номер кс': 'surface_id', 'Номер конструкции': 'surface_id', 'GRP (18+)': 'grp', 'GRP (18+) в сутки': 'grp', 'OTS (18+)': 'ots', 'OTS (18+) тыс.чел. в сутки': 'ots', 'Широта': 'lat', 'Долгота': 'lon'}, inplace=True, errors='ignore')
        required_columns = ['surface_id', 'grp', 'ots', 'city', 'format', 'seller', 'lat', 'lon']
        for col in required_columns:
            if col not in df.columns: raise KeyError(f"В файле отсутствует столбец '{col}'.")
        for col in ['city', 'format', 'seller']: df[col] = df[col].astype(str)
        for col in ['lat', 'lon']: df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(subset=['city', 'format', 'lat', 'lon'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}"); return None

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

# --- СИСТЕМА АУТЕНТИФИКАЦИИ (без изменений) ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'role' not in st.session_state: st.session_state.role = None

def login():
    st.markdown("""<style> div[data-testid="stButton"] > button { background-color: #007bff; color: white; border-radius: 5px; padding: 10px 20px; } </style>""", unsafe_allow_html=True)
    st.header("Вход в систему OOH Analytics")
    password = st.text_input("Введите пароль:", type="password", label_visibility="collapsed")
    if st.button("Войти"):
        if password == ADMIN_PASSWORD: st.session_state.authenticated = True; st.session_state.role = "admin"; st.rerun()
        elif password == USER_PASSWORD: st.session_state.authenticated = True; st.session_state.role = "user"; st.rerun()
        else: st.error("Неверный пароль")

# --- ГЛАВНЫЙ БЛОК ПРИЛОЖЕНИЯ ---
if not st.session_state.authenticated:
    login()
else:
    # --- ХЕДЕР (без изменений) ---
    logo_col, title_col, controls_col, user_col = st.columns([1, 4, 3, 1])
    with logo_col: st.image("https://emojigraph.org/media/google/chart-increasing_1f4c8.png", width=60)
    with title_col: st.markdown("### OOH Analytics\n*Аналитика наружной рекламы*")
    with controls_col:
        with st.container():
            st.markdown('<div data-testid="stToolbar">', unsafe_allow_html=True)
            export_button_placeholder = st.empty()
            if st.session_state.role == "admin":
                uploaded_file = st.file_uploader("Загрузить Excel", type=["xlsx", "xls"], label_visibility="collapsed")
                if uploaded_file:
                    new_df = process_uploaded_file(uploaded_file)
                    if new_df is not None: new_df.to_parquet(DATA_FILE, index=False); st.cache_data.clear(); st.success("Файл обновлен!"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    with user_col:
        st.markdown(f"**{st.session_state.role.upper()}**")
        if st.button("Выход"): st.session_state.authenticated = False; st.session_state.role = None; st.rerun()
    st.markdown("---")
    
    # --- ОСНОВНОЙ ИНТЕРФЕЙС (изменения только в блоке карты) ---
    if not os.path.exists(DATA_FILE):
        st.info("Данные еще не загружены. Пожалуйста, попросите администратора загрузить файл.")
    else:
        df = load_data(DATA_FILE)
        
        main_cols = st.columns([1, 3])
        with main_cols[0]: # КОЛОНКА С ФИЛЬТРАМИ (без изменений)
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Фильтры")
                selected_city = st.selectbox("Город", options=["Все города"] + sorted(list(df['city'].unique())), label_visibility="collapsed")
                df_for_filters = df if selected_city == "Все города" else df[df['city'] == selected_city]
                selected_seller = st.selectbox("Продавец", options=["Все продавцы"] + sorted(list(df_for_filters['seller'].unique())), label_visibility="collapsed")
                st.markdown("##### Форматы поверхностей")
                format_options = sorted(df_for_filters['format'].unique())
                select_all_formats = st.checkbox("Выбрать все форматы", value=True)
                selected_formats = []
                for fmt in format_options:
                    if st.checkbox(fmt, value=select_all_formats, key=f"fmt_{fmt}"):
                        selected_formats.append(fmt)
                if not selected_formats: selected_formats = format_options if select_all_formats else []
                st.markdown("</div>", unsafe_allow_html=True)

        with main_cols[1]: # КОЛОНКА С КОНТЕНТОМ
            df_filtered = df.copy()
            if selected_city != "Все города": df_filtered = df_filtered[df_filtered['city'] == selected_city]
            if selected_seller != "Все продавцы": df_filtered = df_filtered[df_filtered['seller'] == selected_seller]
            if selected_formats: df_filtered = df_filtered[df_filtered['format'].isin(selected_formats)]
            else: df_filtered = pd.DataFrame()
            
            if df_filtered.empty:
                st.warning("Нет данных, соответствующих выбранным фильтрам.")
            else:
                kpi_cols = st.columns(3)
                total_surfaces, avg_grp, avg_ots_k = df_filtered['surface_id'].nunique(), df_filtered['grp'].mean(), df_filtered['ots'].mean()
                with kpi_cols[0]: st.markdown(f"""<div class='card kpi-card'><div class='kpi-icon' style='background-color: #4A90E2;'>📋</div><div class='kpi-text'><div class='kpi-value'>{total_surfaces/1000:.1f}K</div><div class='kpi-title'>Количество поверхностей</div></div></div>""", unsafe_allow_html=True)
                with kpi_cols[1]: st.markdown(f"""<div class='card kpi-card'><div class='kpi-icon' style='background-color: #50E3C2;'>📈</div><div class='kpi-text'><div class='kpi-value'>{avg_grp:.3f}</div><div class='kpi-title'>Средний GRP (18+)</div></div></div>""", unsafe_allow_html=True)
                with kpi_cols[2]: st.markdown(f"""<div class='card kpi-card'><div class='kpi-icon' style='background-color: #BD10E0;'>👥</div><div class='kpi-text'><div class='kpi-value'>{avg_ots_k:.1f}K</div><div class='kpi-title'>Средний OTS (18+)</div></div></div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.subheader("Аналитика по форматам")
                    summary_table = df_filtered.groupby(['city', 'seller', 'format']).agg(Количество=('surface_id', 'nunique'), Средний_GRP=('grp', 'mean'), Средний_OTS_тыс=('ots', 'mean')).reset_index().sort_values(by=['city'])
                    excel_data = to_excel(summary_table); export_button_placeholder.download_button("Экспорт в Excel", data=excel_data, file_name="ooh_analytics_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.dataframe(summary_table, use_container_width=True)
                    
                    # ИЗМЕНЕНО: ВОЗВРАЩЕНА СТАНДАРТНАЯ КАРТА ST.MAP
                    st.subheader("Карта поверхностей")
                    df_map = df_filtered[['lon', 'lat']].copy()
                    df_map.dropna(inplace=True)

                    if not df_map.empty:
                        st.map(df_map) # Просто, бесплатно, без ключей, но с большими точками
                    else:
                        st.info("Нет данных с координатами для отображения на карте.")
                        
                    st.markdown("</div>", unsafe_allow_html=True)