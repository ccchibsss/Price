# -*- coding: utf-8 -*-
"""
МОНОЛИТНОЕ ПРИЛОЖЕНИЕ ПРАЙС-АНАЛИЗАТОР
Стиль Streamlit Premium — темная тема, фирменные градиенты, полная функциональность.
"""
import streamlit as st
import pandas as pd
import os
import glob
import re
import tempfile
from io import BytesIO
from typing import Optional, Tuple
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
# КАСТОМНЫЙ CSS — стильный интерфейс в стиле Streamlit Premium
# ============================================================
st.markdown("""
<style>
  /* ======= Общие сбросы ======= */
  * {
    box-sizing: border-box;
  }
  
  /* Скрываем стандартный header Streamlit, делаем свой */
  .css-1d391kg { padding-top: 0 !important; }
  
  /* Индивидуальный скроллбар */
  ::-webkit-scrollbar {
    width: 7px;
    height: 7px;
  }
  ::-webkit-scrollbar-track {
    background: #0f1117;
  }
  ::-webkit-scrollbar-thumb {
    background: #2d3139;
    border-radius: 4px;
    transition: background 0.2s ease;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #3d4149;
  }
  
  /* Контейнер приложения */
  .app-container {
    background-color: #0f1117;
    min-height: 100vh;
  }
  
  /* Заголовок-баннер */
  .hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #1a1c30 50%, #0f172a 100%);
    border-radius: 18px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.75rem;
    border: 1px solid #1e2230;
    position: relative;
    overflow: hidden;
  }
  .hero-banner::after {
    content: '';
    position: absolute;
    top: -40px;
    right: -80px;
    width: 280px;
    height: 280px;
    background: radial-gradient(circle, rgba(102,126,234,0.15) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-banner::before {
    content: '';
    position: absolute;
    bottom: -60px;
    right: 60px;
    width: 180px;
    height: 180px;
    background: radial-gradient(circle, rgba(118,75,162,0.12) 0%, transparent 70%);
    border-radius: 50%;
  }
  
  .banner-gradient-text {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 60%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  /* Карточки статистики */
  .stat-card {
    background: linear-gradient(180deg, #181b24 0%, #13161e 100%);
    border: 1px solid #2a2d38;
    border-radius: 14px;
    padding: 1.25rem;
    transition: all 0.2s linear;
    position: relative;
    overflow: hidden;
  }
  .stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    opacity: 0;
    transition: opacity 0.25s ease;
  }
  .stat-card:hover::before {
    opacity: 1;
  }
  .stat-card:hover {
    border-color: #3a3d48;
    transform: translateY(-1px);
  }
  
  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  
  .stat-label {
    font-size: 0.8rem;
    color: #7d808a;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  
  /* Карточка — список файлов */
  .file-card {
    background: #181b24;
    border: 1px solid #2a2d38;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.35rem;
    transition: border-color 0.2s ease;
  }
  .file-card.success { border-left: 3px solid #10b981; }
  .file-card.warning { border-left: 3px solid #f59e0b; }
  .file-card.error   { border-left: 3px solid #ef4444; }
  
  /* Кнопки в стиле баннера */
  .btn-gradient {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    cursor: pointer;
    letter-spacing: 0.01em;
  }
  .btn-gradient:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102,126,234,0.35);
  }
  
  /* Ввод пути */
  .path-input {
    background: #13161e;
    border: 1px solid #2a2d38;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #e4e4e7;
    font-size: 0.9rem;
    width: 100%;
    transition: border-color 0.2s ease;
  }
  .path-input:focus {
    border-color: #667eea !important;
    outline: none;
  }
  
  /* Метки статусов */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  /* Таблица */
  .dataframe-wrapper {
    background: #13161e;
    border: 1px solid #2a2d38;
    border-radius: 12px;
    overflow: hidden;
  }
  
  /* Загрузка */
  .spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 0;
    gap: 1rem;
  }
  .spinner {
    width: 42px;
    height: 42px;
    border: 4px solid #1e1e2a;
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  /* Дисклеймеры и тосты */
  .info-card {
    background: #181b24;
    border: 1px solid #2a2d38;
    border-radius: 12px;
    padding: 1.25rem;
  }
  
  .toast {
    padding: 0.85rem 1.25rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }
  
  /* Стилизация загрузки filer */
  .stFileUploader { width: 100%; }
  .stFileUploader > div { border: 2px dashed #2a2d38 !important; border-radius: 14px !important; background: #13161e !important; }
</style>
""", unsafe_allow_html=True)
# ============================================================
# ПОЛЕЗНЫЕ ФУНКЦИИ
# ============================================================
def format_size(size_bytes: int) -> str:
    """Преобразовать байты в человекочитаемый размер."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
def detect_column(df: pd.DataFrame, keywords: list) -> Optional[str]:
    """Найти в DataFrame колонку по ключевым словам (частичное совпадение, игнорирование регистра)."""
    for col in df.columns:
        col_lower = str(col).strip().lower()
        for kw in keywords:
            if kw.lower() in col_lower:
                return col
    return None
def clean_price(val) -> Optional[float]:
    """
    Очистить значение цены от валют, пробелов, разделителей тысяч.
    Вернуть float или None.
    """
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None
    s = str(val).strip().replace('\xa0', '').replace(' ', '')
    if not s:
        return None
    # Удаляем всё кроме цифр, точки, запятой, минуса
    s = re.sub(r'[^\d.,\-]', '', s)
    if not s:
        return None
    try:
        # Определяем разделитель
        if ',' in s and '.' in s:
            # Оба есть — считаем, что точка разделитель тысяч (например 1.250,50)
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            parts = s.split(',')
            if len(parts[-1]) <= 2:
                # Запятая как десятичная: 1250,50 -> 1250.50
                s = s.replace(',', '.')
            else:
                # Запятая как разделитель тысяч: 1,250 -> 1250
                s = s.replace(',', '')
        elif '.' in s and s.count('.') > 1:
            s = s.replace('.', '')
        return float(s)
    except (ValueError, TypeError):
        return None
def read_file(filepath: str) -> Optional[pd.DataFrame]:
    """Прочитать xlsx, xls или csv с попыткой различных кодировок."""
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(filepath)
        # CSV — пробуем несколько кодировок
        for enc in ['utf-8', 'cp1251', 'windows-1251', 'koi8-r', 'iso-8859-1']:
            try:
                df = pd.read_csv(filepath, encoding=enc)
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
        return pd.read_csv(filepath)  # fallback (может выбросить ошибку)
    except Exception:
        return None
# ============================================================
# ОБРАБОТКА ПАПКИ — основа монолитного приложения
# ============================================================
def process_folder(folder_path: str) -> Tuple[Optional[pd.DataFrame], list]:
    """
    Скандалит все xlsx/xls/csv файлы в папке, ищет колонки Артикул/Бренд/Цена,
    объединяет, находит минимум цены по каждому артикулу, добавляет Источник.
    
    Возвращает: (result_df, file_statuses)
    """
    file_statuses = []
    all_rows = []
    # Ищем файлы (рекурсивно до 1 уровня вложенности)
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
        # Чтение
        df = read_file(fpath)
        if df is None or df.empty:
            file_statuses.append({
                'name': fname,
                'size': size,
                'status': 'error',
                'msg': 'Файл пуст или повреждён',
                'art_col': None,
                'brand_col': None,
                'price_col': None,
                'rows': 0
            })
            continue
        # Поиск колонок
        col_art   = detect_column(df, ['артикул', 'арт', 'sku', 'код', 'item', 'товар', 'code', 'номер', 'id', 'артикултовара', 'штрихкод'])
        col_brand = detect_column(df, ['бренд', 'brand', 'производитель', 'произв', 'изготовитель', 'make', 'марка', 'производительтовара'])
        col_price = detect_column(df, ['цена', 'price', 'cost', 'стоимость', 'закуп', 'сумма', 'ценазакупа', 'ррц', 'ценареализации', 'sale'])
        # Если цена не найдена — автоопределение: находим числовой столбец с наибольшей долей цифр
        if col_price is None:
            best_col = None
            best_ratio = 0
            for col in df.columns:
                sample = pd.to_numeric(df[col].head(50), errors='coerce')
                ratio = sample.notna().sum() / min(len(df), 50)
                # Пропускаем колонки, похожие на артикул/бренд (нечисловые)
                if df[col].dtype.kind in 'bifc' or sample.notna().sum() > 5:
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_col = col
            col_price = best_col
        # Проверяем наличие обязательных колонок
        if col_art is None or col_price is None:
            missing = []
            if col_art is None: missing.append('Артикул')
            if col_price is None: missing.append('Цена')
            file_statuses.append({
                'name': fname,
                'size': size,
                'status': 'error',
                'msg': f'Не найдены колонки: {", ".join(missing)}',
                'art_col': col_art,
                'brand_col': col_brand,
                'price_col': col_price,
                'rows': 0
            })
            continue
        # Извлекаем подмножество
        sub = df[[col_art, col_price] + ([col_brand] if col_brand else [])].copy()
        
        # Переименуем для единообразия
        rename_map = {col_art: 'артикул', col_price: 'цена'}
        if col_brand:
            rename_map[col_brand] = 'бренд'
        sub = sub.rename(columns=rename_map)
        if 'бренд' not in sub.columns:
            sub['бренд'] = '—'
        # Очистка
        sub['цена'] = sub['цена'].apply(clean_price)
        sub['артикул'] = sub['артикул'].astype(str).str.strip()
        sub = sub.dropna(subset=['артикул', 'цена'])
        sub = sub[sub['артикул'] != '']
        sub = sub[sub['цена'] > 0]
        sub['бренд'] = sub['бренд'].astype(str).str.strip()
        if sub.empty:
            file_statuses.append({
                'name': fname,
                'size': size,
                'status': 'warning',
                'msg': 'После очистки не осталось данных',
                'art_col': col_art,
                'brand_col': col_brand,
                'price_col': col_price,
                'rows': 0
            })
            continue
        sub['источник'] = base_name
        file_statuses.append({
            'name': fname,
            'size': size,
            'status': 'success',
            'msg': f'✅ {len(sub)} строк | Цена: {col_price} | Арт: {col_art}',
            'art_col': col_art,
            'brand_col': col_brand,
            'price_col': col_price,
            'rows': len(sub)
        })
        all_rows.append(sub)
    if not all_rows:
        return None, file_statuses
    # Объединяем
    combined = pd.concat(all_rows, ignore_index=True)
    # Для каждого артикула берём минимальную цену.
    # Сортируем по цене — при groupby первое значение будет самым дешёвым.
    combined = combined.sort_values('цена')
    result = combined.groupby('артикул', as_index=False).agg({
        'цена': 'first',
        'источник': 'first',
        'бренд': 'first'
    })
    # Оформляем итог
    result = result[['артикул', 'бренд', 'цена', 'источник']]
    result.columns = ['Артикул', 'Бренд', 'Цена', 'Источник']
    result['Цена'] = result['Цена'].round(2)
    result = result.sort_values('Артикул').reset_index(drop=True)
    return result, file_statuses
# ============================================================
# ЭКСПОРТ
# ============================================================
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Результат')
        ws = writer.sheets['Результат']
        # Шрифт и цвет заголовков
        from openpyxl.styles import Font, PatternFill
        header_fill = PatternFill('solid', fgColor='667eea')
        header_font = Font(color='FFFFFF', bold=True)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
        # Автоподбор ширины
        for col_idx, col in enumerate(df.columns, 1):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.column_dimensions[ws.cell(1, col_idx).column_letter].width = min(max_len, 40)
    return buf.getvalue()
def to_csv_string(df: pd.DataFrame) -> str:
    return df.to_csv(index=False, encoding='utf-8-sig', sep=';')
# ============================================================
# ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================
st.markdown('<div class="app-container">', unsafe_allow_html=True)
# ---------- БАННЕР ----------
st.markdown('<div class="hero-banner">', unsafe_allow_html=True)
st.markdown("""
    <div class="d-flex justify-content-between align-items-center" style="position:relative;z-index:1;">
      <div>
        <div style="display:inline-block;background:#667eea22;color:#a5b4fc;
font-size:0.75rem;font-weight:600;padding:0.2rem 0.8rem;border-radius:20px;margin
-:0 0 0.5rem 0;border:1px solid #667eea44;">
          <span style="display:inline-block;margin-right:0.3rem;">⚡</span> Работает локально · Без отправки данных в сеть
        </div>
        <h1 style="color:#fff;font-size:1.9rem;font-weight:700;margin
        :0;letter-spacing:-0.02em;">
          Прайс-<span class="banner-gradient-text">анализатор</span>
        </h1>
        <p style="color:#7d808a;margin:0.35rem 0 0 0;font-size:0.95rem;">
          Автоматическая сборка минимальных цен из прайс-листов поставщиков<br>
          <span style="font-size:0.85rem;color:#5a5f6e;">Все файлы обрабатываются на вашем компьютере</span>
        </p>
      </div>
      <div style="display:flex;gap:0.4rem;flex-shrink:0;">
        <span style="font-size:2rem;filter:grayscale(0.2);">📊</span>
        <span style="font-size:1.6rem;filter:grayscale(0.2);">🔍</span>
        <span style="font-size:1.6rem;filter:grayscale(0.2);">💰</span>
      </div>
    </div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
# ========================================================================
# БОКОВАЯ ПАНЕЛЬ (SIDEBAR)
# ================================================================
with st.sidebar:
    st.markdown('<div style="margin-bottom:0.8rem;">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#a5b4fc;font-size:1rem;font-weight:700;margin:0 0 0.5rem 0;display:flex;align-items:center;gap:0.5rem;">'
                '<span style="font-size:1.2rem;">📁</span> Источник данных</h2>', unsafe_allow_html=True)
    # Ввод пути к папке
    folder_path = st.text_input(
        "Путь к папке с прайсами",
        value="",
        placeholder="C:\\Прайсы\\2026\\ или /home/user/prices/...",
        label_visibility="collapsed",
        key="folder_input"
    )
    folder_valid = False
    if folder_path.strip():
        folder_path = folder_path.strip().strip('"').strip("'")
        if os.path.isdir(folder_path):
            folder_valid = True
            st.success(f"✅ Папка найдена  `" + os.path.basename(folder_path) + "`")
            # Краткая статистика по папке
            try:
                items = os.listdir(folder_path)
                files_in_folder = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
                dirs = [d for d in items if os.path.isdir(os.path.join(folder_path, d))]
                st.caption(f"📊 {len(files_in_folder)} файлов · {len(dirs)} папок")
            except Exception:
                pass
        else:
            st.error("❌ Папка не найдена. Проверьте путь.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    # --- Демо-данные ---
    st.markdown('<h3 style="color:#a5b4fc;font-size:0.85rem;font-weight:600;margin:0 0 0.5rem 0;">🧪 Демо-данные</h3>', unsafe_allow_html=True)
    st.caption("Если нет собственной папки — нажмите кнопку для быстрого теста")
    if st.button("📦 Загрузить демо-папку", use_container_width=True, type="primary"):
        # Создаём временную папку с тестовыми файлами
        demo_dir = tempfile.mkdtemp(prefix="price_demo_")
        demo_files = build_demo_files(demo_dir)
        st.session_state['_demo_dir'] = demo_dir
        st.session_state['_folder_path'] = demo_dir
        st.rerun()
    st.divider()
    # --- Краткая справка ---
    with st.expander("ℹ️  Как это работает", expanded=False):
        st.markdown("""
        **Алгоритм работы приложения:**
        
        1. Сканирует все `.xlsx` / `.xls` / `.csv` файлы в указанной папке
        2. Автоматически находит колонки 
           - **Артикул** (`артикул`, `арт`, `sku`, `код`, `item`...)
           - **Бренд** (`бренд`, `brand`, `производитель`...)
           - **Цена** (`цена`, `price`, `cost`...). 
             Если ценовой столбец не найден по названию — определяется как первая числовая колонка
        3. Объединяет все файлы, очищает цены (убранные пробелы, валюты, разделители тысяч)
        4. Для каждого артикула находит **самую низкую цену**
        5. Добавляет колонку **Источник** (имя файла без расширения)
        6. Результат можно скачать в **Excel** или **CSV**
        
        **Важно:** все данные обрабатываются локально. Никакой отправки в интернет.
        """)
    st.divider()
    # --- Очистка ---
    if 'result_df' in st.session_state and st.session_state['result_df'] is not None:
        st.markdown("")
        if st.button("🗑  Очистить результат", use_container_width=True):
            st.session_state['result_df'] = None
            st.session_state['file_statuses'] = []
            st.rerun()
# ================================================================
# ПОЛЕ ЗАГРУЗКИ ФАЙЛОВ (дополнительный способ)
# ================================================================
with st.sidebar:
    st.markdown('<h3 style="color:#a5b4fc;font-size:0.85rem;font-weight:600;margin:0 0 0.5rem 0;">📂 Загрузить файлы вручную</h3>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Выберите xlsx/xls/csv файлы",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files and not folder_valid:
        # Если файлы загружены вручную и папка не задана — обрабатываем их
        st.info(f"📎 Загручено файлов: {len(uploaded_files)}")
    if uploaded_files and folder_valid:
        st.warning("⚠️ И загрузка файлов, и путь к папке указаны. Будут использованы файлы из папки.")
# ================================================================
# ЛОГИКА — определяем, откуда брать файлы
# ================================================================
result_df = st.session_state.get('result_df', None)
file_statuses = st.session_state.get('file_statuses', [])
# Если папка валидна — проверяем, нужно ли перезапустить анализ
should_process = False
process_source = None
if folder_valid:
    st.session_state_folder_key = '_folder_hash'
    import hashlib
    folder_hash = hashlib.md5(folder_path.encode()).hexdigest()
    last_hash = st.session_state.get(st.session_state_folder_key, None)
    if last_hash != folder_hash:
        should_process = True
        process_source = 'folder'
    # Если результат уже на месте и хеш совпадает — используем
    if result_df is None:
        should_process = True
        process_source = 'folder'
# Загрузка файлов из ручного интерфейса
if uploaded_files and not folder_valid:
    # Проверим, не менялся ли состав файлов
    current_names = sorted([f.name for f in uploaded_files])
    old_names = st.session_state.get('_uploaded_names', [])
    if current_names != old_names:
        should_process = True
        process_source = 'files'
    elif result_df is None:
        should_process = True
        process_source = 'files'
st.session_state['_uploaded_names'] = sorted([f.name for f in uploaded_files]) if uploaded_files else []
# Демо-режим
if '_demo_dir' in st.session_state:
    demo_dir = st.session_state['_demo_dir']
    if os.path.isdir(demo_dir):
        should_process = True
        process_source = 'folder'
        folder_path = demo_dir
        st.session_state['_folder_path'] = demo_dir
# ================================================================
# ВЫПОЛНЕНИЕ АНАЛИЗА
# ================================================================
if should_process:
    with st.spinner("🔍 Сканирование и анализ прайсов..."):
        if process_source == 'folder' and folder_valid:
            out_df, statuses = process_folder(folder_path)
        elif process_source == 'files' and uploaded_files:
            # Временный каталог для загруженных файлов
            tmp_dir = tempfile.mkdtemp(prefix="streamlit_prices_")
            saved_paths = []
            for uf in uploaded_files:
                save_path = os.path.join(tmp_dir, uf.name)
                with open(save_path, 'wb') as f:
                    f.write(uf.getbuffer())
                saved_paths.append(save_path)
            out_df, statuses = process_folder(tmp_dir)
            # Сохраняем временную папку для повторного использования
            st.session_state['_tmp_files_dir'] = tmp_dir
        else:
            out_df, statuses = None, []
    st.session_state['result_df'] = out_df
    st.session_state['file_statuses'] = statuses
    st.session_state['_process_time'] = datetime.now().strftime("%H:%M:%S")
    
    if process_source == 'folder':
        st.session_state['_folder_hash'] = hashlib.md5(folder_path.encode()).hexdigest()
    st.rerun()
# ================================================================
# ВЫВОД РЕЗУЛЬТАТОВ
# ================================================================
if result_df is not None and not result_df.empty:
    statuses = file_statuses
    # ---------- СТАТУСЫ ФАЙЛОВ ----------
    st.markdown("""
        <div style="margin-bottom:1.25rem;">
            <h3 style="color:#a5b4fc;font-size:1rem;font-weight:600;margin:0 0 0.75rem 0;display:flex;align-items:center;gap:0.5rem;">
                <span>📋</span> Статус обработки файлов
            </h3>
        </div>
    """, unsafe_allow_html=True)
    success_files = [s for s in statuses if s['status'] == 'success']
    error_files   = [s for s in statuses if s['status'] == 'error']
    warning_files = [s for s in statuses if s['status'] == 'warning']
    col_success, col_error = st.columns(2)
    
    with col_success:
        if success_files:
            for fs in success_files:
                st.markdown(f"""
                    <div class="file-card success">
                        <div style="display:flex;flex-direction:column;flex:1;">
                            <span style="font-weight:600;color:#e4e4e7;font-size:0.9rem;">{fs['name']}</span>
                            <span style="color:#7d808a;font-size:0.75rem;margin-top:0.1rem;">{fs['size']}</span>
                        </div>
                        <span style="color:#10b981;font-size:0.8rem;font-weight:500;white-space:nowrap;">{fs['msg']}</span>
                    </div>
                """, unsafe_allow_html=True)
    with col_error:
        if error_files or warning_files:
            for fs in error_files + warning_files:
                color = '#ef4444' if fs['status'] == 'error' else '#f59e0b'
                icon  = '⚠️' if fs['status'] == 'warning' else '❌'
                st.markdown(f"""
                    <div class="file-card {'warning' if fs['status']=='warning' else 'error'}">
                        <div style="display:flex;flex-direction:column;flex:1;">
                            <span style="font-weight:600;color:#e4e4e7;font-size:0.9rem;">{fs['name']}</span>
                            <span style="color:#7d808a;font-size:0.75rem;margin-top:0.1rem;">{fs['size']}</span>
                        </div>
                        <span style="color:{color};font-size:0.8rem;font-weight:500;white-space:nowrap;">{icon} {fs['msg']}</span>
                    </div>
                """, unsafe_allow_html=True)
    if not statuses:
        st.caption("Файлы не найдены в указанной папке.")
    st.divider()
    # ---------- СТАТИСТИКА ----------
    total_art = len(result_df)
    min_price = result_df['Цена'].min()
    max_price = result_df['Цена'].max()
    avg_price = result_df['Цена'].mean()
    unique_sources = result_df['Источник'].nunique()
    
    # Подсчёт экономии (разница между средней и минимальной для нескольких источников на один артикул)
    art_source_counts = result_df.groupby('Артикул')['Источник'].nunique()
    competing_arts = (art_source_counts > 1).sum()
    st.markdown("""
        <div style="margin-bottom:1.25rem;">
            <h3 style="color:#a5b4fc;font-size:1rem;font-weight:600;margin:0 0 0.75rem 0;display:flex;align-items:center;gap:0.5rem;">
                <span>🏆</span> Аналитика
            </h3>
        </div>
    """, unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    stat_cards = [
        (f"{total_art:,}", "Уникальных артикулов\nс найденной ценой", "#667eea"),
        (f"{min_price:,.2f} ₽", "Самая низкая цена\nсреди всех прайсов", "#10b981"),
        (f"{max_price:,.2f} ₽", "Самая высокая цена\n(для анализа разброса)", "#f87171"),
        (f"{avg_price:,.2f} ₽", "Средняя цена\nпо найденным предложениям", "#8b5cf6"),
        (f"{unique_sources}", "Уникальных источников\n(файлов-поставщиков)", "#f59e0b"),
    ]
    for col, (val, label, accent) in zip([s1, s2, s3, s4, s5], stat_cards):
        col.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color:{accent};">{val}</div>
                <div class="stat-label" style="color:#7d808a;margin-top:0.35rem;">{label}</div>
            </div>
        """, unsafe_allow_html=True)
    if competing_arts > 0:
        st.caption(f"💡 {competing_arts} артикулов найдены в нескольких прайс-листах — выбраны самые дешёвые предложения.")
    st.divider()
    # ---------- ТАБЛИЦА РЕЗУЛЬТАТОВ ----------
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <h3 style="color:#a5b4fc;font-size:1rem;font-weight:600;margin:0 0 0.5rem 0;display:flex;align-items:center;gap:0.5rem;">
                <span>📊</span> Таблица результатов
                <span style="font-weight:400;font-size:0.8rem;color:#5a5f6e;margin-left:auto;">{0} из {1} записей</span>
            </h3>
        </div>
    """.format(0, len(result_df)), unsafe_allow_html=True)
    # Стилизованная таблица
    table_html = """
    <div class="dataframe-wrapper">
        <table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
            <thead>
                <tr style="background:#1e2230;border-bottom:2px solid #2d3139;">
                    <th style="padding:0.85rem 1rem;text-align:left;color:#a5b4fc;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">#</th>
                    <th style="padding:0.85rem 1rem;text-align:left;color:#a5b4fc;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Артикул</th>
                    <th style="padding:0.85rem 1rem;text-align:left;color:#a5b4fc;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Бренд</th>
                    <th style="padding:0.85rem 1rem;text-align:right;color:#10b981;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Цена (₽)</th>
                    <th style="padding:0.85rem 1rem;text-align:left;color:#a5b4fc;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;">Источник (поставщик)</th>
                </tr>
    """
    rows_to_show = min(len(result_df), 50)
    for idx, row in result_df.head(rows_to_show).iterrows():
        table_html += f"""
            <tr style="border-bottom:1px solid #1e2230;transition:background 0.15s ease;" onmouseover="this.style.background='#1a1d28'" onmouseout="this.style.background='transparent'">
                <td style="padding:0.65rem 1rem;color:#5a5f6e;font-size:0.75rem;">{idx+1}</td>
                <td style="padding:0.65rem 1rem;color:#e4e4e7;font-weight:500;font-family:monospace;font-size:0.85rem;">{row['Артикул']}</td>
                <td style="padding:0.65rem 1rem;color:#d4d4d8;">{row['Бренд']}</td>
                <td style="padding:0.65rem 1rem;text-align:right;font-weight:700;color:#10b981;font-size:0.95rem;">{row['Цена']:,.2f}</td>
                <td style="padding:0.65rem 1rem;color:#a5b4fc;font-size:0.82rem;display:flex;align-items:center;gap:0.5rem;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#667eea;display:inline-block;"></span>
                    <span style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{row['Источник']}">{row['Источник']}</span>
                </td>
            </tr>
        """
    table_html += "</tbody></table></div>"
    if len(result_df) > 50:
        table_html += f"""
            <div style="text-align:center;padding:0.75rem;color:#7d808a;font-size:0.8rem;background:#13161e;border-top:1px solid #1e2230;border-radius:0 0 12px 12px;">
                📦 Показано первых 50 записей из {len(result_df)}. Для полного результата скачайте Excel-файл.
            </div>
        """
    st.markdown(table_html, unsafe_allow_html=True)
    st.divider()
    # ---------- ЭКСПОРТ ----------
    st.markdown("""
        <div style="margin-bottom:0.75rem;">
            <h3 style="color:#a5b4fc;font-size:1rem;font-weight:600;margin:0 0 0.75rem 0;display:flex;align-items:center;gap:0.5rem;">
                <span>⬇️</span> Скачать результат
            </h3>
        </div>
    """, unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    # Excel
    with e1:
        excel_bytes = to_excel_bytes(result_df)
        st.download_button(
            label="📗  Скачать Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    # CSV
    with e2:
        csv_str = to_csv_string(result_df)
        st.download_button(
            label="📄  Скачать CSV (.csv)",
            data=csv_str.encode('utf-8-sig'),
            file_name=f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv;charset=utf-8-sig",
            use_container_width=True,
            type="primary"
        )
    # TSV (для быстрой вставки в Excel)
    with e3:
        tsv_str = result_df.to_csv(index=False, sep='\t', encoding='utf-8')
        st.download_button(
            label="📋  TSV для вставки",
            data=tsv_str.encode('utf-8'),
            file_name=f"price_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv",
            mime="text/tab-separated-values",
            use_container_width=True,
            type="secondary"
        )
    st.divider()
    # ---------- ПОДСКАЗКИ ----------
    with st.expander("💡  Советы и вопросы"):
        st.markdown("""
        **Формат файлов:**
        - Поддерживаются `.xlsx`, `.xls`, `.csv`
        - CSV-файлы автоматически определяют кодировку (UTF-8, Windows-1251, KOI8-R)
        - Цена очищается от валютных символов, пробелов, тысячных разделителей
        
        **Названия столбцов:**
        - **Артикул** определяется по ключевым словам: *артикул, арт, sku, код, item, товар, number, id*
        - **Бренд** определяется по: *бренд, brand, производитель, производитель, материал*
        - **Цена** определяется по: *цена, price, cost, стоимость, закуп, сумма, ррц, price*. 
          Если нет явной цены — выбирается первая числовая колонка
        
        **Примеры названий столбцов, которые сработают:**
        - `Артикул товара`, `ART`, `SKU`, `Код товара`
        - `Бренд`, `Производитель`, `Brand`, `Производитель товара`
        - `Цена`, `Price`, `Цена закупа`, `Стоимость`, `Цена (руб.)`, `Cost`
        """)
else:
    # ---------- СТРАНИЦА ОЖИДАНИЯ / ПУСТАЯ ----------
    st.markdown("""
        <div style="text-align:center;padding:4rem 1rem;">
            <div style="font-size:4rem;margin-bottom:1rem;opacity:0.6;">📂</div>
            <h2 style="color:#e4e4e7;font-weight:600;font-size:1.4rem;margin:0 0 0.5rem 0;">
                Загрузите прайс-листы для анализа
            </h2>
            <p style="color:#5a5f6e;max-width:500px;margin:0 auto;font-size:0.9rem;line-height:1.6;">
                Введите путь к папке с файлами прайсов в боковой панели,<br>
                нажмите <strong style="color:#a5b4fc;">«Загрузить демо-папку»</strong> для быстрого теста,<br>
                или загрузите файлы вручную через меню в сайдбаре.
            </p>
        </div>
    """, unsafe_allow_html=True)
    # Информационная карточка
    st.info("""
    **Что делает приложение:**
    
    - Сканирует все Excel (`.xlsx`/`.xls`) и CSV файлы в папке
    - Автоматически находит колонки **Артикул**, **Бренд**, **Цена**
    - Для каждого артикула ищет **минимальную цену** по всем прайсам
    - Добавляет колонку **Источник** — имя файла-поставщика
    - Позволяет скачать итоговый отчёт в **Excel** или **CSV**
    
    ⚡  Все обработки происходят на вашем компьютере. Данные не покидают его.
    """)
st.markdown('</div>', unsafe_allow_html=True)
# ================================================================
# СТРОИТЕЛЬ ДЕМО-ФАЙЛОВ
# ================================================================
def build_demo_files(tmp_dir: str) -> list:
    """Создаёт несколько тестовых прайс-листов в папке tmp_dir."""
    # Прайс 1: «ОптТорг-Запад»
    df1 = pd.DataFrame({
        'Артикул': [
            'IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY',
            'XIA-14-256-BLK', 'SONY-WH1000XM5', 'MAC-M2-8-256'
        ],
        'Бренд': [
            'Apple', 'Apple', 'Samsung',
            'Xiaomi', 'Sony', 'Apple'
        ],
        'Цена (руб.)': [
            78900, 91200, 59900,
            48900, 34500, 118000
        ]
    })
    df1.to_excel(os.path.join(tmp_dir, 'ОптТорг_Запад.xlsx'), index=False)
    # Прайс 2: «Маркет-Дистрибьютор» — у Андрея цены лучше на некоторых
    df2 = pd.DataFrame({
        'Артикул': [
            'IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY',
            'XIA-14-256-BLK', 'SONY-WH1000XM5', 'DYSON-V15-DET',
            'ASUS-ROG-ZEPRO'
        ],
        'Бренд': [
            'Apple Inc.', 'Apple Corporation', 'Samsung Electronics',
            'Xiaomi Group', 'Sony Corp', 'Dyson Ltd',
            'ASUS ROG'
        ],
        'Цена_закупки': [
            76500,  88500, 57800,   # дешевле
            46900,  32900, 89900,   # дешевле
            109900                          # уникальный
        ]
    })
    df2.to_excel(os.path.join(tmp_dir, 'Маркет-Дистрибьютор.xlsx'), index=False)
    # Прайс 3: «Премиум-Импорт» (CSV)
    df3 = pd.DataFrame({
        'Код товара': [
            'IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY',
            'XIA-14-256-BLK', 'SONY-WH1000XM5', 'MAC-M2-8-256',
            'GOOGLE-PIXEL8-256'
        ],
        'Производитель': [
            'Apple Store', 'Apple US', 'Samsung RU',
            'Xiaomi CN', 'Sony Japan', 'Apple Store EU',
            'Google LLC'
        ],
        'Стоимость_руб': [
            79000,  92000, 60500,
            49200,  34000, 122000,
            67900
        ]
    })
    df3.to_csv(os.path.join(tmp_dir, 'Премиум-Импорт.csv'), index=False, encoding='utf-8-sig')
    # Прайс 4: «СмартФэн» (xls старый формат, через xlsx сохраняем)
    df4 = pd.DataFrame({
        'Арт.': [
            'IP15-128-GLA', 'IP15-256-BLK', 'SAM-A54-128-GRY',
            'DYSON-V15-DET', 'ASUS-ROG-ZEPRO'
        ],
        'Бренд': [
            'Apple', 'Apple', 'Samsung',
            'Dyson', 'ASUS'
        ],
        'Цена': [
            81000, 90500, 61000,
            87900, 112000
        ]
    })
    df4.to_excel(os.path.join(tmp_dir, 'СмартФэн_Опт.xlsm' if False else 'СмартФэн_Опт.xlsx'), index=False)
    return [f for f in os.listdir(tmp_dir) if os.path.isfile(os.path.join(tmp_dir, f))]
