# Docling Converter

> This is a multi-format document conversion tool built on the [Docling](https://github.com/docling-ai/docling) framework. It supports batch conversion of PDFs and image files into formats like HTML, JSON, Markdown, > plain text, or Doctags — without relying on vision-language models (VLMs). It also supports GPU-accelerated OCR using EasyOCR with automatic CPU fallback and logs every step to both the console and a log file.

---

## ✅ Features

- Convert individual files or entire folders
- Output to:
  - HTML
  - JSON
  - Markdown
  - Plain text
  - Doctags
- Fully parallelized with Python multiprocessing
- GPU OCR via [EasyOCR](https://github.com/JaidedAI/EasyOCR) for `.jpg`, `.jpeg`, `.png`
- Logs to both console and `conversion.log`
- Preserves folder structure under:

output/format/input-folder/

- Summary CSV report (`conversion_summary.csv`) with:
- File path
- Success/failure status
- Timestamp

---

## 📦 Requirements

Python 3.10+

Install dependencies:

```bash
pip install docling-core tqdm easyocr
```

If using GPU OCR:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

---

## 🚀 Usage

```bash
python doc_ling.py
```

Follow the prompts to:

1. Enter a file or directory to convert
2. Choose an output format
3. Enable or disable GPU OCR support

---

## 📝 Output Example

Input:
/docs/invoices/sample1.pdf

Output:
/output/html/invoices/sample1.html

Log:
conversion.log

Summary:
output/conversion_summary.csv

---

## 📋 Notes

- Uses Python’s `"spawn"` method to avoid CUDA semaphore leaks.
- Uses EasyOCR only on image files and only if you opt in.
- Automatically creates output folders matching input layout.

---

## 📄 License

GPL-3
