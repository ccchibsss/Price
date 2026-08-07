# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║           PRICE.FUSION — МОНОЛИТНЫЙ STREAMLIT (ВСЁ В 1 ФАЙЛЕ app.py)        ║
#    Авто-поиск: Артикул | Бренд | Цена → Мин. цена + Источник + Экспорт        ║
#    Оптимизировано: 300k+ строк, векторизованные операции                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
import pandas as pd
import numpy as np
import io
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# 0. КОНФИГУРАЦИЯ СТРАНИЦЫ
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Price.Fusion — Агрегатор прайсов",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CSS СТИЛИ (СИНЯЯ ТЕМА + ТЁМНЫЕ КНОПКИ + ЧИТАЕМОСТЬ)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Общий фон и шрифт ── */
    .stApp {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%) !important;
        color: #f4f4f5 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Сайдбар ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3352 0%, #234567 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] * {
        color: #e0e7ff !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* ── Кнопки управления (ТЁМНО-СИНИЕ) ── */
    .stButton > button {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f2440 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(15, 36, 64, 0.5) !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(15, 36, 64, 0.7) !important;
        background: linear-gradient(135deg, #2d5a87 0%, #1e3a5f 100%) !important;
        border-color: rgba(96, 165, 250, 0.6) !important;
    }
    .stButton > button:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }

    /* ── Кнопки скачивания (ТЁМНО-ЗЕЛЁНЫЕ) ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(6, 78, 59, 0.5) !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(6, 78, 59, 0.7) !important;
        background: linear-gradient(135deg, #065f46 0%, #047857 100%) !important;
        border-color: rgba(16, 185, 129, 0.6) !important;
    }

    /* ── Загрузчик файлов ── */
    [data-testid="stFileUploader"] {
        background: rgba(15, 36, 64, 0.85) !important;
        border: 2px dashed rgba(56, 189, 248, 0.45) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        transition: all 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(56, 189, 248, 0.8) !important;
        background: rgba(15, 36, 64, 0.95) !important;
    }
    /* убираем белый фон дропзоны во всех вложенных элементах */
    [data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"],
    [data-testid="stFileUploadDropzone"] > div,
    [data-testid="stFileUploadDropzoneInput"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] > div > div,
    [data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploadDropzone"] small {
        color: #9db8d8 !important;
    }
    [data-testid="stFileUploader"] *,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] div {
        color: #e8eefc !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #0f2440 !important;
        color: #ffffff !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #1e3a5f !important;
        border-color: #38bdf8 !important;
    }
    [data-testid="stFileUploader"] svg {
        fill: #7dd3fc !important;
        color: #7dd3fc !important;
    }

    /* ── Мульти-селект (выбор столбцов для выгрузки) ── */
    [data-testid="stMultiSelect"] label,
    [data-testid="stMultiSelect"] label p,
    [data-testid="stMultiSelect"] > label p {
        color: #f4f4f5 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #0f2440 !important;
        border: 1px solid rgba(96, 165, 250, 0.35) !important;
        border-radius: 12px !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.25) !important;
    }
    [data-testid="stMultiSelect"] input {
        color: #ffffff !important;
    }
    [data-testid="stMultiSelect"] input::placeholder {
        color: #7d9ac2 !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background: rgba(56, 189, 248, 0.18) !important;
        color: #bae6fd !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
        fill: #bae6fd !important;
        color: #bae6fd !important;
    }
    /* выпадающий список опций мульти-селекта */
    [data-baseweb="popover"] div[role="listbox"],
    [data-baseweb="menu"] {
        background-color: #0f2440 !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        border-radius: 12px !important;
    }
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] li * {
        color: #e8eefc !important;
    }
    [data-baseweb="menu"] li:hover,
    li[role="option"]:hover,
    div[role="option"]:hover {
        background-color: rgba(56, 189, 248, 0.18) !important;
    }

    /* ── Метрики ── */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 1.1rem 1.3rem !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #93c5fd !important;
    }

    /* ── Карточки файлов ── */
    .card {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        padding: 1.2rem 1.4rem !important;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(10px);
        transition: border-color 0.2s;
    }
    .card:hover { border-color: rgba(96, 165, 250, 0.4) !important; }
    .card-ok   { border-left: 3px solid #10b981 !important; }
    .card-warn { border-left: 3px solid #f59e0b !important; }
    .card-err  { border-left: 3px solid #ef4444 !important; }

    /* ── Бейджи ── */
    .badge {
        display: inline-block;
        padding: 0.2em 0.7em;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.06em;
    }
    .badge-green  { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-red    { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-yellow { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-blue   { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }

    /* ── Заголовки и текст ── */
    .hero-title {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #ffffff 0%, #bfdbfe 50%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.15;
        letter-spacing: -0.03em;
    }
    .hero-sub {
        color: #bfdbfe !important;
        font-size: 1rem !important;
        margin-top: 0.5rem !important;
        line-height: 1.6;
        max-width: 680px;
    }
    .section-title {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: #93c5fd !important;
        margin-bottom: 0.8rem;
    }

    /* ── Шаги / Онбординг ── */
    .step-box {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        text-align: left;
        backdrop-filter: blur(10px);
        transition: all 0.2s;
    }
    .step-box:hover {
        border-color: rgba(96, 165, 250, 0.4) !important;
        transform: translateY(-2px);
    }
    .step-num {
        width: 42px !important;
        height: 42px !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(37, 99, 235, 0.3)) !important;
        border: 1px solid rgba(96, 165, 250, 0.5) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        color: #bfdbfe !important;
        margin-bottom: 0.9rem;
    }

    /* ── Инпуты, селекты, текстовые поля ── */
    input,
    select,
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    [data-testid="stTextInputRootElement"] input {
        background: #1e3a5f !important;
        background-color: #1e3a5f !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
    }
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    [data-testid="stTextInputRootElement"]:focus-within {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.3) !important;
    }
    input::placeholder,
    .stTextInput input::placeholder,
    [data-testid="stTextInputRootElement"] input::placeholder {
        color: #93c5fd !important;
        opacity: 0.85 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1e3a5f !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] * { color: #ffffff !important; }

    /* ── Выпадающие списки (опции) ── */
    div[data-baseweb="menu"] {
        background-color: #1e3a5f !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    div[data-baseweb="menu"] * { color: #ffffff !important; }
    div[data-baseweb="option"]:hover {
        background-color: #2d5a87 !important;
    }

    /* ── Табы ── */
    [data-testid="stTabs"] > div:first-child {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #93c5fd !important;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.7rem 1.4rem !important;
        border-radius: 10px 10px 0 0 !important;
        transition: all 0.2s;
    }
    button[data-baseweb="tab"]:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #60a5fa !important;
        background: rgba(96, 165, 250, 0.15) !important;
    }

    /* ── DataFrame таблица ── */
    div[data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div[data-testid="stDataFrame"] table { color: #f4f4f5 !important; }
    div[data-testid="stDataFrame"] th {
        background: rgba(30, 58, 95, 0.8) !important;
        color: #93c5fd !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div[data-testid="stDataFrame"] td {
        color: #f4f4f5 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] * { color: #f4f4f5 !important; }

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #3b82f6, #60a5fa) !important;
    }

    /* ── Info/Warning/Error boxes ── */
    [data-testid="stAlert"] {
        background: rgba(30, 58, 95, 0.8) !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        border-radius: 12px !important;
        color: #f4f4f5 !important;
    }
    [data-testid="stAlert"] * { color: #f4f4f5 !important; }

    hr { border: none; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 1.5rem 0; }

    /* ── Скроллбар ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #1e3a5f; }
    ::-webkit-scrollbar-thumb { background: rgba(96, 165, 250, 0.5); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(147, 197, 253, 0.7); }

    /* ── Caption ── */
    .stCaption { color: #93c5fd !important; }

    /* ── Spinner для экспорта ── */
    .pf-spinner {
        width: 22px;
        height: 22px;
        border: 3px solid rgba(147, 197, 253, 0.25);
        border-top-color: #60a5fa;
        border-radius: 50%;
        animation: pf-spin 0.7s linear infinite;
        flex-shrink: 0;
    }
    @keyframes pf-spin {
        to { transform: rotate(360deg); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. КЛЮЧЕВЫЕ СЛОВА ДЛЯ АВТО-ОПРЕДЕЛЕНИЯ КОЛОНОК
# ─────────────────────────────────────────────────────────────────────────────
ARTICLE_KW = [
    "артикул", "арт", "sku", "код", "кодтовара", "код товара",
    "номер", "part", "oem", "деталь", "catalog", "article",
    "шифр", "партномер", "code", "product code", "item",
    "ean", "upc", "gtin", "mpn", "model", "модель",
]

BRAND_KW = [
    "бренд", "brand", "производитель", "произв", "марка",
    "фирма", "изготовитель", "maker", "manufacturer",
    "вендор", "make", "producer",
]

PRICE_KW = [
    "цена", "price", "стоимость", "прайс", "закуп",
    "розница", "опт", "закупка", "cost", "ррц",
    "rub", "грн", "uah", "usd", "сумма", "ценасоскидкой",
    "цена со скидкой", "опт цена", "цена закупки",
    "стоимость закупки", "retail", "wholesale",
    "amount", "total", "sum", "net", "gross",
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────────────────────────────────────


def normalize_header(h: str) -> str:
    """Нормализация заголовка: убираем пробелы, спецсимволы, приводим к нижнему регистру."""
    return re.sub(r"[\s_\-\.\,\/\(\)]+", "", str(h).strip().lower())


def detect_column(
    columns: list[str], keywords: list[str]
) -> Optional[str]:
    """Авто-поиск колонки по ключевым словам. Возвращает наилучшее совпадение."""
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


def clean_price_vectorized(series: pd.Series) -> pd.Series:
    """
    Векторизованная очистка цен.
    Преобразует Series со строковыми ценами в float. Неверные → NaN.

    Поддерживаемые форматы:
      - "1 200,50 ₽"    → 1200.50
      - "1.200,50"      → 1200.50  (европейский формат)
      - "1,200.50"      → 1200.50  (американский формат)
      - "$1200"         → 1200.00
      - "1200 руб"      → 1200.00
    """
    # Конвертируем в object dtype чтобы избежать PyArrow проблем с regex
    s = series.fillna("").astype(object).astype(str).str.strip()

    # Заменяем Unicode whitespace символы на обычный пробел (regex=False)
    s = s.str.replace("\u00a0", " ", regex=False)  # non-breaking space
    s = s.str.replace("\u202f", " ", regex=False)  # narrow no-break space
    s = s.str.replace("\u2009", " ", regex=False)  # thin space
    s = s.str.replace("\u200b", "", regex=False)   # zero-width space

    # Убираем все пробелы
    s = s.str.replace(r"\s+", "", regex=True)

    # Убираем символы валют и буквенные суффиксы
    s = s.str.replace(r"[₽$€£¥₴]", "", regex=True)
    s = s.str.replace(r"руб\.?", "", regex=True, case=False)
    s = s.str.replace(r"RUB|rub", "", regex=True, case=False)

    # Пустые → NaN
    s = s.replace(
        {
            "": np.nan,
            "nan": np.nan,
            "none": np.nan,
            "None": np.nan,
            "NULL": np.nan,
        }
    )

    # Обработка запятых и точек
    has_comma = s.str.contains(",", na=False)
    has_dot = s.str.contains(r"\.", na=False, regex=True)

    # Случай 1: есть и запятая, и точка → разделитель тот, что правее
    both = has_comma & has_dot
    comma_right = s.str.rfind(",") > s.str.rfind(r"\.")
    mask1 = both & comma_right  # запятая — десятичный разделитель
    mask2 = both & ~comma_right  # точка — десятичный разделитель

    # Случай 2: только запятая
    only_comma = has_comma & ~has_dot
    # Проверяем: если после запятой ≤2 цифр → десятичный разделитель
    decimal_comma = only_comma & s.str.contains(r",\d{1,2}$", na=False, regex=True)

    # Применяем замены
    result = s.copy()
    result[mask1] = result[mask1].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    result[mask2] = result[mask2].str.replace(",", "", regex=False)
    result[decimal_comma] = result[decimal_comma].str.replace(",", ".", regex=False)
    result[only_comma & ~decimal_comma] = result[only_comma & ~decimal_comma].str.replace(",", "", regex=False)

    # Преобразуем в numeric
    numeric = pd.to_numeric(result, errors="coerce")
    return numeric.where(numeric > 0, np.nan)


def find_header_row(df_raw: pd.DataFrame) -> int:
    """
    Поиск строки заголовка в первых 30 строках.
    Считает score на основе совпадений ключевых слов.
    """
    best_idx = 0
    best_score = -1
    for i in range(min(30, len(df_raw))):
        row = df_raw.iloc[i]
        score = 0
        has_art = False
        has_price = False
        for cell in row:
            norm = normalize_header(str(cell))
            for kw in ARTICLE_KW:
                if normalize_header(kw) in norm or norm in normalize_header(kw):
                    has_art = True
                    score += 2
            for kw in PRICE_KW:
                if normalize_header(kw) in norm or norm in normalize_header(kw):
                    has_price = True
                    score += 2
            for kw in BRAND_KW:
                if normalize_header(kw) in norm or norm in normalize_header(kw):
                    score += 1
        if has_art and has_price:
            score += 5
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx


def read_file(uploaded_file) -> Optional[pd.DataFrame]:
    """Чтение файла (xlsx, xls, csv, ods) в DataFrame с raw-строкami."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            for enc in ["utf-8-sig", "utf-8", "cp1251", "latin-1"]:
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(
                        uploaded_file,
                        encoding=enc,
                        sep=None,
                        engine="python",
                        header=None,
                        dtype=str,
                    )
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


def parse_price_file(
    uploaded_file, forced_cols: Optional[dict] = None
) -> dict:
    """
    Парсинг одного прайс-листа.
    Возвращает словарь с результатами: статус, сообщение, найденные колонки, очищенные данные.
    """
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
    headers = [
        str(h).strip() if h is not None else f"col_{i}"
        for i, h in enumerate(headers)
    ]

    df = df_raw.iloc[hrow + 1 :].copy()
    df.columns = headers
    df = df.dropna(how="all")

    if df.empty:
        result["message"] = "Нет данных после шапки"
        return result

    # ── Определение колонок (с учётом ручных переопределений) ──
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

    result["col_art"] = col_art
    result["col_brand"] = col_brand
    result["col_price"] = col_price

    if not col_art or not col_price:
        result["message"] = (
            f"❌ Не найдены обязательные столбцы "
            f"(Артикул: {bool(col_art)}, Цена: {bool(col_price)})"
        )
        return result

    # Проверка что колонки существуют в DataFrame
    if col_art not in df.columns or col_price not in df.columns:
        result["message"] = (
            f"❌ Колонки не найдены в данных "
            f"(Артикул: {col_art}, Цена: {col_price})"
        )
        return result

    # ── ВЕКТОРИЗОВАННАЯ обработка ──
    source = Path(uploaded_file.name).stem

    # Артикул: строка, strip, фильтр мусора
    art_series = df[col_art].fillna("").astype(str).str.strip()
    invalid_art = art_series.isin(["", "nan", "none", "NaN", "None"]) | art_series.isna()

    # Цена: векторизованная очистка
    price_series = clean_price_vectorized(df[col_price])

    # Бренд
    if col_brand and col_brand in df.columns:
        brand_series = df[col_brand].fillna("").astype(str).str.strip()
        brand_series = brand_series.where(
            ~brand_series.isin(["", "nan", "none", "NaN", "None"]), "—"
        )
        brand_series = brand_series.replace({"": "—", np.nan: "—"})
    else:
        brand_series = pd.Series("—", index=df.index)

    # Сборка валидных строк
    valid_mask = ~invalid_art & price_series.notna()

    if valid_mask.sum() == 0:
        result["message"] = "⚠️ Нет строк с валидными артикулами и ценами"
        result["status"] = "warning"
        return result

    df_clean = pd.DataFrame(
        {
            "Артикул": art_series[valid_mask].values,
            "Бренд": brand_series[valid_mask].values,
            "Цена": price_series[valid_mask].values,
            "Источник": source,
        }
    ).reset_index(drop=True)

    result["df_clean"] = df_clean
    result["row_count"] = len(df_clean)
    result["status"] = "ok"
    result["message"] = f"✅ Успешно: {len(df_clean):,} строк"
    return result


def aggregate_best_prices(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Агрегация: для каждого уникального Артикула оставляем запись с МИНИМАЛЬНОЙ ценой.
    Сохраняем источник, у которого эта цена, и считаем экономию относительно макс. цены.
    """
    if df_all.empty:
        return pd.DataFrame()

    df = df_all.copy()

    # Фильтр битых артикулов
    df = df[
        df["Артикул"].notna()
        & (df["Артикул"].str.strip() != "")
        & (~df["Артикул"].str.strip().str.lower().isin(["nan", "none", "null", "undefined"]))
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # Нормализация ключа для группировки (без пробелов, регистра, дефисов) — до дедупликации
    df["_key"] = df["Артикул"].str.upper().str.replace(r"[\s\-_\.\,]+", "", regex=True)
    df = df[df["_key"].str.len() > 0]

    if df.empty:
        return pd.DataFrame()

    # Количество ВСЕХ строк (предложений) по артикулу во всех файлах, включая дубли
    qty = df.groupby("_key").size().rename("Количество").reset_index()

    # Дедупликация: один артикул + один источник = одна запись (мин. цена)
    df = df.sort_values("Цена").drop_duplicates(subset=["_key", "Источник"], keep="first")

    # УНИКАЛЬНЫЕ источники + мин/макс цены
    grp = df.groupby("_key").agg(
        Цена_мин=("Цена", "min"),
        Цена_макс=("Цена", "max"),
        Предложений=("Источник", "nunique"),
    ).reset_index()

    # Индекс минимальной цены (среди всех строк для этого артикула)
    idx_min = df.groupby("_key")["Цена"].idxmin()
    df_best = df.loc[idx_min].copy()
    df_best = df_best.merge(grp, on="_key", how="left").merge(qty, on="_key", how="left")
    df_best = df_best.drop(columns=["_key", "Цена"], errors="ignore")
    df_best = df_best.rename(columns={"Цена_мин": "Цена"})

    # Экономия
    df_best["Экономия_руб"] = (df_best["Цена_макс"] - df_best["Цена"]).round(2)
    df_best["Экономия_%"] = np.where(
        df_best["Цена_макс"] > 0,
        ((df_best["Экономия_руб"] / df_best["Цена_макс"]) * 100).round(1),
        0.0,
    )

    cols = [
        "Артикул", "Бренд", "Цена", "Источник",
        "Предложений", "Количество", "Цена_макс", "Экономия_руб", "Экономия_%",
    ]
    df_best = df_best[[c for c in cols if c in df_best.columns]]
    df_best = df_best.sort_values("Артикул").reset_index(drop=True)
    return df_best


@st.cache_data(show_spinner=False, ttl=3600)
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Создание Excel-файла с форматированием (кэшируется)."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Best Prices")
        ws = writer.sheets["Best Prices"]
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        header_fill = PatternFill("solid", fgColor="1e3a5f")
        header_font = Font(bold=True, color="93c5fd", size=10)
        thin_border = Border(bottom=Side(style="thin", color="2d5a87"))
        price_font = Font(bold=True, color="6ee7b7", size=11)

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
                *[
                    len(str(ws.cell(row=r, column=col_idx).value or ""))
                    for r in range(2, min(ws.max_row + 1, 200))
                ],
            )
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 45)

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(vertical="center")
                cell.border = thin_border
                if price_col_idx and cell.column == price_col_idx:
                    cell.font = price_font
                    if cell.value is not None:
                        cell.number_format = "#,##0.00 \u20bd"

        ws.row_dimensions[1].height = 24
        ws.freeze_panes = "A2"
    return output.getvalue()


@st.cache_data(show_spinner=False, ttl=3600)
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Создание CSV-файла (UTF-8 с BOM, разделитель — точка с запятой). Кэшируется."""
    return df.to_csv(index=False, encoding="utf-8-sig", sep=";").encode("utf-8-sig")


def format_file_size(num_bytes: int) -> str:
    """Человекочитаемый размер файла."""
    if num_bytes < 1024:
        return f"{num_bytes} Б"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} КБ"
    return f"{num_bytes / (1024 * 1024):.2f} МБ"


# ─────────────────────────────────────────────────────────────────────────────
# 4. ИНИЦИАЛИЗАЦИЯ SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
if "parsed_results" not in st.session_state:
    st.session_state.parsed_results = []
if "df_final" not in st.session_state:
    st.session_state.df_final = pd.DataFrame()
if "uploaded_objects" not in st.session_state:
    st.session_state.uploaded_objects = []

# ─────────────────────────────────────────────────────────────────────────────
# 5. САЙДБАР
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:.75rem;padding:.5rem 0 1.5rem;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:1.5rem;">
          <div style="width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#3b82f6,#2563eb);display:flex;align-items:center;justify-content:center;font-size:1.2rem;box-shadow:0 4px 15px rgba(59,130,246,0.5)">⚡</div>
          <div>
            <div style="font-weight:700;font-size:1rem;color:#fff;letter-spacing:-0.01em">PRICE.FUSION</div>
            <div style="font-size:0.65rem;color:#93c5fd;font-family:monospace;letter-spacing:0.1em">MONOLITH STREAMLIT</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">📂 Источник данных</div>', unsafe_allow_html=True)

    sim_path = st.text_input(
        "Путь к папке",
        value=r"C:\Прайсы\2026\ или /home/user/prices",
        label_visibility="collapsed",
    )

    uploaded_files = st.file_uploader(
        "Выберите прайс-листы",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        help="Загрузите прайс-листы или папку с файлами",
    )

    if uploaded_files:
        st.session_state.uploaded_objects = uploaded_files

    st.markdown("<br>", unsafe_allow_html=True)

    c_run, c_clr = st.columns(2)
    with c_run:
        btn_analyze = st.button(
            "▶ Анализ",
            use_container_width=True,
            disabled=not st.session_state.uploaded_objects,
        )
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
        df_demo1 = pd.DataFrame(
            {
                "Артикул товара": [
                    "IP15-128-BLK", "IP15-256-WHT", "SAM-S24-256",
                    "XIA-14-512", "SONY-XM5", "MAC-AIR-M3",
                ],
                "Производитель": ["Apple", "Apple", "Samsung", "Xiaomi", "Sony", "Apple"],
                "Цена закупки": [78900, 89900, 69900, 54900, 34500, 142000],
            }
        )
        df_demo2 = pd.DataFrame(
            {
                "Код SKU": [
                    "IP15-128-BLK", "IP15-256-WHT", "SAM-S24-256",
                    "XIA-14-512", "SONY-XM5", "DYSON-HS05",
                ],
                "Бренд": ["Apple LLC", "Apple", "Samsung Group", "Xiaomi Corp", "Sony", "Dyson"],
                "Опт цена": [76500, 91200, 67800, 56900, 32900, 47900],
            }
        )
        df_demo3 = pd.DataFrame(
            {
                "Артикул": [
                    "IP15-128-BLK", "IP15-256-WHT", "SAM-S24-256",
                    "XIA-14-512", "MAC-AIR-M3", "PS5-SLIM",
                ],
                "Бренд": ["Apple", "Apple", "Samsung", "Xiaomi", "Apple Store", "Sony"],
                "Цена со скидкой": [79000, 88500, 71000, 52900, 139000, 48900],
            }
        )

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
        <div style="font-size:0.72rem;color:#93c5fd;line-height:1.6">
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

    total_files = len(st.session_state.uploaded_objects)
    prog = st.progress(0, text=f"🔄 Интеллектуальный анализ прайс-листов (0/{total_files})...")

    for idx, uf in enumerate(st.session_state.uploaded_objects):
        prog.progress(
            (idx) / total_files,
            text=f"Анализ файла {idx + 1}/{total_files}: {uf.name}",
        )

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

    prog.progress(1.0, text="✅ Агрегация результатов...")
    st.session_state.parsed_results = results

    if all_frames:
        df_all = pd.concat(all_frames, ignore_index=True)
        st.session_state.df_final = aggregate_best_prices(df_all)
    else:
        st.session_state.df_final = pd.DataFrame()

    prog.empty()

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

if df_final.empty and not st.session_state.parsed_results:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="step-box">
              <div class="step-num">01</div>
              <div style="font-weight:700;color:#f4f4f5;margin-bottom:.4rem;font-size:0.95rem">Авто-поиск шапки</div>
              <div style="font-size:0.8rem;color:#bfdbfe;line-height:1.6">
                Ищем строку, где встречаются ключевые слова в первых 30 строках, даже в самых грязных прайсах.
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
              <div style="font-size:0.8rem;color:#bfdbfe;line-height:1.6">
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
              <div style="font-weight:700;color:#f4f4f5;margin-bottom:.4rem;font-size:0.95rem">Выборминимума</div>
              <div style="font-size:0.8rem;color:#bfdbfe;line-height:1.6">
                Группируем по Артикул и оставляем запись с минимальной ценой и источником.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(
        "👈 **Начните работу:** выберите файлы слева или нажмите **«🚀 Загрузить демо-папку»** "
        "для быстрого теста.",
        icon="💡",
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 8. КАРТОЧКИ ФАЙЛОВ И РУЧНАЯ КОРРЕКЦИЯ КОЛОНОК
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Источники прайс-листов</div>', unsafe_allow_html=True)

for res in st.session_state.parsed_results:
    icon = (
        "✅" if res["status"] == "ok"
        else ("⚠️" if res["status"] == "warning" else "❌")
    )
    cls = (
        "card-ok" if res["status"] == "ok"
        else ("card-warn" if res["status"] == "warning" else "card-err")
    )
    badge = (
        f'<span class="badge badge-green">OK · {res["row_count"]:,} строк</span>'
        if res["status"] == "ok"
        else (
            '<span class="badge badge-yellow">ВНИМАНИЕ</span>'
            if res["status"] == "warning"
            else '<span class="badge badge-red">ОШИБКА</span>'
        )
    )
    art_b = f'<span class="badge badge-blue">Арт: {res["col_art"] or "—"}</span>'
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
          <div style="font-size:0.78rem;color:#bfdbfe;margin-top:.4rem">{res['message']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
                    headers_list = (
                        ["—"]
                        + [
                            str(x)
                            for x in raw_test.iloc[h_idx].tolist()
                            if pd.notna(x)
                        ]
                    )
                else:
                    headers_list = ["—"]
            except Exception:
                headers_list = ["—"]

            c_a, c_b, c_p = st.columns(3)
            with c_a:
                st.selectbox(
                    "Столбец: Артикул",
                    headers_list,
                    key=f"ovr_art_{res['name']}",
                )
            with c_b:
                st.selectbox(
                    "Столбец: Бренд",
                    headers_list,
                    key=f"ovr_brand_{res['name']}",
                )
            with c_p:
                st.selectbox(
                    "Столбец: Цена",
                    headers_list,
                    key=f"ovr_price_{res['name']}",
                )
            st.caption(
                "После выбора нажмите кнопку **▶ Анализ** в сайдбаре слева повторно."
            )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 9. МЕТРИКИ (KPI DASHBOARD)
# ─────────────────────────────────────────────────────────────────────────────
if not df_final.empty:
    st.markdown('<div class="section-title">📊 Сводные метрики агрегатора</div>', unsafe_allow_html=True)

    total_unique = len(df_final)
    total_offers = int(df_final["Предложений"].sum()) if "Предложений" in df_final.columns else 0
    total_savings = df_final["Экономия_руб"].sum() if "Экономия_руб" in df_final.columns else 0
    avg_price = df_final["Цена"].mean()
    total_min_sum = df_final["Цена"].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔑 Уникальных SKU", f"{total_unique:,}")
    m2.metric("📊 Источников", f"{total_offers:,}", help="Сумма уникальных поставщиков по всем SKU")
    m3.metric("💰 Средняя мин. цена", f"{avg_price:,.0f} ₽")
    m4.metric(
        "💵 Сумма мин. цен",
        f"{total_min_sum:,.0f} ₽",
        help="Точная сумма минимальных цен по всем SKU — бюджет закупки",
    )
    m5.metric(
        "📉 Суммарная экономия",
        f"{total_savings:,.0f} ₽",
        help="Σ(макс−мин) по всем SKU",
    )

    st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 10. ТАБЛИЦА РЕЗУЛЬТАТОВ, АНАЛИЗ И ЭКСПОРТ
# ─────────────────────────────────────────────────────────────────────────────
if not df_final.empty:

    tab_table, tab_analysis, tab_sources = st.tabs(
        ["📋 Итоговый прайс", "📈 Анализ и графики", "🏢 По источникам"]
    )

    # ── TAB 1: ТАБЛИЦА ──
    with tab_table:
        st.markdown(
            '<div class="section-title">🏆 Итоговый прайс (минимальная цена + источник)</div>',
            unsafe_allow_html=True,
        )

        f_col1, f_col2, f_col3 = st.columns([3, 2, 2])
        with f_col1:
            search_q = st.text_input(
                "🔍 Поиск по артикулу, бренду или источнику",
                placeholder="Введите запрос...",
                label_visibility="collapsed",
            )
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
                df_view["Артикул"].str.lower().str.contains(q, na=False)
                | df_view["Бренд"].str.lower().str.contains(q, na=False)
                | df_view["Источник"].str.lower().str.contains(q, na=False)
            ]
        if sel_brand_val != "Все бренды":
            df_view = df_view[df_view["Бренд"] == sel_brand_val]
        if sel_source_val != "Все источники":
            df_view = df_view[df_view["Источник"] == sel_source_val]

        disp_cols = [
            "Артикул", "Бренд", "Цена", "Источник",
            "Предложений", "Количество", "Экономия_руб", "Экономия_%",
        ]
        disp_cols = [c for c in disp_cols if c in df_view.columns]

        # ── Экспорт (СВЕРХУ ТАБЛИЦЫ) ──
        st.markdown(
            '<div class="section-title" style="margin-top:0.8rem;">💾 Скачивание результата</div>',
            unsafe_allow_html=True,
        )

        # Выбор столбцов для выгрузки
        all_available_cols = df_view.columns.tolist()
        export_cols = st.multiselect(
            "Выберите столбцы для выгрузки",
            options=all_available_cols,
            default=[c for c in disp_cols if c in all_available_cols],
            help="Укажите, какие именно колонки должны попасть в итоговый Excel и CSV файл."
        )
        if not export_cols:
            export_cols = [c for c in ["Артикул", "Цена", "Источник"] if c in all_available_cols]
            st.caption("⚠️ Не выбрано ни одного столбца — будет выгружен базовый набор: Артикул, Цена, Источник.")
        else:
            st.caption(f"📊 В файл попадёт столбцов: {len(export_cols)}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        n_rows = len(df_view)
        export_status = st.empty()
        export_progress = st.empty()

        # Индикатор загрузки при формировании файлов
        export_status.markdown(
            f"""
            <div style="
                background: rgba(59,130,246,0.12);
                border: 1px solid rgba(96,165,250,0.35);
                border-radius: 12px;
                padding: 0.85rem 1.1rem;
                margin-bottom: 0.75rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            ">
              <div class="pf-spinner"></div>
              <div>
                <div style="color:#f4f4f5;font-weight:600;font-size:0.9rem;">
                  Формирование файлов для экспорта…
                </div>
                <div style="color:#93c5fd;font-size:0.78rem;margin-top:0.15rem;">
                  Обрабатываем {n_rows:,} строк · Excel + CSV
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        prog = export_progress.progress(0, text="Подготовка данных…")

        prog.progress(25, text="Формирование Excel (.xlsx)…")
        with st.spinner("⏳ Создаём Excel-файл…"):
            excel_bytes = to_excel_bytes(df_view[export_cols])

        prog.progress(70, text="Формирование CSV (.csv)…")
        with st.spinner("⏳ Создаём CSV-файл…"):
            csv_bytes = to_csv_bytes(df_view[export_cols])

        prog.progress(100, text="Готово!")
        excel_size = format_file_size(len(excel_bytes))
        csv_size = format_file_size(len(csv_bytes))

        export_progress.empty()
        export_status.markdown(
            f"""
            <div style="
                background: rgba(16,185,129,0.12);
                border: 1px solid rgba(16,185,129,0.35);
                border-radius: 12px;
                padding: 0.75rem 1.1rem;
                margin-bottom: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 0.5rem;
            ">
              <div style="display:flex;align-items:center;gap:0.6rem;">
                <span style="font-size:1.1rem;">✅</span>
                <div>
                  <div style="color:#6ee7b7;font-weight:600;font-size:0.88rem;">
                    Файлы готовы к скачиванию
                  </div>
                  <div style="color:#93c5fd;font-size:0.75rem;margin-top:0.1rem;">
                    {n_rows:,} строк · Excel {excel_size} · CSV {csv_size}
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        dl_c1, dl_c2 = st.columns(2)
        with dl_c1:
            st.download_button(
                label=f"📗 Скачать Excel (.xlsx) · {excel_size}",
                data=excel_bytes,
                file_name=f"price_fusion_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"dl_xlsx_{timestamp}_{n_rows}",
            )
        with dl_c2:
            st.download_button(
                label=f"📄 Скачать CSV (.csv) · {csv_size}",
                data=csv_bytes,
                file_name=f"price_fusion_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"dl_csv_{timestamp}_{n_rows}",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── ТАБЛИЦА ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА ──
        st.dataframe(
            df_view[disp_cols],
            use_container_width=True,
            height=500,
            hide_index=True,
            column_config={
                "Артикул": st.column_config.TextColumn("🔑 Артикул", width="medium"),
                "Бренд": st.column_config.TextColumn("🏷 Бренд", width="medium"),
                "Цена": st.column_config.NumberColumn("💰 Мин. цена (₽)", format="%.2f ₽", width="small"),
                "Источник": st.column_config.TextColumn("📁 Источник (Прайс)", width="large"),
                "Предложений": st.column_config.NumberColumn(
                    "📊 Источников", width="small",
                    help="Кол-во уникальных поставщиков",
                ),
                "Количество": st.column_config.NumberColumn(
                    "🔢 Кол-во строк", width="small",
                    help="Всего строк с этим артикулом во всех загруженных прайсах (включая дубли)",
                ),
                "Экономия_руб": st.column_config.NumberColumn("💚 Экономия (₽)", format="%.2f ₽", width="small"),
                "Экономия_%": st.column_config.NumberColumn("📉 Экономия (%)", format="%.1f%%", width="small"),
            },
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
            hist_df = pd.DataFrame(
                {
                    "Диапазон": [str(i.mid.round(0)) for i in hist.index],
                    "Кол-во": hist.values,
                }
            )
            st.bar_chart(hist_df.set_index("Диапазон"), color="#60a5fa", height=300)

        with gc2:
            st.markdown("**Топ-10 брендов по числу SKU**")
            top_brands = (
                df_final[df_final["Бренд"] != "—"]["Бренд"]
                .value_counts()
                .head(10)
                .reset_index()
            )
            top_brands.columns = ["Бренд", "Артикулов"]
            st.bar_chart(top_brands.set_index("Бренд"), color="#34d399", height=300)

    # ── TAB 3: ПО ИСТОЧНИКАМ ──
    with tab_sources:
        st.markdown('<div class="section-title">🏢 Статистика по источникам (поставщикам)</div>', unsafe_allow_html=True)

        src_stats = (
            df_final.groupby("Источник")
            .agg(
                Побед=("Источник", "count"),
                Мин_цена=("Цена", "min"),
                Средн_цена=("Цена", "mean"),
                Макс_цена=("Цена", "max"),
                Сумма_мин=("Цена", "sum"),
                Экономия=("Экономия_руб", "sum"),
            )
            .round(2)
            .sort_values("Побед", ascending=False)
            .reset_index()
        )

        st.dataframe(
            src_stats,
            use_container_width=True,
            height=380,
            hide_index=True,
            column_config={
                "Источник": st.column_config.TextColumn("📁 Источник", width="large"),
                "Побед": st.column_config.NumberColumn(
                    "🏆 Побед (мин. цена)",
                    help="Кол-во позиций, где этот прайс дал самую дешёвую цену",
                ),
                "Мин_цена": st.column_config.NumberColumn("Min ₽", format="%.0f ₽"),
                "Средн_цена": st.column_config.NumberColumn("Ср. ₽", format="%.0f ₽"),
                "Макс_цена": st.column_config.NumberColumn("Max ₽", format="%.0f ₽"),
                "Сумма_мин": st.column_config.NumberColumn(
                    "💵 Сумма мин. цен ₽",
                    format="%.0f ₽",
                    help="Сумма минимальных цен по позициям этого источника",
                ),
                "Экономия": st.column_config.NumberColumn("💚 Экономия ₽", format="%.0f ₽"),
            },
        )

# ─────────────────────────────────────────────────────────────────────────────
# 11. FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <hr>
    <div style="text-align:center;font-size:0.75rem;color:#93c5fd;padding:1rem 0">
      ⚡ <b>Price.Fusion</b> &nbsp;·&nbsp; Монолитный Streamlit App &nbsp;·&nbsp;
      Все функции и стили в одном файле <code>app.py</code>
    </div>
    """,
    unsafe_allow_html=True,
)
