import React, { useState, useRef, useMemo } from 'react';
import * as XLSX from 'xlsx';
import confetti from 'canvas-confetti';
import { 
  FolderOpen, 
  FileSpreadsheet, 
  Download, 
  Search, 
  ArrowUpDown, 
  Trash2, 
  Sparkles, 
  CheckCircle, 
  AlertTriangle, 
  Info,
  Layers,
  TrendingDown,
  Activity,
  FileCode,
  Copy,
  Database
} from 'lucide-react';

// ======================= TYPES & INTERFACES =======================
interface ParsedRow {
  article: string;
  brand: string;
  price: number;
  source: string;
}

interface FileStatus {
  name: string;
  size: string;
  status: 'success' | 'warning' | 'error';
  message: string;
  detectedColumns: {
    article: string | null;
    brand: string | null;
    price: string | null;
  };
  rowCount: number;
}

interface AggregatedResult {
  article: string;
  brand: string;
  price: number;
  source: string;
  allPrices: { source: string; price: number; brand: string }[];
}

export default function App() {
  // ======================= STATE =======================
  const [files, setFiles] = useState<FileStatus[]>([]);
  const [parsedData, setParsedData] = useState<ParsedRow[]>([]);
  const [simulatedPath, setSimulatedPath] = useState<string>('C:\\Users\\Manager\\Downloads\\Prices_2026');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, setItemsPerPage] = useState<number>(15);
  const [sortField, setSortField] = useState<keyof ParsedRow>('price');
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  // ======================= COLUMN DETECTOR KEYWORDS =======================
  const ARTICLE_KEYWORDS = ['артикул', 'арт', 'sku', 'код', 'номер', 'article', 'id', 'товар', 'кодтовара'];
  const BRAND_KEYWORDS = ['бренд', 'brand', 'производитель', 'произв', 'изготовитель', 'make', 'марка'];
  const PRICE_KEYWORDS = ['цена', 'price', 'стоимость', 'cost', 'закуп', 'сумма', 'ценазакупа', 'ррц'];

  // Helper helper to clean up price string and return number
  const cleanPrice = (val: any): number | null => {
    if (val === undefined || val === null) return null;
    if (typeof val === 'number') return isNaN(val) ? null : val;
    
    let s = String(val).trim().replace(/\s/g, '').replace(/\u00a0/g, '');
    if (!s) return null;
    
    // Replace comma with dot if it's acting as a decimal separator
    // If we have both commas and dots: e.g. 1,250.50 -> strip commas, keep dot
    if (s.includes(',') && s.includes('.')) {
      s = s.replace(/,/g, '');
    } else if (s.includes(',')) {
      // If only comma, check if it's decimal or thousands. E.g. "1250,50" -> "1250.50"
      const parts = s.split(',');
      if (parts[parts.length - 1].length <= 2) {
        s = s.replace(',', '.');
      } else {
        s = s.replace(/,/g, '');
      }
    }
    
    // Strip everything except numbers, dots, and minus
    s = s.replace(/[^\d.-]/g, '');
    const num = parseFloat(s);
    return isNaN(num) ? null : num;
  };

  // Helper helper to detect matching columns
  const detectColumn = (headers: string[], keywords: string[]): string | null => {
    for (const header of headers) {
      const hLower = header.toString().trim().toLowerCase();
      for (const kw of keywords) {
        if (hLower === kw || hLower.includes(kw)) {
          return header;
        }
      }
    }
    return null;
  };

  // Format file size
  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // ======================= FILE PROCESSING LOGIC =======================
  const handleFiles = async (fileList: FileList | File[]) => {
    setIsProcessing(true);
    const newFilesStatus: FileStatus[] = [];
    const newRows: ParsedRow[] = [];

    // Filter valid formats
    const validFiles = Array.from(fileList).filter(f => 
      f.name.endsWith('.xlsx') || 
      f.name.endsWith('.xls') || 
      f.name.endsWith('.csv')
    );

    if (validFiles.length === 0) {
      setIsProcessing(false);
      alert('Не найдено поддерживаемых файлов (.xlsx, .xls, .csv)');
      return;
    }

    for (const file of validFiles) {
      const reader = new FileReader();
      const fileNameWithoutExt = file.name.replace(/\.[^/.]+$/, "");

      try {
        const data = await new Promise<ArrayBuffer>((resolve, reject) => {
          reader.onload = (e) => {
            if (e.target?.result instanceof ArrayBuffer) {
              resolve(e.target.result);
            } else {
              reject(new Error('Не удалось прочитать файл'));
            }
          };
          reader.onerror = () => reject(new Error('Ошибка чтения'));
          reader.readAsArrayBuffer(file);
        });

        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        
        // Convert sheet to json matrix (raw rows)
        const rawJson: any[][] = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        if (rawJson.length === 0) {
          newFilesStatus.push({
            name: file.name,
            size: formatSize(file.size),
            status: 'warning',
            message: 'Файл пуст',
            detectedColumns: { article: null, brand: null, price: null },
            rowCount: 0
          });
          continue;
        }

        // Find headers (usually the first row with several columns, or search the first 5 rows)
        let headerRowIndex = 0;
        let headers: string[] = [];
        for (let r = 0; r < Math.min(10, rawJson.length); r++) {
          const row = rawJson[r];
          if (row && row.length > 1) {
            const hasKeywords = row.some(cell => {
              if (!cell) return false;
              const cellStr = String(cell).toLowerCase();
              return ARTICLE_KEYWORDS.some(k => cellStr.includes(k)) || 
                     PRICE_KEYWORDS.some(k => cellStr.includes(k));
            });
            if (hasKeywords) {
              headerRowIndex = r;
              headers = row.map(h => String(h || '').trim());
              break;
            }
          }
        }

        // Fallback to first row if no keywords detected
        if (headers.length === 0) {
          headers = (rawJson[0] || []).map(h => String(h || '').trim());
        }

        const colArt = detectColumn(headers, ARTICLE_KEYWORDS);
        const colBrand = detectColumn(headers, BRAND_KEYWORDS);
        const colPrice = detectColumn(headers, PRICE_KEYWORDS);

        if (!colArt || !colPrice) {
          // Attempt numeric auto-detect for price if not found
          let fallbackPriceCol = colPrice;
          if (!colPrice && rawJson.length > headerRowIndex + 1) {
            // Check headers that have numeric cells down below
            const nextRow = rawJson[headerRowIndex + 1];
            for (let c = 0; c < nextRow.length; c++) {
              const val = cleanPrice(nextRow[c]);
              if (val !== null && val > 0 && headers[c]) {
                fallbackPriceCol = headers[c];
                break;
              }
            }
          }

          if (!colArt || !fallbackPriceCol) {
            newFilesStatus.push({
              name: file.name,
              size: formatSize(file.size),
              status: 'error',
              message: `Не найдены обязательные столбцы: ${!colArt ? 'Артикул' : ''} ${!colPrice ? 'Цена' : ''}`,
              detectedColumns: { article: colArt, brand: colBrand, price: fallbackPriceCol },
              rowCount: 0
            });
            continue;
          } else {
            // Used fallback price
            // Let's bind it
          }
        }

        const artIndex = headers.indexOf(colArt);
        const brandIndex = colBrand ? headers.indexOf(colBrand) : -1;
        const priceIndex = headers.indexOf(colPrice || '');

        let successRowsCount = 0;
        // Parse rows starting from headerRowIndex + 1
        for (let r = headerRowIndex + 1; r < rawJson.length; r++) {
          const row = rawJson[r];
          if (!row || row.length === 0) continue;

          const rawArt = row[artIndex];
          if (rawArt === undefined || rawArt === null || String(rawArt).trim() === '') continue;
          
          const art = String(rawArt).trim();
          const rawPrice = row[priceIndex];
          const price = cleanPrice(rawPrice);

          if (price === null || price <= 0) continue;

          const brand = brandIndex !== -1 && row[brandIndex] !== undefined && row[brandIndex] !== null 
            ? String(row[brandIndex]).trim() 
            : '—';

          newRows.push({
            article: art,
            brand: brand,
            price: price,
            source: fileNameWithoutExt
          });
          successRowsCount++;
        }

        newFilesStatus.push({
          name: file.name,
          size: formatSize(file.size),
          status: 'success',
          message: `Обработано строк: ${successRowsCount}`,
          detectedColumns: { article: colArt, brand: colBrand, price: colPrice || 'Автоопределение' },
          rowCount: successRowsCount
        });

      } catch (err: any) {
        newFilesStatus.push({
          name: file.name,
          size: formatSize(file.size),
          status: 'error',
          message: `Ошибка чтения: ${err.message || err}`,
          detectedColumns: { article: null, brand: null, price: null },
          rowCount: 0
        });
      }
    }

    setFiles(prev => [...prev, ...newFilesStatus]);
    setParsedData(prev => [...prev, ...newRows]);
    setIsProcessing(false);

    // Boom! 🎉 trigger confetti for success
    if (newRows.length > 0) {
      confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#667eea', '#764ba2', '#10b981']
      });
    }
  };

  // ======================= GENERATE DEMO DATA =======================
  const handleLoadDemo = () => {
    // Generate simulated supplier databases
    const supplier1Rows: ParsedRow[] = [
      { article: 'IP15-128-BLK', brand: 'Apple', price: 78900, source: 'Прайс_Марвел_Дистрибьюция' },
      { article: 'IP15-256-WHT', brand: 'Apple', price: 89900, source: 'Прайс_Марвел_Дистрибьюция' },
      { article: 'SAM-S24-256-GRY', brand: 'Samsung', price: 69900, source: 'Прайс_Марвел_Дистрибьюция' },
      { article: 'XIA-14-512-BLK', brand: 'Xiaomi', price: 54900, source: 'Прайс_Марвел_Дистрибьюция' },
      { article: 'SONY-WH1000-XM5', brand: 'Sony', price: 34500, source: 'Прайс_Марвел_Дистрибьюция' },
      { article: 'MAC-AIR-M3-16', brand: 'Apple', price: 142000, source: 'Прайс_Марвел_Дистрибьюция' },
    ];

    const supplier2Rows: ParsedRow[] = [
      { article: 'IP15-128-BLK', brand: 'Apple LLC', price: 76500, source: 'ОптТорг_Смартфоны_Юг' }, // Cheaper
      { article: 'IP15-256-WHT', brand: 'Apple', price: 91200, source: 'ОптТорг_Смартфоны_Юг' }, // Exp
      { article: 'SAM-S24-256-GRY', brand: 'Samsung Group', price: 67800, source: 'ОптТорг_Смартфоны_Юг' }, // Cheaper
      { article: 'XIA-14-512-BLK', brand: 'Xiaomi Corp', price: 56900, source: 'ОптТорг_Смартфоны_Юг' },
      { article: 'SONY-WH1000-XM5', brand: 'Sony', price: 32900, source: 'ОптТорг_Смартфоны_Юг' }, // Cheaper
      { article: 'DYSON-HS05-VIO', brand: 'Dyson', price: 47900, source: 'ОптТорг_Смартфоны_Юг' }, // Unique
    ];

    const supplier3Rows: ParsedRow[] = [
      { article: 'IP15-128-BLK', brand: 'Apple', price: 79000, source: 'Премиум_Импорт_Москва' },
      { article: 'IP15-256-WHT', brand: 'Apple', price: 88500, source: 'Премиум_Импорт_Москва' }, // Cheaper
      { article: 'SAM-S24-256-GRY', brand: 'Samsung', price: 71000, source: 'Премиум_Импорт_Москва' },
      { article: 'XIA-14-512-BLK', brand: 'Xiaomi', price: 52900, source: 'Премиум_Импорт_Москва' }, // Cheaper
      { article: 'MAC-AIR-M3-16', brand: 'Apple Store', price: 139000, source: 'Премиум_Импорт_Москва' }, // Cheaper
      { article: 'DYSON-HS05-VIO', brand: 'Dyson Airwrap', price: 49900, source: 'Премиум_Импорт_Москва' },
      { article: 'PS5-SLIM-1TB', brand: 'Sony Interactive', price: 48900, source: 'Премиум_Импорт_Москва' }, // Unique
    ];

    setFiles([
      {
        name: 'Прайс_Марвел_Дистрибьюция.xlsx',
        size: '142.5 KB',
        status: 'success',
        message: 'Обработано строк: 6',
        detectedColumns: { article: 'Артикул товара', brand: 'Производитель', price: 'Цена (руб.)' },
        rowCount: 6
      },
      {
        name: 'ОптТорг_Смартфоны_Юг.csv',
        size: '88.1 KB',
        status: 'success',
        message: 'Обработано строк: 6',
        detectedColumns: { article: 'Код SKU', brand: 'Бренд', price: 'Цена закупки' },
        rowCount: 6
      },
      {
        name: 'Премиум_Импорт_Москва.xls',
        size: '1.2 MB',
        status: 'success',
        message: 'Обработано строк: 7',
        detectedColumns: { article: 'Артикул', brand: 'Бренд', price: 'Цена со скидкой' },
        rowCount: 7
      }
    ]);

    setParsedData([...supplier1Rows, ...supplier2Rows, ...supplier3Rows]);
    
    confetti({
      particleCount: 100,
      spread: 60,
      origin: { y: 0.6 }
    });
  };

  // ======================= AGGREGATION ALGORITHM =======================
  const aggregatedResults = useMemo(() => {
    const articleMap = new Map<string, AggregatedResult>();

    parsedData.forEach(row => {
      const normArt = row.article.toUpperCase().trim();
      
      const existing = articleMap.get(normArt);
      const rowPrice = row.price;
      
      if (!existing) {
        articleMap.set(normArt, {
          article: row.article, // preserve original casing
          brand: row.brand,
          price: rowPrice,
          source: row.source,
          allPrices: [{ source: row.source, price: rowPrice, brand: row.brand }]
        });
      } else {
        existing.allPrices.push({ source: row.source, price: rowPrice, brand: row.brand });
        
        // If we found a cheaper price, update top level
        if (rowPrice < existing.price) {
          existing.price = rowPrice;
          existing.source = row.source;
          // Only update brand if it was empty/default and the new one is better
          if (row.brand && row.brand !== '—') {
            existing.brand = row.brand;
          }
        } else if (existing.brand === '—' && row.brand && row.brand !== '—') {
          // If existing brand is empty but the more expensive offer has a brand, update it
          existing.brand = row.brand;
        }
      }
    });

    return Array.from(articleMap.values());
  }, [parsedData]);

  // ======================= FILTER & SORT & PAGINATION =======================
  const filteredAndSortedResults = useMemo(() => {
    let result = [...aggregatedResults];

    // Filter by query
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(item => 
        item.article.toLowerCase().includes(q) || 
        item.brand.toLowerCase().includes(q) || 
        item.source.toLowerCase().includes(q)
      );
    }

    // Sort
    result.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (typeof valA === 'string') {
        return sortAsc 
          ? (valA as string).localeCompare(valB as string) 
          : (valB as string).localeCompare(valA as string);
      } else if (typeof valA === 'number') {
        return sortAsc 
          ? (valA as number) - (valB as number) 
          : (valB as number) - (valA as number);
      }
      return 0;
    });

    return result;
  }, [aggregatedResults, searchQuery, sortField, sortAsc]);

  // Paginated chunk
  const paginatedResults = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAndSortedResults.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAndSortedResults, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredAndSortedResults.length / itemsPerPage) || 1;

  // Watch query changes to reset page
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, itemsPerPage]);

  const handleSort = (field: keyof ParsedRow) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  // ======================= DOWNLOAD EXPORTERS =======================
  const downloadExcel = () => {
    if (aggregatedResults.length === 0) return;

    // Prepare custom formatted data
    const exportData = aggregatedResults.map(item => ({
      'Артикул': item.article,
      'Бренд': item.brand,
      'Цена (Самая низкая)': item.price,
      'Источник (Поставщик)': item.source,
      'Всего предложений': item.allPrices.length
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    
    // Auto fit column widths
    const maxLens = Object.keys(exportData[0]).map(key => {
      const colKey = key as keyof typeof exportData[0];
      const lengths = exportData.map(row => String(row[colKey]).length);
      lengths.push(key.length);
      return { wch: Math.max(...lengths) + 3 };
    });
    worksheet['!cols'] = maxLens;

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Минимальные Цены");
    
    XLSX.writeFile(workbook, "Самые_дешевые_предложения.xlsx");
    
    confetti({
      particleCount: 80,
      angle: 60,
      spread: 55,
      origin: { x: 0 }
    });
    confetti({
      particleCount: 80,
      angle: 120,
      spread: 55,
      origin: { x: 1 }
    });
  };

  const downloadCSV = () => {
    if (aggregatedResults.length === 0) return;

    const headers = ['Артикул', 'Бренд', 'Цена', 'Источник'];
    const rows = aggregatedResults.map(item => [
      `"${item.article.replace(/"/g, '""')}"`,
      `"${item.brand.replace(/"/g, '""')}"`,
      item.price,
      `"${item.source.replace(/"/g, '""')}"`
    ]);

    const csvContent = "\uFEFF" + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "Самые_дешевые_предложения.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const copyToClipboard = () => {
    if (aggregatedResults.length === 0) return;

    const headers = ['Артикул', 'Бренд', 'Цена', 'Источник'].join('\t');
    const rows = aggregatedResults.map(item => [
      item.article,
      item.brand,
      item.price,
      item.source
    ].join('\t')).join('\n');

    navigator.clipboard.writeText(headers + '\n' + rows);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const clearData = () => {
    setFiles([]);
    setParsedData([]);
    setCurrentPage(1);
  };

  // Calculate global savings metrics
  const globalMetrics = useMemo(() => {
    let savedTotal = 0;
    let competingItemsCount = 0;

    aggregatedResults.forEach(item => {
      if (item.allPrices.length > 1) {
        const prices = item.allPrices.map(p => p.price);
        const maxPrice = Math.max(...prices);
        const minPrice = item.price;
        savedTotal += (maxPrice - minPrice);
        competingItemsCount++;
      }
    });

    const totalArticles = aggregatedResults.length;
    const avgPrice = totalArticles > 0 ? aggregatedResults.reduce((acc, curr) => acc + curr.price, 0) / totalArticles : 0;

    return {
      savedTotal,
      competingItemsCount,
      avgPrice
    };
  }, [aggregatedResults]);

  return (
    <div className="min-h-screen bg-[#0e1117] text-[#e4e4e7] font-sans selection:bg-[#667eea]/30 selection:text-white flex flex-col md:flex-row">
      
      {/* ======================= SIDEBAR (STREAMLIT STYLE) ======================= */}
      <aside className="w-full md:w-[340px] bg-[#1a1d24] border-b md:border-b-0 md:border-r border-[#2a2d35] p-6 flex flex-col gap-6 shrink-0">
        
        {/* Sidebar Brand Logo */}
        <div className="flex items-center gap-3 pb-4 border-b border-[#2a2d35]">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#667eea] to-[#764ba2] flex items-center justify-center shadow-lg shadow-[#667eea]/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide leading-tight">Прайс Анализатор</h1>
            <p className="text-[11px] text-[#8b8fa3] font-mono">Streamlit Premium v1.4.2</p>
          </div>
        </div>

        {/* Directory Scanner Simulator input */}
        <div>
          <label className="block text-xs font-semibold text-[#8b8fa3] uppercase tracking-wider mb-2">
            Выбранная папка (Путь)
          </label>
          <div className="relative">
            <input 
              type="text" 
              value={simulatedPath}
              onChange={(e) => setSimulatedPath(e.target.value)}
              placeholder="C:\Users\Documents\Prices"
              className="w-full bg-[#0e1117] border border-[#2a2d35] rounded-lg px-3 py-2 text-sm text-[#e4e4e7] focus:outline-none focus:border-[#667eea] transition"
            />
            <div className="absolute right-2 top-2.5">
              <span className="w-2 h-2 rounded-full bg-[#10b981] inline-block animate-pulse" title="Система подключена"></span>
            </div>
          </div>
          <p className="text-[11px] text-[#6b7280] mt-1.5 leading-relaxed">
            Виртуальный путь к локальной папке с прайс-листами поставщиков.
          </p>
        </div>

        {/* Directory Scan Controls */}
        <div className="bg-[#0e1117]/50 rounded-xl p-4 border border-[#2a2d35] flex flex-col gap-3">
          <span className="text-xs font-semibold text-white/90 flex items-center gap-1.5">
            <FolderOpen className="w-3.5 h-3.5 text-[#667eea]" /> Выбрать источник
          </span>
          
          <button 
            onClick={() => folderInputRef.current?.click()}
            className="w-full py-2 px-3 bg-[#2a2d35]/60 hover:bg-[#2a2d35] text-xs font-medium text-white rounded-lg border border-[#3a3d45] transition flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>📁 Выбрать всю папку</span>
          </button>

          <button 
            onClick={() => fileInputRef.current?.click()}
            className="w-full py-2 px-3 bg-[#2a2d35]/60 hover:bg-[#2a2d35] text-xs font-medium text-white rounded-lg border border-[#3a3d45] transition flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>📄 Выбрать файлы</span>
          </button>

          {/* Hidden inputs */}
          <input 
            type="file" 
            ref={folderInputRef}
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
            className="hidden"
            // @ts-ignore
            webkitdirectory="" 
            directory="" 
            multiple
          />
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
            className="hidden"
            accept=".xlsx, .xls, .csv"
            multiple
          />

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-[#2a2d35]"></div>
            <span className="flex-shrink mx-2 text-[10px] text-[#6b7280] uppercase tracking-widest">ИЛИ</span>
            <div className="flex-grow border-t border-[#2a2d35]"></div>
          </div>

          <button
            onClick={handleLoadDemo}
            className="w-full py-2.5 px-3 bg-gradient-to-r from-[#667eea]/20 to-[#764ba2]/20 hover:from-[#667eea]/30 hover:to-[#764ba2]/30 text-xs font-semibold text-[#a5b4fc] rounded-lg border border-[#667eea]/40 transition flex items-center justify-center gap-2"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#a5b4fc] animate-pulse" />
            <span>Загрузить демо-данные</span>
          </button>
        </div>

        {/* Auto Detect Rules */}
        <div className="mt-auto pt-4 border-t border-[#2a2d35]">
          <span className="text-[11px] font-semibold text-[#8b8fa3] uppercase tracking-wider block mb-2">
            🎯 Алгоритм автоопределения колонок
          </span>
          <div className="space-y-2 text-[11px] text-[#8b8fa3] leading-relaxed">
            <p>
              <strong className="text-[#a5b4fc]">Артикул:</strong> поиск совпадений по <em>"артикул", "арт", "sku", "код", "кодтовара", "id"</em>.
            </p>
            <p>
              <strong className="text-[#a5b4fc]">Бренд:</strong> поиск по <em>"бренд", "brand", "производитель", "марка"</em>.
            </p>
            <p>
              <strong className="text-[#a5b4fc]">Цена:</strong> поиск по <em>"цена", "price", "стоимость", "cost", "закуп"</em>. При отсутствии выбирает первый численный столбец.
            </p>
          </div>
        </div>

        {/* Clear Data button */}
        {files.length > 0 && (
          <button
            onClick={clearData}
            className="w-full py-2 bg-red-500/10 hover:bg-red-500/20 text-xs font-medium text-red-400 rounded-lg border border-red-500/20 transition flex items-center justify-center gap-2"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Очистить все данные</span>
          </button>
        )}

      </aside>

      {/* ======================= MAIN APP AREA ======================= */}
      <main className="flex-grow p-6 md:p-8 flex flex-col gap-6 max-w-7xl mx-auto w-full overflow-x-hidden relative">
        
        {/* Processing Spinner Overlay */}
        {isProcessing && (
          <div className="absolute inset-0 bg-[#0e1117]/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-4">
            <div className="w-12 h-12 rounded-full border-4 border-t-[#667eea] border-r-transparent border-[#2a2d35] animate-spin"></div>
            <p className="text-sm font-semibold text-white">Интеллектуальный парсинг и сопоставление прайсов...</p>
            <p className="text-xs text-[#8b8fa3]">Поиск цен, определение брендов и удаление дубликатов</p>
          </div>
        )}

        {/* Premium Header Banner */}
        <header className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#1e1b4b] via-[#1a1c2e] to-[#0f172a] border border-[#2a2d35] p-6 md:p-8 shadow-xl shadow-[#000000]/30">
          <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-[#667eea] opacity-[0.04] blur-[80px] rounded-full -mr-32 -mt-32"></div>
          <div className="absolute bottom-0 left-0 w-[200px] h-[200px] bg-[#764ba2] opacity-[0.04] blur-[60px] rounded-full -ml-20 -mb-20"></div>

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#667eea]/10 border border-[#667eea]/30 text-xs font-medium text-[#a5b4fc] mb-3">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Мгновенное сопоставление прайс-листов</span>
              </div>
              <h1 className="text-2xl md:text-3.5xl font-extrabold text-white tracking-tight leading-none mb-2">
                Анализ цен по Артикулу и Бренду
              </h1>
              <p className="text-sm md:text-base text-[#8b8fa3] max-w-2xl leading-relaxed">
                Загрузите папку с прайс-листами поставщиков. Наш интеллектуальный парсер автоматически сопоставит артикулы, очистит числовые форматы валют, найдет самое выгодное (дешевое) предложение и зафиксирует его источник.
              </p>
            </div>
          </div>
        </header>

        {/* Step-by-Step user visual helper when empty */}
        {files.length === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-4">
            <div className="bg-[#1a1d24] border border-[#2a2d35] rounded-xl p-5 hover:border-[#667eea]/40 transition duration-300">
              <div className="w-10 h-10 rounded-lg bg-[#667eea]/10 border border-[#667eea]/30 flex items-center justify-center text-lg font-bold text-[#a5b4fc] mb-4">1</div>
              <h3 className="text-base font-semibold text-white mb-2">Подготовьте прайс-листы</h3>
              <p className="text-xs text-[#8b8fa3] leading-relaxed">
                Сложите Excel-файлы или CSV в одну папку. Документы могут иметь разные структуры колонок и отличающиеся наименования столбцов.
              </p>
            </div>
            <div className="bg-[#1a1d24] border border-[#2a2d35] rounded-xl p-5 hover:border-[#667eea]/40 transition duration-300">
              <div className="w-10 h-10 rounded-lg bg-[#764ba2]/10 border border-[#764ba2]/30 flex items-center justify-center text-lg font-bold text-[#c7d2fe] mb-4">2</div>
              <h3 className="text-base font-semibold text-white mb-2">Загрузите в систему</h3>
              <p className="text-xs text-[#8b8fa3] leading-relaxed">
                Укажите путь к папке в сайдбаре или нажмите <span className="text-[#a5b4fc] font-semibold">"Загрузить демо-данные"</span>, чтобы мгновенно увидеть результат на подготовленном кейсе поставщиков электроники.
              </p>
            </div>
            <div className="bg-[#1a1d24] border border-[#2a2d35] rounded-xl p-5 hover:border-[#667eea]/40 transition duration-300">
              <div className="w-10 h-10 rounded-lg bg-[#10b981]/10 border border-[#10b981]/30 flex items-center justify-center text-lg font-bold text-emerald-300 mb-4">3</div>
              <h3 className="text-base font-semibold text-white mb-2">Скачайте отчет</h3>
              <p className="text-xs text-[#8b8fa3] leading-relaxed">
                Экспортируйте консолидированную таблицу с найденной минимальной ценой и источником-поставщиком в один клик в формате .xlsx (Excel) или .csv!
              </p>
            </div>
          </div>
        )}

        {/* Dropzone Area / Drag and Drop (Alternative) */}
        {files.length === 0 && (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-[#2a2d35] hover:border-[#667eea] bg-[#1a1d24]/40 hover:bg-[#1a1d24]/80 rounded-2xl p-12 text-center cursor-pointer transition duration-300 group"
          >
            <div className="w-16 h-16 rounded-full bg-[#2a2d35] group-hover:bg-[#667eea]/10 group-hover:scale-110 transition duration-300 flex items-center justify-center mx-auto mb-4">
              <FolderOpen className="w-8 h-8 text-[#8b8fa3] group-hover:text-[#a5b4fc]" />
            </div>
            <h3 className="text-lg font-semibold text-white group-hover:text-[#a5b4fc] transition mb-1">
              Нажмите для выбора папки или нескольких прайс-листов
            </h3>
            <p className="text-xs text-[#8b8fa3] max-w-md mx-auto leading-relaxed">
              Поддерживаются файлы Excel (.xlsx, .xls) и таблицы CSV. Система автоматически найдет нужные колонки во всех файлах.
            </p>
          </div>
        )}

        {/* File Parser Status Section */}
        {files.length > 0 && (
          <section className="bg-[#1a1d24] border border-[#2a2d35] rounded-xl p-5">
            <h2 className="text-xs font-semibold text-[#8b8fa3] uppercase tracking-wider mb-4 flex items-center gap-2">
              <Database className="w-4 h-4 text-[#667eea]" /> Статус обработки источников в папке:
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {files.map((file, idx) => (
                <div 
                  key={idx} 
                  className={`p-3.5 rounded-xl border flex flex-col gap-2 transition ${
                    file.status === 'success' ? 'bg-emerald-500/5 border-emerald-500/20' :
                    file.status === 'warning' ? 'bg-amber-500/5 border-amber-500/20' :
                    'bg-rose-500/5 border-rose-500/20'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-semibold text-xs text-white truncate" title={file.name}>
                        {file.name}
                      </p>
                      <p className="text-[10px] text-[#6b7280]">{file.size}</p>
                    </div>
                    {file.status === 'success' ? (
                      <CheckCircle className="w-4.5 h-4.5 text-emerald-500 shrink-0" />
                    ) : (
                      <AlertTriangle className={`w-4.5 h-4.5 shrink-0 ${file.status === 'warning' ? 'text-amber-500' : 'text-rose-500'}`} />
                    )}
                  </div>

                  <div className="bg-[#0e1117]/60 rounded px-2 py-1.5 text-[10px] flex flex-wrap gap-x-3 gap-y-1">
                    <span className="text-[#8b8fa3]">
                      Арт: <b className={file.detectedColumns.article ? "text-[#a5b4fc]" : "text-rose-400"}>{file.detectedColumns.article ? '✅' : '❌'}</b>
                    </span>
                    <span className="text-[#8b8fa3]">
                      Бренд: <b className="text-amber-300">{file.detectedColumns.brand ? '✅' : '—'}</b>
                    </span>
                    <span className="text-[#8b8fa3]">
                      Цена: <b className={file.detectedColumns.price ? "text-emerald-400" : "text-rose-400"}>{file.detectedColumns.price ? '✅' : '❌'}</b>
                    </span>
                  </div>

                  <p className={`text-[11px] font-medium ${
                    file.status === 'success' ? 'text-emerald-400' :
                    file.status === 'warning' ? 'text-amber-400' :
                    'text-rose-400'
                  }`}>
                    {file.message}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Global Key Metrics Row */}
        {aggregatedResults.length > 0 && (
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            
            <div className="bg-gradient-to-tr from-[#1a1d24] to-[#16191f] border border-[#2a2d35] rounded-xl p-4 flex flex-col gap-1.5 relative overflow-hidden group">
              <div className="absolute right-3 top-3 opacity-10 group-hover:scale-110 transition duration-300">
                <Layers className="w-10 h-10 text-[#667eea]" />
              </div>
              <span className="text-xs text-[#8b8fa3] font-medium">Уникальных артикулов</span>
              <span className="text-2xl font-bold text-white tracking-tight">
                {aggregatedResults.length.toLocaleString('ru-RU')}
              </span>
              <span className="text-[10px] text-[#10b981] flex items-center gap-1">
                среди {parsedData.length} предложений
              </span>
            </div>

            <div className="bg-gradient-to-tr from-[#1a1d24] to-[#16191f] border border-[#2a2d35] rounded-xl p-4 flex flex-col gap-1.5 relative overflow-hidden group">
              <div className="absolute right-3 top-3 opacity-10 group-hover:scale-110 transition duration-300">
                <TrendingDown className="w-10 h-10 text-[#10b981]" />
              </div>
              <span className="text-xs text-[#8b8fa3] font-medium">Экономия на закупках</span>
              <span className="text-2xl font-bold text-[#10b981] tracking-tight">
                {globalMetrics.savedTotal > 0 ? `${globalMetrics.savedTotal.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽` : '—'}
              </span>
              <span className="text-[10px] text-[#8b8fa3]">
                по {globalMetrics.competingItemsCount} конкурирующим товарам
              </span>
            </div>

            <div className="bg-gradient-to-tr from-[#1a1d24] to-[#16191f] border border-[#2a2d35] rounded-xl p-4 flex flex-col gap-1.5 relative overflow-hidden group">
              <div className="absolute right-3 top-3 opacity-10 group-hover:scale-110 transition duration-300">
                <FileCode className="w-10 h-10 text-violet-400" />
              </div>
              <span className="text-xs text-[#8b8fa3] font-medium">Успешных источников</span>
              <span className="text-2xl font-bold text-violet-400 tracking-tight">
                {files.filter(f => f.status === 'success').length} / {files.length}
              </span>
              <span className="text-[10px] text-[#8b8fa3]">
                обработано без ошибок
              </span>
            </div>

            <div className="bg-gradient-to-tr from-[#1a1d24] to-[#16191f] border border-[#2a2d35] rounded-xl p-4 flex flex-col gap-1.5 relative overflow-hidden group">
              <div className="absolute right-3 top-3 opacity-10 group-hover:scale-110 transition duration-300">
                <Activity className="w-10 h-10 text-[#764ba2]" />
              </div>
              <span className="text-xs text-[#8b8fa3] font-medium">Средняя цена товара</span>
              <span className="text-2xl font-bold text-white tracking-tight">
                {globalMetrics.avgPrice.toLocaleString('ru-RU', { maximumFractionDigits: 1 })} ₽
              </span>
              <span className="text-[10px] text-[#8b8fa3]">
                выбранного по минимальному прайсу
              </span>
            </div>

          </section>
        )}

        {/* Aggregated Data View & Controls */}
        {aggregatedResults.length > 0 && (
          <section className="bg-[#1a1d24] border border-[#2a2d35] rounded-xl overflow-hidden flex flex-col gap-4 p-5">
            
            {/* Header + Actions row */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white tracking-tight">Результаты оптимизации</h2>
                <p className="text-xs text-[#8b8fa3]">Для каждого артикула выбрано самое дешевое предложение из прайс-листов папки</p>
              </div>

              {/* Action buttons (Downloaders) */}
              <div className="flex flex-wrap items-center gap-2">
                <button 
                  onClick={downloadExcel}
                  className="px-4 py-2 bg-[#10b981] hover:bg-[#059669] text-xs font-semibold text-white rounded-lg shadow-lg shadow-emerald-900/20 transition flex items-center gap-2 cursor-pointer"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>Скачать в Excel</span>
                </button>
                <button 
                  onClick={downloadCSV}
                  className="px-4 py-2 bg-[#667eea] hover:bg-[#5a6fd6] text-xs font-semibold text-white rounded-lg shadow-lg shadow-[#667eea]/20 transition flex items-center gap-2 cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  <span>Скачать в CSV</span>
                </button>
                <button 
                  onClick={copyToClipboard}
                  className="px-4 py-2 bg-[#2a2d35] hover:bg-[#343842] text-xs font-semibold text-[#d4d4d8] border border-[#3a3d45] rounded-lg transition flex items-center gap-2 cursor-pointer"
                >
                  {copied ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  <span>{copied ? 'Скопировано!' : 'Буфер (TSV)'}</span>
                </button>
              </div>
            </div>

            {/* Filter and limits */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#0e1117] p-3 rounded-lg border border-[#2a2d35]">
              
              {/* Search */}
              <div className="relative flex-grow max-w-md">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-[#6b7280]" />
                </div>
                <input
                  type="text"
                  placeholder="Поиск по артикулу, бренду или источнику..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="block w-full pl-9 pr-3 py-1.5 bg-[#1a1d24] border border-[#2a2d35] rounded-md text-xs text-white placeholder-[#6b7280] focus:outline-none focus:border-[#667eea] transition"
                />
              </div>

              {/* Items per page */}
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[11px] text-[#8b8fa3]">Показывать по:</span>
                <select
                  value={itemsPerPage}
                  onChange={(e) => setItemsPerPage(Number(e.target.value))}
                  className="bg-[#1a1d24] border border-[#2a2d35] rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-[#667eea]"
                >
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                  <option value={30}>30</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>

            {/* Main Interactive Table */}
            <div className="overflow-x-auto rounded-lg border border-[#2a2d35]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#2a2d35]/30 text-xs font-semibold text-[#8b8fa3] uppercase border-b border-[#2a2d35]">
                    <th 
                      onClick={() => handleSort('article')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition select-none"
                    >
                      <div className="flex items-center gap-1">
                        <span>Артикул</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th 
                      onClick={() => handleSort('brand')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition select-none"
                    >
                      <div className="flex items-center gap-1">
                        <span>Бренд</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th 
                      onClick={() => handleSort('price')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition select-none text-right"
                    >
                      <div className="flex items-center justify-end gap-1">
                        <span>Цена (минимальная)</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th 
                      onClick={() => handleSort('source')}
                      className="py-3 px-4 cursor-pointer hover:text-white transition select-none"
                    >
                      <div className="flex items-center gap-1">
                        <span>Название источника (Прайса)</span>
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                    <th className="py-3 px-4 text-center">Всего предложений</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2a2d35]/50 text-xs font-medium">
                  {paginatedResults.length > 0 ? (
                    paginatedResults.map((item, index) => {
                      // Determine savings for tooltip or small badge
                      let savings = null;
                      if (item.allPrices.length > 1) {
                        const prices = item.allPrices.map(p => p.price);
                        const maxPrice = Math.max(...prices);
                        if (maxPrice > item.price) {
                          savings = maxPrice - item.price;
                        }
                      }

                      return (
                        <tr key={index} className="hover:bg-[#2a2d35]/15 transition duration-150">
                          <td className="py-3 px-4 font-mono text-white text-[13px]">{item.article}</td>
                          <td className="py-3 px-4 text-[#d4d4d8]">{item.brand}</td>
                          <td className="py-3 px-4 text-right text-emerald-400 font-bold text-[13px]">
                            {item.price.toLocaleString('ru-RU', { minimumFractionDigits: 1 })} ₽
                            {savings !== null && (
                              <div className="text-[10px] text-emerald-500 font-medium leading-none mt-0.5" title="Экономия по сравнению с максимальным предложением">
                                -{savings.toLocaleString('ru-RU')} ₽
                              </div>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#2a2d35]/60 text-white/80 border border-[#3a3d45]">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#667eea]"></span>
                              <span className="truncate max-w-[180px]" title={item.source}>{item.source}</span>
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              item.allPrices.length > 1 
                                ? 'bg-[#667eea]/20 text-[#a5b4fc] border border-[#667eea]/30' 
                                : 'bg-zinc-800 text-zinc-400'
                            }`}>
                              {item.allPrices.length} {item.allPrices.length > 1 ? 'варианта' : 'вариант'}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-[#6b7280]">
                        Нет совпадений по вашему запросу. Попробуйте изменить фильтр.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-[#2a2d35]">
              <span className="text-[11px] text-[#8b8fa3]">
                Показано <b className="text-white">{Math.min(currentPage * itemsPerPage, filteredAndSortedResults.length)}</b> из <b className="text-white">{filteredAndSortedResults.length}</b> уникальных записей
              </span>

              <div className="flex items-center gap-1.5">
                <button
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  className="px-2.5 py-1 bg-[#2a2d35] hover:bg-[#343842] disabled:opacity-40 text-xs font-semibold rounded transition cursor-pointer"
                >
                  Назад
                </button>
                
                {Array.from({ length: totalPages }).map((_, idx) => {
                  const pNum = idx + 1;
                  // Show current page, and surrounding pages, plus first and last
                  const isNear = Math.abs(pNum - currentPage) <= 1;
                  const isFirstOrLast = pNum === 1 || pNum === totalPages;
                  
                  if (!isNear && !isFirstOrLast) {
                    if (pNum === 2 || pNum === totalPages - 1) {
                      return <span key={idx} className="text-[#6b7280] px-1 text-xs">...</span>;
                    }
                    return null;
                  }

                  return (
                    <button
                      key={idx}
                      onClick={() => setCurrentPage(pNum)}
                      className={`px-2.5 py-1 text-xs font-semibold rounded transition cursor-pointer ${
                        currentPage === pNum 
                          ? 'bg-[#667eea] text-white' 
                          : 'bg-[#2a2d35] hover:bg-[#343842] text-[#8b8fa3]'
                      }`}
                    >
                      {pNum}
                    </button>
                  );
                })}

                <button
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  className="px-2.5 py-1 bg-[#2a2d35] hover:bg-[#343842] disabled:opacity-40 text-xs font-semibold rounded transition cursor-pointer"
                >
                  Вперед
                </button>
              </div>
            </div>

          </section>
        )}

        {/* Informative Help Card / Features */}
        <section className="bg-[#1a1d24]/50 border border-[#2a2d35] rounded-xl p-5 flex gap-4">
          <Info className="w-6 h-6 text-[#667eea] shrink-0" />
          <div className="text-xs leading-relaxed text-[#8b8fa3]">
            <h4 className="font-bold text-white mb-1.5 text-sm">💡 Преимущества монолитного веб-приложения:</h4>
            <ul className="list-disc pl-4 space-y-1">
              <li><b>Конфиденциальность:</b> Ваши файлы обрабатываются на 100% локально на вашем компьютере. Данные не передаются в интернет и не сохраняются на серверах.</li>
              <li><b>Универсальное распознавание:</b> Автоматически очищаются некорректные символы рубля, разделители тысяч, пробелы в ценах, а также приводятся к единому формату буквенные обозначения артикулов.</li>
              <li><b>Дубликаты артикулов:</b> Приложение безошибочно сопоставляет несколько поставщиков и находит именно тот файл, который предлагает самую низкую цену для оптимизации вашей маржи.</li>
            </ul>
          </div>
        </section>

      </main>
    </div>
  );
}
