import streamlit as st
import pandas as pd
import os
import glob
from pathlib import Path
from typing import Optional, Tuple
import re
from io import BytesIO

# ======================= PAGE CONFIG =======================
st.set_page_config(
    page_title="Прайс-анализатор",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a Bug": None,
        "About": "📊 Прайс-анализатор — поиск самого выгодного предложения"
    }
)

# ======================= STYLES =======================
st.markdown("""
<style>
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #2a2d35;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3a3d45;
    }
    
    /* Main container */
    .main {
        background: #0e1117;
    }
    
    /* Header gradient */
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
    }
    
    /* Cards */
    .card {
        background: #1a1d24;
        border: 1px solid #2a2d35;
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.2s ease;
    }
    .card:hover {
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1d24 0%, #16191f 100%);
        border: 1px solid #2a2d35;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b8fa3;
        margin-top: 0.25rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* File item */
    .file-item {
        background: #1a1d24;
        border: 1px solid #2a2d35;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .file-icon {
        font-size: 1.5rem;
    }
    .file-name {
        flex: 1;
        color: #e4e4e7;
        font-weight: 500;
    }
    .file-size {
        color: #6b7280;
        font-size: 0.85rem;
    }
    
    /* Success badge */
    .success-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #6b7280;
    }
    .empty-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* Dataframe custom */
    .dataframe {
        background: #1a1d24;
        border-radius: 8px;
    }
    .dataframe th {
        background: #2a2d35;
        color: #e4e4e7;
    }
    .dataframe td {
        color: #d4d4d8;
    }
</style>
""", unsafe_allow_html=True)

# ======================= HELPERS =======================

def format_size(size_bytes: int) -> str:
    """Format file size to human readable."""
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def detect_column(df: pd.DataFrame, keywords: list[str]) -> Optional[str]:
    """Detect column by keywords in name."""
    for col in df.columns:
        col_lower = str(col).strip().lower()
        for kw in keywords:
            if kw.lower() in col_lower:
                return col
    return None


def clean_price_string(val) -> Optional[float]:
    """Clean price string to float. Исправлено: корректная обработка RU и US форматов."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    
    s = str(val).strip().replace(' ', '').replace('\xa0', '')
    if not s:
        return None
    
    # Оставляем только цифры, точки, запятые и минус
    s = re.sub(r'[^\d.,\-]', '', s)
    
    try:
        if ',' in s and '.' in s:
            # Определяем, какой символ идет последним (он является десятичным разделителем)
            if s.rfind(',') > s.rfind('.'):
                # Формат RU: 1.234,56 -> 1234.56
                s = s.replace('.', '').replace(',', '.')
            else:
                # Формат US: 1,234.56 -> 1234.56
                s = s.replace(',', '')
        elif ',' in s:
            # Только запятая. Проверяем, является ли она десятичной
            parts = s.split(',')
            if len(parts[-1]) <= 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        return float(s)
    except Exception:
        return None


def read_file_safe(filepath: str) -> Optional[pd.DataFrame]:
    """Try to read a file (xlsx, csv, xls). Исправлено: замена голого except на Exception."""
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(filepath)
        else:
            # Try different encodings
            for enc in ['utf-8', 'cp1251', 'windows-1251', 'koi8-r']:
                try:
                    return pd.read_csv(filepath, encoding=enc)
                except Exception:
                    continue
            return pd.read_csv(filepath)  # last attempt
    except Exception:
        return None


def process_folder(folder_path: str) -> Tuple[Optional[pd.DataFrame], list[dict]]:
    """
    Scan folder, find Артикул, Бренд, Цена columns,
    return best (cheapest) price per article with source.
    """
    files_data = []
    all_rows = []

    # Исправлено: более надежный поиск через pathlib
    path = Path(folder_path)
    files = [str(p) for p in path.rglob('*') if p.suffix.lower() in ['.xlsx', '.xls', '.csv']]
    files = list(set(files))

    if not files:
        return None, []

    for fpath in sorted(files):
        fname = os.path.basename(fpath)
        size = os.path.getsize(fpath)
        
        df = read_file_safe(fpath)
        if df is None or df.empty:
            files_data.append({
                'name': fname,
                'size': format_size(size),
                'status': '❌ Не удалось прочитать',
                'error': True
            })
            continue

        # Detect columns
        col_art = detect_column(df, ['артикул', 'арт', 'sku', 'код', 'item', 'товар'])
        col_brand = detect_column(df, ['бренд', 'brand', 'производитель', 'произв'])
        col_price = detect_column(df, ['цена', 'price', 'cost', 'стоимость', 'закуп'])

        # If price not found by keywords, try to auto-detect numeric column near article
        if col_price is None:
            for col in df.columns:
                sample = df[col].dropna().head(20)
                if len(sample) > 0:
                    numeric_count = sum(pd.to_numeric(sample, errors='coerce').notna())
                    if numeric_count > len(sample) * 0.5:
                        col_price = col
                        break

        if not col_art:
            files_data.append({
                'name': fname,
                'size': format_size(size),
                'status': '❌ Столбец "Артикул" не найден',
                'error': True
            })
            continue
        
        if not col_price:
            files_data.append({
                'name': fname,
                'size': format_size(size),
                'status': '❌ Столбец "Цена" не найден',
                'error': True
            })
            continue

        # Build clean dataframe
        source_name = os.path.splitext(fname)[0]
        
        cols_to_keep = [col_art, col_price] + ([col_brand] if col_brand else [])
        sub = df[cols_to_keep].copy()
        sub.columns = ['артикул', 'цена', 'бренд'] if col_brand else ['артикул', 'цена']
        sub['цена'] = sub['цена'].apply(clean_price_string)
        sub = sub.dropna(subset=['артикул', 'цена'])
        sub['артикул'] = sub['артикул'].astype(str).str.strip()
        sub = sub[sub['артикул'] != '']
        sub['источник'] = source_name
        sub = sub[sub['цена'] > 0]

        if sub.empty:
            files_data.append({
                'name': fname,
                'size': format_size(size),
                'status': '⚠️ Нет данных после очистки',
                'error': True
            })
            continue

        files_data.append({
            'name': fname,
            'size': format_size(size),
            'status': f'✅ {len(sub)} строк | Цена: {col_price}',
            'error': False
        })
        all_rows.append(sub)

    if not all_rows:
        return None, files_data

    combined = pd.concat(all_rows, ignore_index=True)

    # Get cheapest price per article, keep first brand encountered
    # Sort by price ascending so first brand per article is from cheapest file
    combined = combined.sort_values('цена')
    
    result = combined.groupby('артикул', as_index=False).agg({
        'цена': 'first',
        'источник': 'first',
        'бренд': 'first'
    })

    # Reorder columns: Артикул, Бренд, Цена, Источник
    result = result[['артикул', 'бренд', 'цена', 'источник']]
    result.columns = ['Артикул', 'Бренд', 'Цена', 'Источник']
    
    # Format price as number
    result['Цена'] = result['Цена'].round(2)
    
    # Sort by article
    result = result.sort_values('Артикул').reset_index(drop=True)

    return result, files_data


def download_file(df: pd.DataFrame, fmt: str) -> bytes:
    """Prepare file for download."""
    if fmt == 'csv':
        return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    else:
        buf = BytesIO()
        df.to_excel(buf, index=False)
        return buf.getvalue()


# ======================= MAIN APP =======================

st.markdown('<div class="header-gradient">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">📊 Прайс-анализатор</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 0.25rem 0 0 0; font-size: 0.95rem;">
            Автоматический поиск самого выгодного предложения по Артикулу
        </p>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 📁 Источник данных")
    folder = st.text_input(
        "Путь к папке",
        placeholder="Например: /путь/к/прайсам или C:\\прайсы",
        help="Укажите папку, содержащую файлы прайсов (xlsx, xls, csv)"
    )
    
    if folder:
        folder = folder.strip().strip('"')
    
    folder_valid = False
    if folder and os.path.isdir(folder):
        folder_valid = True
        st.success(f"✅ Папка найдена: **{os.path.basename(folder)}**")
        
        # Show folder contents preview
        try:
            item_count = len(os.listdir(folder))
            st.info(f"📦 В папке: {item_count} элементов")
        except Exception:
            pass
    elif folder:
        st.error("❌ Папка не найдена. Проверьте путь.")

    st.divider()
    
    st.markdown("### ⚙️ Настройки")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sample_rows = st.slider("Предпросмотр строк", 5, 50, 10)
    with col_s2:
        price_decimals = st.slider("Десятичных знаков цены", 0, 4, 2)
    
    st.divider()
    
    st.markdown("### ℹ️ Как это работает")
    st.markdown("""
    1. Приложение сканирует все **xlsx / xls / csv** файлы в папке
    2. Автоматически ищет столбцы: **Артикул**, **Бренд**, **Цена**
    3. Для каждого артикула находит **минимальную цену**
    4. Добавляет столбец **Источник** — имя файла-поставщика
    5. Результат можно скачать в **CSV** или **Excel**
    """)

# ==================== MAIN CONTENT ====================
if not folder:
    # Empty state - folder not selected
    st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📂</div>
            <h3 style="color: #d4d4d8; margin-bottom: 0.5rem;">Выберите папку с прайсами</h3>
            <p style="color: #6b7280; font-size: 0.95rem;">
                Введите путь к папке в боковой панели, чтобы начать анализ
            </p>
        </div>
    """, unsafe_allow_html=True)

elif not folder_valid:
    st.markdown("""
        <div class="card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
            <h3 style="color: #f87171; margin-bottom: 0.5rem;">Папка не найдена</h3>
            <p style="color: #6b7280;">Проверьте правильность пути и права доступа.</p>
        </div>
    """, unsafe_allow_html=True)

else:
    # Process button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 3, 1])
    with col_btn2:
        analyze_clicked = st.button(
            "🚀 Запустить анализ",
            type="primary",
            use_container_width=True,
            help="Просканировать все файлы и найти минимальные цены"
        )

    if analyze_clicked:
        with st.spinner("🔍 Сканирование файлов..."):
            result_df, file_info = process_folder(folder)

        if result_df is None or result_df.empty:
            st.markdown("""
                <div class="card" style="text-align: center; padding: 2rem;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">😕</div>
                    <h3 style="color: #fbbf24; margin-bottom: 0.5rem;">Не удалось обработать файлы</h3>
                    <p style="color: #6b7280;">Убедитесь, что файлы содержат столбцы с артикулами и ценами.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Show file processing summary
            st.markdown("### 📋 Статус обработки файлов")
            
            # Separate success and errors
            success_files = [f for f in file_info if not f.get('error')]
            error_files = [f for f in file_info if f.get('error')]
            
            if success_files:
                st.markdown("#### ✅ Обработано успешно")
                for fi in success_files:
                    st.markdown(f"""
                        <div class="file-item">
                            <span class="file-icon">📄</span>
                            <span class="file-name">{fi['name']}</span>
                            <span class="file-size">{fi['size']}</span>
                        </div>
                    """, unsafe_allow_html=True)
            
            if error_files:
                st.markdown("#### ❌ Ошибки")
                for fi in error_files:
                    st.markdown(f"""
                        <div class="file-item">
                            <span class="file-icon">⚠️</span>
                            <span class="file-name">{fi['name']}</span>
                            <span class="file-size">{fi['size']}</span>
                            <span style="color: #f87171; font-size: 0.85rem;">{fi['status']}</span>
                        </div>
                    """, unsafe_allow_html=True)

            st.divider()

            # Results
            st.markdown("### 🏆 Результаты анализа")
            
            total_articles = len(result_df)
            min_price = result_df['Цена'].min()
            max_price = result_df['Цена'].max()
            avg_price = result_df['Цена'].mean()
            unique_sources = result_df['Источник'].nunique()

            # Metric cards
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{total_articles:,}</div>
                        <div class="metric-label">Уникальных артикулов</div>
                    </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #10b981;">{min_price:,.{price_decimals}f} ₽</div>
                        <div class="metric-label">Самая низкая цена</div>
                    </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #f87171;">{max_price:,.{price_decimals}f} ₽</div>
                        <div class="metric-label">Самая высокая цена</div>
                    </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{unique_sources}</div>
                        <div class="metric-label">Источников (файлов)</div>
                    </div>
                """, unsafe_allow_html=True)

            st.divider()

            # Data preview
            st.markdown("#### 📊 Просмотр данных")
            st.dataframe(
                result_df.head(sample_rows),
                use_container_width=True,
                height=min(400, sample_rows * 35),
                column_config={
                    "Артикул": st.column_config.TextColumn("Артикул", width="120px"),
                    "Бренд": st.column_config.TextColumn("Бренд", width="140px"),
                    "Цена": st.column_config.NumberColumn("Цена (₽)", format=f"%.{price_decimals}f ₽"),
                    "Источник": st.column_config.TextColumn("Источник (файл)", width="180px"),
                }
            )

            st.caption(f"Показано {min(sample_rows, len(result_df))} из {len(result_df)} строк")

            # Download section
            st.divider()
            st.markdown("### ⬇️ Скачать результат")
            
            dl1, dl2, dl3 = st.columns(3)
            
            csv_data = download_file(result_df, 'csv')
            xlsx_data = download_file(result_df, 'excel')
            tsv_data = result_df.to_csv(index=False, sep='\t', encoding='utf-8-sig')
            
            with dl1:
                st.download_button(
                    label="📄 Скачать CSV",
                    data=csv_data,
                    file_name="analysis_result.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with dl2:
                st.download_button(
                    label="📗 Скачать Excel",
                    data=xlsx_data,
                    file_name="analysis_result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with dl3:
                # Исправлено: удалена ложь про "копирование в буфер". Теперь честно указано скачивание TSV.
                st.download_button(
                    label="📥 Скачать TSV",
                    data=tsv_data,
                    file_name="analysis_result.tsv",
                    mime="text/tab-separated-values",
                    use_container_width=True,
                    help="Скачать в формате TSV для удобной вставки в Excel"
                )

            # Tips
            st.divider()
            st.markdown("""
            <details>
            <summary style="color: #8b8fa3; cursor: pointer;">💡 Советы по использованию</summary>
            <div style="margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem; line-height: 1.6;">
                <ul>
                    <li>Файлы должны содержать столбцы с названиями, содержащими <b>Артикул</b>, <b>Цена</b> (и опционально <b>Бренд</b>)</li>
                    <li>Поддерживаются форматы: <b>.xlsx</b>, <b>.xls</b>, <b>.csv</b></li>
                    <li>Для CSV файлов приложение автоматически определяет кодировку (UTF-8, Windows-1251, KOI8-R)</li>
                    <li>Цена должна быть числовым значением — приложение автоматически очищает пробелы и валютные знаки</li>
                    <li>Если у одного артикула несколько цен, выбирается <b>минимальная</b></li>
                </ul>
            </div>
            </details>
            """, unsafe_allow_html=True)
