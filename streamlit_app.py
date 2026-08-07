# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║        PRICE.FUSION — МОНОЛИТНОЕ СТРИМЛИТ ПРИЛОЖЕНИЕ (ВСЁ В 1 ФАЙЛЕ)         ║
# ║   Авто-поиск: Артикул | Бренд | Цена → Мин. цена + Источник + Экспорт        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
import pandas as pd
import numpy as np
import io
import re
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 0. КОНФИГУРАЦИЯ СТРАНИЦЫ (СТРОГО ПЕРВАЯ СТРИМЛИТ КОМАНДА)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Price.Fusion — Агрегатор прайсов",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. СТИЛИЗАЦИЯ (ПРЕМИУМ ТЁМНЫЙ UI С ГРАДИЕНТАМИ И СТЕКЛОМ)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Общий фон и шрифт ── */
    .stApp {
        background: #070709;
        color: #f4f4f5;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Сайдбар ── */
    [data-testid="stSidebar"] {
        background: #0e0e12 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    [data-testid="stSidebar"] * {
        color: #d4d4d8 !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; }

    /* ── Кнопки управления ── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.5);
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    }

    /* ── Кнопки скачивания ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #0d9488 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        font-size: 0.85rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
        width: 100%;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.5);
    }

    /* ── Загрузчик файлов ── */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1.5px dashed rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 1.2rem;
        transition: all 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(139, 92, 246, 0.5);
        background: rgba(139, 92, 246, 0.03);
    }
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
    }

    /* ── Метрики ── */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #71717a !important;
    }

    /* ── Карточки файлов ── */
    .card {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(10px);
        transition: border-color 0.2s;
    }
    .card:hover { border-color: rgba(255, 255, 255, 0.15); }
    .card-ok   { border-left: 3px solid #10b981; }
    .card-warn { border-left: 3px solid #f59e0b; }
    .card-err  { border-left: 3px solid #ef4444; }

    /* ── Бейджи ── */
    .badge {
        display: inline-block;
        padding: 0.2em 0.7em;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.06em;
    }
    .badge-green  { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-red    { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-yellow { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-blue   { background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); }

    /* ── Заголовки и текст ── */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 30%, #a78bfa 70%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.15;
        letter-spacing: -0.03em;
    }
    .hero-sub {
        color: #a1a1aa;
        font-size: 1rem;
        margin-top: 0.5rem;
        line-height: 1.6;
        max-width: 680px;
    }
    .section-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: #71717a;
        margin-bottom: 0.8rem;
    }

    /* ── Шаги / Онбординг ── */
    .step-box {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: left;
        backdrop-filter: blur(10px);
        transition: all 0.2s;
    }
    .step-box:hover {
        border-color: rgba(139, 92, 246, 0.3);
        transform: translateY(-2px);
    }
    .step-num {
        width: 42px; height: 42px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(79, 70, 229, 0.2));
        border: 1px solid rgba(139, 92, 246, 0.4);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
        font-weight: 800;
        color: #c4b5fd;
        margin-bottom: 0.9rem;
    }

    /* ── Инпуты, селекты, текстовые поля и выпадающие списки (Тёмный фон + белые буквы) ── */
    input, select, .stSelectbox > div > div, .stTextInput > div > div > input, [data-testid="stTextInputRootElement"] input {
        background: #121217 !important;
        background-color: #121217 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
    }
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    [data-testid="stTextInputRootElement"]:focus-within {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Заголовки, лейблы и плейсхолдеры внутри инпутов */
    input::placeholder, .stTextInput input::placeholder, [data-testid="stTextInputRootElement"] input::placeholder {
        color: #a1a1aa !important;
        opacity: 0.85 !important;
    }
    
    /* Стилизация выпадающих селекторов в Streamlit */
    div[data-baseweb="select"] > div {
        background-color: #121217 !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    
    /* ── Стилизация File Uploader (Полностью тёмная тема + белые/светлые буквы) ── */
    [data-testid="stFileUploader"] {
        background-color: #121217 !important;
        background: #121217 !important;
        border: 2px dashed rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
    }
    [data-testid="stFileUploader"] *, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] p, 
    [data-testid="stFileUploader"] label {
        color: #f4f4f5 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #1f1f2e !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: background 0.2s !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #2e2e3f !important;
        border-color: #8b5cf6 !important;
    }
    
    /* Подсветка подсказки скрепки и названия файлов в тёмной теме */
    [data-testid="stFileUploader"] svg {
        fill: #a78bfa !important;
        color: #a78bfa !important;
    }

    /* ── Табы ── */
    [data-testid="stTabs"] > div:first-child {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #71717a !important;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.7rem 1.4rem !important;
        border-radius: 10px 10px 0 0 !important;
        transition: all 0.2s;
    }
    button[data-baseweb="tab"]:hover {
        color: #c4b5fd !important;
        background: rgba(255, 255, 255, 0.02) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #c4b5fd !important;
        border-bottom: 2px solid #8b5cf6 !important;
        background: rgba(139, 92, 246, 0.08) !important;
    }

    hr { border: none; border-top: 1px solid rgba(255, 255, 255, 0.06); margin: 1.5rem 0; }
    
    /* ── Скроллбар ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #070709; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.12); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(139, 92, 246, 0.5); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. СИНОНИМЫ И КЛЮЧЕВЫЕ СЛОВА (ДЕТЕКТОР КОЛОНОК)
# ─────────────────────────────────────────────────────────────────────────────
ARTICLE_KW = ["артикул", "арт", "sku", "код", "кодтовара", "код товара", "номер", "part", "oem", "деталь", "catalog", "article", "шифр", "партномер"]
BRAND_KW   = ["бренд", "brand", "производитель", "произв", "марка", "фирма", "изготовитель", "maker", "manufacturer", "вендор", "make"]
PRICE_KW   = ["цена", "price", "стоимость", "прайс", "закуп", "розница", "опт", "закупка", "cost", "ррц", "rub", "грн", "uah", "usd", "сумма", "ценасоскидкой"]

# ─────────────────────────────────────────────────────────────────────────────
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ПАРСИНГ, НОРМАЛИЗАЦИЯ, ЭКСПОРТ)
# ─────────────────────────────────────────────────────────────────────────────
def normalize_header(h: str) -> str:
    return re.sub(r"[\s_\-\.\,\/\(\)]+", "", str(h).strip().lower())

def detect_column(columns: list[str], keywords: list[str]) -> str | None:
    best_col = None
    best_score = -1
    for col in columns:
        norm = normalize_header(col)
        if not norm:
            continue
        for kw in keywords:
            kw_n = normalize_header(kw)
            if norm == kw_n:
                return col
            if norm.startswith(kw_n) and len(kw_n) > best_score:
                best_score = len(kw_n)
                best_col = col
            elif kw_n in norm and len(kw_n) > best_score:
                best_score = len(kw_n)
                best_col = col
    return best_col

def clean_price(val) -> float | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None
    s = str(val).strip()
    s = re.sub(r"[\s\u00a0\u202f\u2009]+", "", s)
    s = re.sub(r"[₽$€£¥₴руб\.RUBrub]+", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        res = float(s)
        return res if res > 0 else None
    except ValueError:
        return None

def find_header_row(df_raw: pd.DataFrame) -> int:
    best_idx = 0
    best_score = -1
    for i in range(min(20, len(df_raw))):
        row = df_raw.iloc[i]
        score = 0
        has_art = False
        has_price = False
        for cell in row:
            norm = normalize_header(str(cell))
            for kw in ARTICLE_KW:
                if normalize_header(kw) in norm:
                    has_art = True
                    score += 2
            for kw in PRICE_KW:
                if normalize_header(kw) in norm:
                    has_price = True
                    score += 2
            for kw in BRAND_KW:
                if normalize_header(kw) in norm:
                    score += 1
        if has_art and has_price:
            score += 5
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx

def read_file(uploaded_file) -> pd.DataFrame | None:
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            for enc in ["utf-8-sig", "utf-8", "cp1251", "latin-1"]:
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, encoding=enc, sep=None, engine="python", header=None, dtype=str)
                except Exception:
                    continue
            return None
        elif name.endswith(".ods"):
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, engine="odf", header=None, dtype=str)
        else:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, header=None, dtype=str)
    except Exception:
        return None

def parse_price_file(uploaded_file, forced_cols=None) -> dict:
    result = {
        "name": uploaded_file.name,
        "status": "error",
        "message": "",
        "col_art": None,
        "col_brand": None,
        "col_price": None,
        "header_row": 0,
        "df_clean": pd.DataFrame(),
        "row_count": 0,
    }

    df_raw = read_file(uploaded_file)
    if df_raw is None or df_raw.empty:
        result["message"] = "Файл пустой или поврежден"
        return result

    hrow = find_header_row(df_raw)
    result["header_row"] = hrow

    headers = df_raw.iloc[hrow].tolist()
    headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(headers)]

    df = df_raw.iloc[hrow + 1:].copy()
    df.columns = headers
    df = df.dropna(how="all")

    if df.empty:
        result["message"] = "Нет данных после шапки"
        return result

    # Автоопределение или принудительный ручной выбор
    if forced_cols and forced_cols.get("art") and forced_cols.get("art") != "—":
        col_art = forced_cols["art"]
    else:
        col_art = detect_column(headers, ARTICLE_KW)

    if forced_cols and forced_cols.get("brand") and forced_cols.get("brand") != "—":
        col_brand = forced_cols["brand"]
    else:
        col_brand = detect_column(headers, BRAND_KW)

    if forced_cols and forced_cols.get("price") and forced_cols.get("price") != "—":
        col_price = forced_cols["price"]
    else:
        col_price = detect_column(headers, PRICE_KW)

    result["col_art"]   = col_art
    result["col_brand"] = col_brand
    result["col_price"] = col_price

    if not col_art or not col_price:
        result["message"] = f"❌ Не найдены обязательные столбцы (Артикул: {bool(col_art)}, Цена: {bool(col_price)})"
        return result

    rows = []
    source = Path(uploaded_file.name).stem

    for _, row in df.iterrows():
        art_val = str(row.get(col_art, "")).strip()
        if not art_val or art_val.lower() in ("nan", "none", ""):
            continue

        price_val = clean_price(row.get(col_price))
        if price_val is None:
            continue

        brand_val = ""
        if col_brand:
            bv = str(row.get(col_brand, "")).strip()
            brand_val = "" if bv.lower() in ("nan", "none", "") else bv

        rows.append({
            "Артикул": art_val,
            "Бренд": brand_val if brand_val else "—",
            "Цена": price_val,
            "Источник": source,
        })

    if not rows:
        result["message"] = "⚠️ Нет строк с валидными артикулами и ценами"
        result["status"] = "warning"
        return result

    df_clean = pd.DataFrame(rows)
    result["df_clean"] = df_clean
    result["row_count"] = len(df_clean)
    result["status"] = "ok"
    result["message"] = f"✅ Успешно: {len(df_clean):,} строк"
    return result

def aggregate_best_prices(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    # Нормализуем артикул (без пробелов, верхний регистр)
    df["_key"] = df["Артикул"].str.upper().str.replace(r"[\s\-_]", "", regex=True)

    grp = df.groupby("_key")["Цена"].agg(
        Цена_мин="min",
        Цена_макс="max",
        Предложений="count"
    ).reset_index()

    idx_min = df.groupby("_key")["Цена"].idxmin()
    df_best = df.loc[idx_min].copy()
    df_best = df_best.merge(grp, on="_key")
    df_best = df_best.drop(columns=["_key", "Цена"], errors="ignore")
    df_best = df_best.rename(columns={"Цена_мин": "Цена"})

    df_best["Экономия_руб"] = (df_best["Цена_макс"] - df_best["Цена"]).round(2)
    df_best["Экономия_%"] = np.where(
        df_best["Цена_макс"] > 0,
        ((df_best["Экономия_руб"] / df_best["Цена_макс"]) * 100).round(1),
        0.0
    )

    cols = ["Артикул", "Бренд", "Цена", "Источник", "Предложений", "Цена_макс", "Экономия_руб", "Экономия_%"]
    df_best = df_best[[c for c in cols if c in df_best.columns]]
    df_best = df_best.sort_values("Артикул").reset_index(drop=True)
    return df_best

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Best Prices")
        ws = writer.sheets["Best Prices"]
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        header_fill = PatternFill("solid", fgColor="18181b")
        header_font = Font(bold=True, color="C4B5FD", size=10)
        thin_border = Border(bottom=Side(style="thin", color="27272a"))
        price_font = Font(bold=True, color="34D399", size=11)

        price_col_idx = None
        for i, col in enumerate(df.columns, 1):
            if col == "Цена":
                price_col_idx = i

        for col_idx, col_name in enumerate(df.columns, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = col_name.upper()
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

            max_len = max(
                len(str(col_name)),
                *[len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(2, min(ws.max_row + 1, 200))]
            )
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 45)

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(vertical="center")
                cell.border = thin_border
                if price_col_idx and cell.column == price_col_idx:
                    cell.font = price_font
                    if cell.value is not None:
                        cell.number_format = '#,##0.00 ₽'

        ws.row_dimensions[1].height = 24
        ws.freeze_panes = "A2"
    return output.getvalue()

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig", sep=";").encode("utf-8-sig")

# ─────────────────────────────────────────────────────────────────────────────
# 4. СОСТОЯНИЕ (SESSION STATE)
# ─────────────────────────────────────────────────────────────────────────────
if "parsed_results" not in st.session_state:
    st.session_state.parsed_results = []
if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame()
if "uploaded_objects" not in st.session_state:
    st.session_state.uploaded_objects = []

# ─────────────────────────────────────────────────────────────────────────────
# 5. САЙДБАР (ДИЗАЙН В СТИЛЕ ВАРИАНТА А)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:.75rem;padding:.5rem 0 1.5rem;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:1.5rem;">
          <div style="width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#7c3aed,#4f46e5);display:flex;align-items:center;justify-content:center;font-size:1.2rem;box-shadow:0 4px 15px rgba(124,58,237,0.4)">⚡</div>
          <div>
            <div style="font-weight:700;font-size:1rem;color:#fff;letter-spacing:-0.01em">PRICE.FUSION</div>
            <div style="font-size:0.65rem;color:#71717a;font-family:monospace;letter-spacing:0.1em">MONOLITH STREAMLIT</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">📂 Источник данных</div>', unsafe_allow_html=True)
    
    # Виртуальный путь для соответствия референсу Варианта А
    sim_path = st.text_input("Путь к папке", value=r"C:\Прайсы\2026\ или /home/user/prices", label_visibility="collapsed")

    uploaded_files = st.file_uploader(
        "Выберите прайс-листы",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        help="Загрузите прайс-листы или папку с файлами"
    )

    if uploaded_files:
        st.session_state.uploaded_objects = uploaded_files

    st.markdown("<br>", unsafe_allow_html=True)

    c_run, c_clr = st.columns(2)
    with c_run:
        btn_analyze = st.button("▶ Анализ", use_container_width=True, disabled=not st.session_state.uploaded_objects)
    with c_clr:
        if st.button("✕ Сброс", use_container_width=True):
            st.session_state.parsed_results = []
            st.session_state.df_final = pd.DataFrame()
            st.session_state.uploaded_objects = []
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-title">⚡ Демо-данные</div>', unsafe_allow_html=True)
    st.caption("Нет собственной папки? Нажмите кнопку для быстрого теста трех прайсов.")
    
    if st.button("🚀 Загрузить демо-папку", use_container_width=True):
        # Создаем демо-файлы в памяти с пересекающимися артикулами
        df_demo1 = pd.DataFrame({
            "Артикул товара": ["IP15-128-BLK", "IP15-256-WHT", "SAM-S24-256", "XIA-14-512", "SONY-XM5", "MAC-AIR-M3"],
            "Производитель": ["Apple", "Apple", "Samsung", "Xiaomi", "Sony", "Apple"],
            "Цена закупки": [78900, 89900, 69900, 54900, 34500, 142000]
        })
        df_demo2 = pd.DataFrame({
            "Код SKU": ["IP15-128-BLK", "IP15-256-WHT", "SAM-S24-256", "XIA-14-512", "SONY-XM5", "DYSON-HS05"],
            "Бренд": ["Apple LLC", "Apple", "Samsung Group", "Xiaomi Corp", "Sony", "Dyson"],
            "Опт цена": [76500, 91200, 67800, 56900, 32900, 47900] # Здесь дешевле IP15-128, SAM-S24, SONY-XM5
        })
        df_demo3 = pd.DataFrame({
            "Артикул": ["IP15-128-BLK", "IP15-256-WHT", "SAM-S24-256", "XIA-14-512", "MAC-AIR-M3", "PS5-SLIM"],
            "Бренд": ["Apple", "Apple", "Samsung", "Xiaomi", "Apple Store", "Sony"],
            "Цена со скидкой": [79000, 88500, 71000, 52900, 139000, 48900] # Здесь дешевле IP15-256, XIA-14, MAC-AIR
        })

        def df_to_uploaded(df, filename):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Prices")
            output.seek(0)
            class MockFile(io.BytesIO):
                def __init__(self, val, name):
                    super().__init__(val)
                    self.name = name
            return MockFile(output.getvalue(), filename)

        demo_files = [
            df_to_uploaded(df_demo1, "Прайс_Марвел_Дистрибьюция.xlsx"),
            df_to_uploaded(df_demo2, "ОптТорг_Смартфоны_Юг.xlsx"),
            df_to_uploaded(df_demo3, "Премиум_Импорт_Москва.xlsx"),
        ]

        st.session_state.uploaded_objects = demo_files
        
        results = []
        all_frames = []
        for uf in demo_files:
            res = parse_price_file(uf)
            results.append(res)
            if res["status"] == "ok" and not res["df_clean"].empty:
                all_frames.append(res["df_clean"])
        
        st.session_state.parsed_results = results
        if all_frames:
            df_all = pd.concat(all_frames, ignore_index=True)
            st.session_state.df_final = aggregate_best_prices(df_all)
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size:0.72rem;color:#71717a;line-height:1.6">
          <b>Автоматический поиск:</b><br>
          • Артикул / SKU / Код<br>
          • Бренд / Производитель<br>
          • Цена / Стоимость / Закуп
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 6. ОБРАБОТКА ПО КНОПКЕ АНАЛИЗ
# ─────────────────────────────────────────────────────────────────────────────
if btn_analyze and st.session_state.uploaded_objects:
    results = []
    all_frames = []
    
    prog = st.progress(0, text="🔄 Интеллектуальный анализ прайс-листов...")
    for idx, uf in enumerate(st.session_state.uploaded_objects):
        prog.progress((idx + 1) / len(st.session_state.uploaded_objects), text=f"Анализ файла: {uf.name}")
        
        forced = {}
        if st.session_state.get(f"ovr_art_{uf.name}"):
            forced["art"] = st.session_state[f"ovr_art_{uf.name}"]
        if st.session_state.get(f"ovr_brand_{uf.name}"):
            forced["brand"] = st.session_state[f"ovr_brand_{uf.name}"]
        if st.session_state.get(f"ovr_price_{uf.name}"):
            forced["price"] = st.session_state[f"ovr_price_{uf.name}"]

        res = parse_price_file(uf, forced_cols=forced if forced else None)
        results.append(res)
        if res["status"] == "ok" and not res["df_clean"].empty:
            all_frames.append(res["df_clean"])
            
    prog.empty()
    st.session_state.parsed_results = results
    
    if all_frames:
        df_all = pd.concat(all_frames, ignore_index=True)
        st.session_state.df_final = aggregate_best_prices(df_all)
    else:
        st.session_state.df_final = pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# 7. ГЛАВНЫЙ ИНТЕРФЕЙС
# ─────────────────────────────────────────────────────────────────────────────
df_final: pd.DataFrame = st.session_state.df_final

st.markdown(
    """
    <div style="padding: 1.5rem 0 1.2rem;">
      <div class="hero-title">Price.Fusion · Агрегатор цен</div>
      <div class="hero-sub">
        Загрузите папку с прайсами. Система сама найдёт <b>Артикул / Бренд / Цену</b>,
        сравнит предложения со всех файлов и оставит самую низкую цену с указанием источника.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Если ничего не загружено — показываем стильный онбординг (как в Варианте А)
if df_final.empty and not st.session_state.parsed_results:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="step-box">
              <div class="step-num">01</div>
              <div style="font-weight:700;color:#f4f4f5;margin-bottom:.4rem;font-size:0.95rem">Авто-поиск шапки</div>
              <div style="font-size:0.8rem;color:#a1a1aa;line-height:1.6">
                Ищем строку, где встречаются ключевые слова в первых 20 строках, даже в самых грязных прайсах.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="step-box">
              <div class="step-num">02</div>
              <div style="font-weight:700;color:#f4f4f5;margin-bottom:.4rem;font-size:0.95rem">Нормализация</div>
              <div style="font-size:0.8rem;color:#a1a1aa;line-height:1.6">
                Артикулы приводим к верхнему регистру без пробелов, цены парсим из любого формата 1 200,50 ₽.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="step-box">
              <div class="step-num">03</div>
              <div style="font-weight:700;color:#f4f4f5;margin-bottom:.4rem;font-size:0.95rem">Выбор минимума</div>
              <div style="font-size:0.8rem;color:#a1a1aa;line-height:1.6">
                Группируем по Артикул + Бренд и оставляем только запись с минимальной ценой и источником.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 **Начните работу:** выберите файлы слева или нажмите **«🚀 Загрузить демо-папку»** для быстрого теста.", icon="💡")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 8. КАРТОЧКИ ФАЙЛОВ И РУЧНАЯ КОРРЕКЦИЯ КОЛОНОК
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📂 Источники прайс-листов</div>', unsafe_allow_html=True)

for res in st.session_state.parsed_results:
    icon  = "✅" if res["status"] == "ok" else ("⚠️" if res["status"] == "warning" else "❌")
    cls   = "card-ok" if res["status"] == "ok" else ("card-warn" if res["status"] == "warning" else "card-err")
    badge = (
        f'<span class="badge badge-green">OK · {res["row_count"]:,} строк</span>'
        if res["status"] == "ok"
        else (
            f'<span class="badge badge-yellow">ВНИМАНИЕ</span>'
            if res["status"] == "warning"
            else '<span class="badge badge-red">ОШИБКА</span>'
        )
    )
    art_b   = f'<span class="badge badge-blue">Арт: {res["col_art"] or "—"}</span>'
    brand_b = f'<span class="badge badge-blue">Бренд: {res["col_brand"] or "—"}</span>'
    price_b = f'<span class="badge badge-blue">Цена: {res["col_price"] or "—"}</span>'

    st.markdown(
        f"""
        <div class="card {cls}">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem">
            <div>
              <span style="font-weight:700;color:#f4f4f5">{icon} {res['name']}</span>
              &nbsp;{badge}
            </div>
            <div style="display:flex;gap:.4rem;flex-wrap:wrap">
              {art_b} {brand_b} {price_b}
            </div>
          </div>
          <div style="font-size:0.78rem;color:#a1a1aa;margin-top:.4rem">{res['message']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ручное переопределение колонок при необходимости
    if res["status"] in ("error", "warning") or not res["col_art"] or not res["col_price"]:
        with st.expander(f"🔧 Настроить столбцы вручную для «{res['name']}»"):
            try:
                raw_test = None
                for uf in st.session_state.uploaded_objects:
                    if uf.name == res["name"]:
                        raw_test = read_file(uf)
                        break
                if raw_test is not None:
                    h_idx = res["header_row"]
                    headers_list = ["—"] + [str(x) for x in raw_test.iloc[h_idx].tolist() if pd.notna(x)]
                else:
                    headers_list = ["—"]
            except Exception:
                headers_list = ["—"]

            c_a, c_b, c_p = st.columns(3)
            with c_a:
                st.selectbox("Столбец: Артикул", headers_list, key=f"ovr_art_{res['name']}")
            with c_b:
                st.selectbox("Столбец: Бренд", headers_list, key=f"ovr_brand_{res['name']}")
            with c_p:
                st.selectbox("Столбец: Цена", headers_list, key=f"ovr_price_{res['name']}")
            st.caption("После выбора нажмите кнопку **▶ Анализ** в сайдбаре слева повторно.")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 9. МЕТРИКИ (KPI DASHBOARD)
# ─────────────────────────────────────────────────────────────────────────────
if not df_final.empty:
    st.markdown('<div class="section-title">📊 Сводные метрики агрегатора</div>', unsafe_allow_html=True)

    total_unique = len(df_final)
    total_offers = df_final["Предложений"].sum() if "Предложений" in df_final.columns else 0
    total_savings = df_final["Экономия_руб"].sum() if "Экономия_руб" in df_final.columns else 0
    avg_price = df_final["Цена"].mean()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🔑 Уникальных SKU", f"{total_unique:,}")
    m2.metric("📋 Всего предложений", f"{int(total_offers):,}")
    m3.metric("💰 Средняя мин. цена", f"{avg_price:,.0f} ₽")
    m4.metric("📉 Суммарная экономия", f"{total_savings:,.0f} ₽", delta="Лучшие цены со всех прайсов")

    st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 10. ТАБЛИЦА РЕЗУЛЬТАТОВ, АНАЛИЗ И ЭКСПОРТ
# ─────────────────────────────────────────────────────────────────────────────
if not df_final.empty:
    
    tab_table, tab_analysis, tab_sources = st.tabs([
        "📋 Итоговый прайс", "📈 Анализ и графики", "🏢 По источникам"
    ])

    # ── TAB 1: ТАБЛИЦА ──
    with tab_table:
        st.markdown('<div class="section-title">🏆 Итоговый прайс (минимальная цена + источник)</div>', unsafe_allow_html=True)

        f_col1, f_col2, f_col3 = st.columns([3, 2, 2])
        with f_col1:
            search_q = st.text_input("🔍 Поиск по артикулу, бренду или источнику", placeholder="Введите запрос...", label_visibility="collapsed")
        with f_col2:
            brand_list = ["Все бренды"] + sorted(df_final["Бренд"].dropna().unique().tolist())
            sel_brand_val = st.selectbox("Бренд", brand_list, label_visibility="collapsed")
        with f_col3:
            source_list = ["Все источники"] + sorted(df_final["Источник"].dropna().unique().tolist())
            sel_source_val = st.selectbox("Источник", source_list, label_visibility="collapsed")

        df_view = df_final.copy()
        if search_q:
            q = search_q.strip().lower()
            df_view = df_view[
                df_view["Артикул"].str.lower().str.contains(q, na=False) |
                df_view["Бренд"].str.lower().str.contains(q, na=False) |
                df_view["Источник"].str.lower().str.contains(q, na=False)
            ]
        if sel_brand_val != "Все бренды":
            df_view = df_view[df_view["Бренд"] == sel_brand_val]
        if sel_source_val != "Все источники":
            df_view = df_view[df_view["Источник"] == sel_source_val]

        disp_cols = ["Артикул", "Бренд", "Цена", "Источник", "Предложений", "Экономия_руб", "Экономия_%"]
        disp_cols = [c for c in disp_cols if c in df_view.columns]

        st.dataframe(
            df_view[disp_cols].style.format({
                "Цена": "{:,.2f} ₽",
                "Экономия_руб": "{:,.2f} ₽",
                "Экономия_%": "{:.1f}%",
            }),
            use_container_width=True,
            height=500,
            hide_index=True,
            column_config={
                "Артикул": st.column_config.TextColumn("🔑 Артикул", width="medium"),
                "Бренд": st.column_config.TextColumn("🏷 Бренд", width="medium"),
                "Цена": st.column_config.NumberColumn("💰 Мин. цена (₽)", format="%.2f ₽", width="small"),
                "Источник": st.column_config.TextColumn("📁 Источник (Прайс)", width="large"),
                "Предложений": st.column_config.NumberColumn("📊 Предл.", width="small", help="Кол-во поставщиков"),
                "Экономия_руб": st.column_config.NumberColumn("💚 Экономия (₽)", format="%.2f ₽", width="small"),
                "Экономия_%": st.column_config.NumberColumn("📉 Экономия (%)", format="%.1f%%", width="small"),
            }
        )

        # ── Экспорт ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">💾 Скачивание результата</div>', unsafe_allow_html=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        excel_bytes = to_excel_bytes(df_view[disp_cols])
        csv_bytes = to_csv_bytes(df_view[disp_cols])

        dl_c1, dl_c2 = st.columns(2)
        with dl_c1:
            st.download_button(
                label="📗 Скачать в Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"price_fusion_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with dl_c2:
            st.download_button(
                label="📄 Скачать в CSV (.csv)",
                data=csv_bytes,
                file_name=f"price_fusion_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ── TAB 2: АНАЛИЗ И ГРАФИКИ ──
    with tab_analysis:
        st.markdown('<div class="section-title">📈 Анализ цен и распределения</div>', unsafe_allow_html=True)

        gc1, gc2 = st.columns(2)
        with gc1:
            st.markdown("**Распределение минимальных цен**")
            prices_data = df_final["Цена"].dropna()
            p98 = prices_data.quantile(0.98)
            clipped = prices_data[prices_data <= p98]
            bins = min(40, max(10, len(clipped) // 15))
            hist = pd.cut(clipped, bins=bins).value_counts().sort_index()
            hist_df = pd.DataFrame({
                "Диапазон": [str(i.mid.round(0)) for i in hist.index],
                "Кол-во": hist.values,
            })
            st.bar_chart(hist_df.set_index("Диапазон"), color="#8b5cf6", height=300)

        with gc2:
            st.markdown("**Топ-10 брендов по числу SKU**")
            top_brands = df_final[df_final["Бренд"] != "—"]["Бренд"].value_counts().head(10).reset_index()
            top_brands.columns = ["Бренд", "Артикулов"]
            st.bar_chart(top_brands.set_index("Бренд"), color="#34d399", height=300)

    # ── TAB 3: ПО ИСТОЧНИКАМ ──
    with tab_sources:
        st.markdown('<div class="section-title">🏢 Статистика по источникам (поставщикам)</div>', unsafe_allow_html=True)

        src_stats = df_final.groupby("Источник").agg(
            Побед=("Источник", "count"),
            Мин_цена=("Цена", "min"),
            Средн_цена=("Цена", "mean"),
            Макс_цена=("Цена", "max"),
            Экономия=("Экономия_руб", "sum"),
        ).round(2).sort_values("Побед", ascending=False).reset_index()

        st.dataframe(
            src_stats.style.format({
                "Мин_цена": "{:,.0f} ₽",
                "Средн_цена": "{:,.0f} ₽",
                "Макс_цена": "{:,.0f} ₽",
                "Экономия": "{:,.0f} ₽",
            }),
            use_container_width=True,
            height=380,
            hide_index=True,
            column_config={
                "Источник": st.column_config.TextColumn("📁 Источник", width="large"),
                "Побед": st.column_config.NumberColumn("🏆 Побед (мин. цена)", help="Кол-во позиций, где этот прайс дал самую дешёвую цену"),
                "Мин_цена": st.column_config.NumberColumn("Min ₽", format="%.0f ₽"),
                "Средн_цена": st.column_config.NumberColumn("Ср. ₽", format="%.0f ₽"),
                "Макс_цена": st.column_config.NumberColumn("Max ₽", format="%.0f ₽"),
                "Экономия": st.column_config.NumberColumn("💚 Экономия ₽", format="%.0f ₽"),
            }
        )

# ─────────────────────────────────────────────────────────────────────────────
# 11. FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <hr>
    <div style="text-align:center;font-size:0.75rem;color:#71717a;padding:1rem 0">
      ⚡ <b>Price.Fusion</b> &nbsp;·&nbsp; Монолитный Streamlit App &nbsp;·&nbsp; Все функции и стили в одном файле <code>app.py</code>
    </div>
    """,
    unsafe_allow_html=True,
)
