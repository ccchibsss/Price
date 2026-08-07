# -*- coding: utf-8 -*-
"""
МОНОЛИТНОЕ ПРИЛОЖЕНИЕ ПРАЙС-АНАЛИЗАТОР
Полностью самодостаточное Streamlit приложение (один файл)
"""
import streamlit as st
import pandas as pd
import os
import glob
import re
import tempfile
from io import BytesIO
from typing import Optional
from datetime import datetime
# ============================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================
st.set_page_config(
    page_title="📊 Прайс-анализатор",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ============================================================
# КАСТОМНЫЙ CSS (тёмная тема Streamlit Premium)
# ============================================================
st.markdown("""
<style>
  .main { background-color: #0f1117; }
  ::-webkit-scrollbar { width: 7px; height: 7px; }
  ::-webkit-scrollbar-thumb { background: #2d3139; border-radius: 4px; }
  
  .hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #1a1c30 50%, #0f172a 100%);
    border-radius: 18px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid #1e2230;
  }
  
  .stat-card {
    background: linear-gradient(180deg, #181b24 0%, #13161e 100%);
    border: 1px solid #2a2d38;
    border-radius: 14px;
    padding: 1.25rem;
  }
  
  .file-card {
    background: #181b24;
    border: 1px solid #2a2d38;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.35rem;
  }
  .file-card.success { border-left: 3px solid #10b981; }
  .file-card.error { border-left: 3px solid #ef4444; }
  
  .stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
  }
</style>
""", unsafe_allow_html=True)
# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
def detect_column(df: pd.DataFrame, keywords: list) -> Optional[str]:
    for col in df.columns:
        col_lower = str(col).strip().lower()
        for kw in keywords:
            if kw.lower() in col_lower:
                return col
    return None
def clean_price(val) -> Optional[float]:
    if pd.isna(val): return None
    if isinstance(val, (int, float)): return float(val) if val > 0 else None
    s = str(val).strip().replace('\xa0', '').replace(' ', '')
    if not s: return None
    s = re.sub(r'[^\d.,\-]', '', s)
    try:
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            parts = s.split(',')
            if len(parts[-1]) <= 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        return float(s)
    except:
        return None
def read_file(filepath: str) -> Optional[pd.DataFrame]:
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(filepath)
        for enc in ['utf-8', 'cp1251', 'windows-1251', 'koi8-r']:
            try:
                return pd.read_csv(filepath, encoding=enc)
            except:
                continue
        return pd.read_csv(filepath)
    except:
        return None
def process_folder(folder_path: str):
    """Основной алгоритм анализа прайсов"""
    file_statuses = []
    all_rows = []
    
    patterns = ['*.xlsx', '*.xls', '*.csv']
    found_files = set()
    for pat in patterns:
        found_files.update(glob.glob(os.path.join(folder_path, pat)))
        found_files.update(glob.glob(os.path.join(folder_path, '**', pat), recursive=True))
    files = sorted(found_files)
    
    if not files:
        return None, []
    
    for fpath in files:
        fname = os.path.basename(fpath)
        size = format_size(os.path.getsize(fpath))
        base_name = os.path.splitext(fname)[0]
        
        df = read_file(fpath)
        if df is None or df.empty:
            file_statuses.append({
                'name': fname, 'size': size, 'status': 'error',
                'msg': 'Файл пуст или повреждён'
            })
            continue
        
        col_art = detect_column(df, ['артикул', 'арт', 'sku', 'код', 'item', 'товар', 'code', 'id'])
        col_brand = detect_column(df, ['бренд', 'brand', 'производитель', 'make', 'марка'])
        col_price = detect_column(df, ['цена', 'price', 'cost', 'стоимость', 'закуп', 'сумма', 'ррц'])
        
        if col_price is None:
            for col in df.columns:
                sample = pd.to_numeric(df[col].head(30), errors='coerce')
                if sample.notna().sum() > 5:
                    col_price = col
                    break
        
        if col_art is None or col_price is None:
            file_statuses.append({
                'name': fname, 'size': size, 'status': 'error',
                'msg': 'Не найдены колонки Артикул/Цена'
            })
            continue
        
        sub = df[[col_art, col_price] + ([col_brand] if col_brand else [])].copy()
        rename_map = {col_art: 'артикул', col_price: 'цена'}
        if col_brand: rename_map[col_brand] = 'бренд'
        sub = sub.rename(columns=rename_map)
        
        if 'бренд' not in sub.columns:
            sub['бренд'] = '—'
        
        sub['цена'] = sub['цена'].apply(clean_price)
        sub['артикул'] = sub['артикул'].astype(str).str.strip()
        sub = sub.dropna(subset=['артикул', 'цена'])
        sub = sub[sub['артикул'] != '']
        sub = sub[sub['цена'] > 0]
        sub['бренд'] = sub['бренд'].astype(str).str.strip()
        
        if sub.empty:
            file_statuses.append({
                'name': fname, 'size': size, 'status': 'warning',
                'msg': 'Нет данных после очистки'
            })
            continue
        
        sub['источник'] = base_name
        file_statuses.append({
            'name': fname, 'size': size, 'status': 'success',
            'msg': f'✅ {len(sub)} строк'
        })
        all_rows.append(sub)
    
    if not all_rows:
        return None, file_statuses
    
    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined.sort_values('цена')
    
    result = combined.groupby('артикул', as_index=False).agg({
        'цена': 'first',
        'источник': 'first',
        'бренд': 'first'
    })
    
    result = result[['артикул', 'бренд', 'цена', 'источник']]
    result.columns = ['Артикул', 'Бренд', 'Цена', 'Источник']
    result['Цена'] = result['Цена'].round(2)
    result = result.sort_values('Артикул').reset_index(drop=True)
    
    return result, file_statuses
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Результат')
    return buf.getvalue()
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding='utf-8-sig', sep=';').encode('utf-8-sig')
# ============================================================
# ДЕМО-ФАЙЛЫ
# ============================================================
def create_demo_files(tmp_dir: str):
    # Прайс 1
    pd.DataFrame({
        'Артикул': ['IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY', 'XIA-14-256-BLK', 'SONY-WH1000XM5', 'MAC-M2-8-256'],
        'Бренд': ['Apple', 'Apple', 'Samsung', 'Xiaomi', 'Sony', 'Apple'],
        'Цена (руб.)': [78900, 91200, 59900, 48900, 34500, 118000]
    }).to_excel(os.path.join(tmp_dir, 'ОптТорг_Запад.xlsx'), index=False)
    
    # Прайс 2
    pd.DataFrame({
        'Артикул': ['IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY', 'XIA-14-256-BLK', 'SONY-WH1000XM5', 'DYSON-V15-DET', 'ASUS-ROG-ZEPRO'],
        'Бренд': ['Apple Inc.', 'Apple Corporation', 'Samsung Electronics', 'Xiaomi Group', 'Sony Corp', 'Dyson Ltd', 'ASUS ROG'],
        'Цена_закупки': [76500, 88500, 57800, 46900, 32900, 89900, 109900]
    }).to_excel(os.path.join(tmp_dir, 'Маркет-Дистрибьютор.xlsx'), index=False)
    
    # Прайс 3 (CSV)
    pd.DataFrame({
        'Код товара': ['IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY', 'XIA-14-256-BLK', 'SONY-WH1000XM5', 'MAC-M2-8-256', 'GOOGLE-PIXEL8-256'],
        'Производитель': ['Apple Store', 'Apple US', 'Samsung RU', 'Xiaomi CN', 'Sony Japan', 'Apple Store EU', 'Google LLC'],
        'Стоимость_руб': [79000, 92000, 60500, 49200, 34000, 122000, 67900]
    }).to_csv(os.path.join(tmp_dir, 'Премиум-Импорт.csv'), index=False, encoding='utf-8-sig')
    
    # Прайс 4
    pd.DataFrame({
        'Арт.': ['IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY', 'DYSON-V15-DET', 'ASUS-ROG-ZEPRO'],
        'Бренд': ['Apple', 'Apple', 'Samsung', 'Dyson', 'ASUS'],
        'Цена': [81000, 90500, 61000, 87900, 112000]
    }).to_excel(os.path.join(tmp_dir, 'СмартФэн_Опт.xlsx'), index=False)
# ============================================================
# ИНТЕРФЕЙС
# ============================================================
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown("""
    <h1 style="color:#fff;font-size:1.9rem;font-weight:700;margin:0;">
        📊 Прайс-<span style="background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">анализатор</span>
    </h1>
    <p style="color:#7d808a;margin:0.35rem 0 0 0;">Автоматический поиск минимальных цен из прайс-листов</p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 📁 Источник данных")
    
    folder_path = st.text_input(
        "Путь к папке",
        value="",
        placeholder="C:\\Прайсы\\2026 или /home/user/prices",
        label_visibility="collapsed"
    )
    
    folder_valid = False
    if folder_path.strip():
        folder_path = folder_path.strip().strip('"').strip("'")
        if os.path.isdir(folder_path):
            folder_valid = True
            st.success(f"✅ {os.path.basename(folder_path)}")
        else:
            st.error("❌ Папка не найдена")
    
    st.divider()
    
    st.markdown("### 🧪 Демо-данные")
    if st.button("📦 Загрузить демо-папку", use_container_width=True, type="primary"):
        demo_dir = tempfile.mkdtemp(prefix="price_demo_")
        create_demo_files(demo_dir)
        st.session_state['demo_folder'] = demo_dir
        st.session_state['result_df'] = None
        st.rerun()
    
    st.divider()
    
    st.markdown("### 📂 Загрузить файлы")
    uploaded_files = st.file_uploader(
        "xlsx / xls / csv",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if 'result_df' in st.session_state and st.session_state['result_df'] is not None:
        if st.button("🗑 Очистить результат", use_container_width=True):
            st.session_state['result_df'] = None
            st.rerun()
# ========== ОБРАБОТКА ==========
result_df = st.session_state.get('result_df', None)
# Демо-папка
if 'demo_folder' in st.session_state:
    demo_dir = st.session_state['demo_folder']
    if os.path.isdir(demo_dir):
        folder_path = demo_dir
        folder_valid = True
# Автоматическая обработка
if folder_valid and result_df is None:
    with st.spinner("🔍 Анализ прайсов..."):
        out_df, statuses = process_folder(folder_path)
    
    st.session_state['result_df'] = out_df
    st.session_state['file_statuses'] = statuses
    st.rerun()
# Обработка загруженных файлов
if uploaded_files and result_df is None:
    tmp_dir = tempfile.mkdtemp(prefix="upload_")
    for uf in uploaded_files:
        with open(os.path.join(tmp_dir, uf.name), 'wb') as f:
            f.write(uf.getbuffer())
    
    with st.spinner("🔍 Анализ загруженных файлов..."):
        out_df, statuses = process_folder(tmp_dir)
    
    st.session_state['result_df'] = out_df
    st.session_state['file_statuses'] = statuses
    st.rerun()
# ========== ВЫВОД РЕЗУЛЬТАТОВ ==========
if result_df is not None and not result_df.empty:
    statuses = st.session_state.get('file_statuses', [])
    
    # Статусы файлов
    st.markdown("### 📋 Статус обработки файлов")
    cols = st.columns(2)
    for i, fs in enumerate(statuses):
        with cols[i % 2]:
            color = "#10b981" if fs['status'] == 'success' else "#ef4444"
            st.markdown(f"""
                <div class="file-card {'success' if fs['status']=='success' else 'error'}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:600;color:#e4e4e7;">{fs['name']}</div>
                            <div style="color:#7d808a;font-size:0.75rem;">{fs['size']}</div>
                        </div>
                        <div style="color:{color};font-size:0.8rem;font-weight:500;">{fs['msg']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Статистика
    st.markdown("### 🏆 Аналитика")
    
    total = len(result_df)
    min_p = result_df['Цена'].min()
    max_p = result_df['Цена'].max()
    avg_p = result_df['Цена'].mean()
    sources = result_df['Источник'].nunique()
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f'<div class="stat-card"><div style="font-size:1.8rem;font-weight:700;color:#667eea;">{total}</div><div style="color:#7d808a;font-size:0.75rem;">УНИКАЛЬНЫХ АРТИКУЛОВ</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><div style="font-size:1.8rem;font-weight:700;color:#10b981;">{min_p:,.0f} ₽</div><div style="color:#7d808a;font-size:0.75rem;">МИНИМАЛЬНАЯ ЦЕНА</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><div style="font-size:1.8rem;font-weight:700;color:#f87171;">{max_p:,.0f} ₽</div><div style="color:#7d808a;font-size:0.75rem;">МАКСИМАЛЬНАЯ ЦЕНА</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-card"><div style="font-size:1.8rem;font-weight:700;color:#8b5cf6;">{avg_p:,.0f} ₽</div><div style="color:#7d808a;font-size:0.75rem;">СРЕДНЯЯ ЦЕНА</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="stat-card"><div style="font-size:1.8rem;font-weight:700;color:#f59e0b;">{sources}</div><div style="color:#7d808a;font-size:0.75rem;">ИСТОЧНИКОВ</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Таблица
    st.markdown("### 📊 Результаты (Артикул • Бренд • Цена • Источник)")
    st.dataframe(
        result_df,
        use_container_width=True,
        height=450,
        column_config={
            "Цена": st.column_config.NumberColumn("Цена (₽)", format="₽ %,.2f"),
            "Источник": st.column_config.TextColumn("Источник", width="medium")
        }
    )
    
    st.divider()
    
    # Скачивание
    st.markdown("### ⬇️ Скачать результат")
    d1, d2, d3 = st.columns(3)
    
    with d1:
        st.download_button(
            "📗 Скачать Excel (.xlsx)",
            data=to_excel_bytes(result_df),
            file_name=f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with d2:
        st.download_button(
            "📄 Скачать CSV (.csv)",
            data=to_csv_bytes(result_df),
            file_name=f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with d3:
        st.download_button(
            "📋 TSV (для вставки)",
            data=result_df.to_csv(index=False, sep='\t').encode('utf-8'),
            file_name=f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.tsv",
            mime="text/tab-separated-values",
            use_container_width=True
        )
else:
    # Пустое состояние
    st.markdown("""
        <div style="text-align:center;padding:5rem 2rem;">
            <div style="font-size:5rem;margin-bottom:1.5rem;opacity:0.4;">📂</div>
            <h2 style="color:#e4e4e7;font-weight:600;">Загрузите прайс-листы</h2>
            <p style="color:#5a5f6e;max-width:420px;margin:1rem auto 0 auto;">
                Введите путь к папке в боковой панели<br>
                или нажмите кнопку <strong style="color:#a5b4fc;">«Загрузить демо-папку»</strong>
            </p>
        </div>
    """, unsafe_allow_html=True)
