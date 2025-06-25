import pdfplumber
import camelot
from paddleocr import PaddleOCR, PPStructure
import pdf2image
import numpy as np
import pandas as pd
import re
import logging
from pathlib import Path
from collections import defaultdict
from io import StringIO

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('pdfplumber').setLevel(logging.ERROR)
logging.getLogger('pypdf').setLevel(logging.ERROR)

# 初始化 PaddleOCR 和 PPStructure
ocr = PaddleOCR(use_angle_cls=True, lang="ch", det_limit_side_len=1200, det_db_thresh=0.05, det_db_box_thresh=0.4, use_gpu=False)
table_engine = PPStructure(show_log=False, lang="ch", table_max_len=1500, det_limit_side_len=1200, det_db_thresh=0.05)

# 設置輸出目錄
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def clean_text(text):
    """清洗文字，移除亂碼和無意義內容，並修正常見錯字"""
    if not text:
        return None
    text = re.sub(r'\\(?:begin|end)\{.*?\}|\{.*?\}|\\hline', '', text)
    text = re.sub(r'[^\u4e00-\u9fff\w\s.,:;()%\-\$/]', '', text)
    text = re.sub(r'\b\d+[a-zA-Z]+\b|\b[a-zA-Z]+\d+\b', '', text)
    replacements = {
        '棣雜雜影': '積體電路', '讨䄪': '財務', '㭘': '報', '范基': '概況', '㥞准': '核准',
        '䇾': '證', '巽': '異', '秤析': '評析', '舆': '與', '撑': '撐', '説': '說', '扣果': '扣除',
        '體電路': '積體電路', '營业': '營業', '仟元': '千元', '約当': '約當', '財務報': '財務報告'
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    text = re.sub(r'\$\s*(\d+),(\d{3}),(\d{3})', r'$\1,\2,\3', text)
    text = re.sub(r'\$\s*(\d+,\d{3},\d{3},\d{3})', r'$\1', text)
    text = re.sub(r'\(\s*\$\s*([\d,]+)\s*\)', r'($\1)', text)
    text = re.sub(r'\s+', ' ', text.strip())
    return text if text and len(text) > 1 else None

def is_text_based_page(page):
    """檢查頁面是否為 text-based，根據文字密度和長度動態判斷"""
    try:
        text = page.extract_text()
        cleaned = clean_text(text)
        words = page.extract_words()
        text_density = len(words) / (page.width * page.height) if words else 0
        if cleaned and len(cleaned) > 50 and text_density > 0.0001:
            logging.info(f"頁面 {page.page_number} 文字密度 {text_density:.6f}，判為 text-based")
            return True
        logging.info(f"頁面 {page.page_number} 文字密度 {text_density:.6f}，判為 scanned")
        return False
    except Exception as e:
        logging.error(f"頁面 {page.page_number} 檢查文字失敗: {e}", exc_info=True)
        return False

def extract_text_with_format(page, exclude_bboxes):
    """提取文字段落，不添加標題標記"""
    try:
        md_content = []
        words = page.extract_words()
        if not words:
            return None

        y_threshold = 12
        current_paragraph = []
        last_y = None

        for word in words:
            x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
            if any(ex_x0 <= x1 and ex_x0 + ex_w >= x0 and ex_y0 <= y1 and ex_y0 + ex_h >= y0
                   for ex_x0, ex_y0, ex_w, ex_h in exclude_bboxes):
                continue

            text = word['text']
            if last_y is None or abs(y0 - last_y) < y_threshold:
                current_paragraph.append(text)
            else:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    cleaned = clean_text(paragraph_text)
                    if cleaned:
                        md_content.append(cleaned)
                current_paragraph = [text]
            last_y = y0

        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            cleaned = clean_text(paragraph_text)
            if cleaned:
                md_content.append(cleaned)

        return md_content if md_content else None
    except Exception as e:
        logging.error(f"頁面 {page.page_number} 提取文字失敗: {e}", exc_info=True)
        return None

def is_narrative_table(df):
    """檢查表格是否為叙述性文字而非數據表格"""
    text_content = ' '.join(df.astype(str).values.flatten())
    cleaned = clean_text(text_content)
    if not cleaned:
        return True
    if re.search(r'設立於|主要從事|公司沿革|股票自|營運據點', cleaned):
        return True
    numeric_ratio = sum(1 for cell in df.values.flatten() if re.match(r'^\d+%$|^\$\d+|^[\d,\.\(\)]+$', str(cell))) / (df.size or 1)
    return numeric_ratio < 0.2

def extract_table_with_camelot(page):
    """使用 camelot 提取文字表格，動態檢測列數並過濾叙述性文字"""
    try:
        tables = camelot.read_pdf(page.pdf.path, flavor='lattice', pages=str(page.page_number))
        if not tables:
            tables = camelot.read_pdf(page.pdf.path, flavor='stream', pages=str(page.page_number), columns=['10,100,200,300,400,500,600,700'])
        
        md_tables = []
        bboxes = []
        text_content = []
        for table in tables:
            df = table.df
            if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
                continue
            if is_narrative_table(df):
                text = '\n'.join(clean_text(' '.join(row)) for row in df.values if any(row))
                text_content.extend([t for t in text.split('\n') if t])
                continue
            md_tables.append(df.to_markdown(index=False))
            x0, y0, x1, y0 = table._bbox
            bboxes.append((x0, page.height - y0, x1 - x0, y0 - (page.height - y0)))
        return md_tables, bboxes, text_content
    except Exception as e:
        logging.error(f"頁面 {page.page_number} camelot 提取表格失敗: {e}", exc_info=True)
        return [], [], []

def extract_table_with_ppsstructure(image):
    """使用 PPStructure 提取表格（Fallback）"""
    try:
        layout = table_engine(image)
        md_tables = []
        bboxes = []
        for region in layout:
            if region['type'] == 'table':
                table_data = region.get('res', {}).get('cells', [])
                if table_data:
                    rows = []
                    for row in table_data:
                        row_text = [clean_text(cell.get('text', '')) for cell in row]
                        rows.append([t for t in row_text if t])
                    if rows:
                        df = pd.DataFrame(rows)
                        if df.empty or df.shape[0] < 2:
                            continue
                        md_tables.append(df.to_markdown(index=False))
                        x0, y0, x1, y1 = region['bbox']
                        bboxes.append((x0, y0, x1 - x0, y1 - y0))
        return md_tables, bboxes
    except Exception as e:
        logging.error(f"PPStructure 提取表格失敗: {e}", exc_info=True)
        return [], []

def pdf_to_image(pdf_path, page_num, resolution=300):
    """將 PDF 頁面轉為圖片"""
    try:
        images = pdf2image.convert_from_path(pdf_path, dpi=resolution, first_page=page_num + 1, last_page=page_num + 1)
        return np.array(images[0].convert("RGB"))
    except Exception as e:
        logging.error(f"頁面 {page_num + 1} 轉圖片失敗: {e}", exc_info=True)
        return None

def extract_table_with_ocr(image):
    """使用 PaddleOCR 重建表格"""
    try:
        result = ocr.ocr(image, cls=True)
        if not result or not result[0]:
            return None, None

        lines = [(line[0], line[1][0], line[1][1]) for line in result[0]]
        if not lines:
            return None, None

        y_coords = [line[0][0][1] for line in lines]
        x_coords = [line[0][0][0] for line in lines]
        text_heights = [line[0][2][1] - line[0][0][1] for line in lines]
        y_threshold = np.median(text_heights) * 1.05 if text_heights else 10
        x_threshold = np.median([line[0][2][0] - line[0][0][0] for line in lines]) * 0.5 if x_coords else 50
        y_groups = defaultdict(list)

        for (bbox, text, conf), y, x in zip(lines, y_coords, x_coords):
            y_key = round(y / y_threshold) * y_threshold
            cleaned = clean_text(text)
            if cleaned and conf > 0.85:
                y_groups[y_key].append((x, cleaned, bbox))

        titles = []
        y_keys = sorted(y_groups.keys())
        for y_key in y_keys[:3]:
            row = y_groups[y_key]
            row_text = ' '.join(item[1] for item in row)
            if re.match(r'^(單位|民國|公司及子公司|\d+年\d+月\d+日|至\d+月\d+日|現金流量表)', row_text):
                titles.append(row_text)
                del y_groups[y_key]

        table = []
        expected_cols = 8
        for y_key in sorted(y_groups.keys()):
            group = y_groups[y_key]
            x_positions = sorted([item[0] for item in group])
            x_groups = defaultdict(list)
            for x, text, bbox in group:
                x_key = min(x_positions, key=lambda xp: abs(xp - x))
                x_groups[x_key].append(text)
            row = []
            for x_pos in sorted(x_positions)[:expected_cols]:
                texts = x_groups.get(x_pos, [''])
                row.append(' '.join(texts))
            if row:
                table.append(row + [''] * (expected_cols - len(row)))

        if not table:
            return None, None

        df = pd.DataFrame(table)
        if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
            return None, None

        empty_ratio = df.isna().sum().sum() / (df.shape[0] * df.shape[1])
        if empty_ratio > 0.3:
            logging.warning(f"表格空欄位比例過高 ({empty_ratio:.2f})，建議使用 PPStructure")
            return None, None

        md_table = df.to_markdown(index=False)
        md_content = [f"{title}" for title in titles if title] + [md_table]
        logging.info(f"OCR 表格提取完成：{df.shape[0]} 行，{df.shape[1]} 列")
        return md_content, None
    except Exception as e:
        logging.error(f"OCR 提取表格失敗: {e}", exc_info=True)
        return None, None

def merge_cross_page_tables(tables):
    """合併跨頁表格並清理 nan"""
    if not tables:
        return tables
    merged = []
    current_table = None
    for table in tables:
        try:
            df = pd.read_csv(StringIO(table), sep='|', skipinitialspace=True)
            df = df.replace('', np.nan).dropna(how='all', axis=1).dropna(how='all', axis=0).fillna('')
            if df.empty or df.shape[0] < 2:
                continue
            if current_table is None:
                current_table = df
            else:
                if df.shape[1] == current_table.shape[1] and len(set(df.columns).intersection(current_table.columns)) > 0:
                    current_table = pd.concat([current_table, df], ignore_index=True)
                else:
                    merged.append(current_table.to_markdown(index=False))
                    current_table = df
        except Exception as e:
            logging.error(f"合併表格失敗: {e}", exc_info=True)
            merged.append(table)
    if current_table is not None:
        merged.append(current_table.to_markdown(index=False))
    return merged

def process_pdf(pdf_path, output_md_path):
    """處理完整 PDF，提取所有頁面內容並優化輸出格式"""
    md_content = []
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            logging.info(f"處理頁面 {page.page_number}")

            if is_text_based_page(page):
                md_tables, table_bboxes, text_content = extract_table_with_camelot(page)
                if not md_tables and not text_content:
                    page_image = pdf_to_image(pdf_path, page_num)
                    if page_image is not None:
                        md_tables, table_bboxes = extract_table_with_ppsstructure(page_image)
                        table_bboxes = [(x0, y0, x1 - x0, y1 - y0) for x0, y0, x1, y1 in table_bboxes]

                text = extract_text_with_format(page, table_bboxes)
                if text:
                    md_content.extend(text)
                if text_content:
                    md_content.extend(text_content)
                all_tables.extend(md_tables)
            else:
                page_image = pdf_to_image(pdf_path, page_num)
                if page_image is None:
                    logging.error(f"頁面 {page_num + 1} 無法轉換為圖片，跳過")
                    continue

                md_table, _ = extract_table_with_ocr(page_image)
                if md_table:
                    md_content.extend(md_table)
                else:
                    md_tables, _ = extract_table_with_ppsstructure(page_image)
                    all_tables.extend(md_tables)

    merged_tables = merge_cross_page_tables(all_tables)
    md_content.extend(merged_tables)
    md_content = [c for c in md_content if not re.match(r'^\s*\(承前[頁贝]\)\s*$', str(c))]

    # 優化輸出格式
    final_content = []
    for item in md_content:
        item = str(item).strip()
        if not item:
            continue
        if re.match(r'^- \d+ -$', item):
            final_content.append(f"[Page {item.strip('- ')}]")
        else:
            final_content.append(item)
        final_content.append('---')

    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_content))
    logging.info(f"處理完成，結果已保存至 {output_md_path}")

if __name__ == "__main__":
    pdf_path = "report.pdf"
    output_md_path = "output.md"
    process_pdf(pdf_path, output_md_path)
