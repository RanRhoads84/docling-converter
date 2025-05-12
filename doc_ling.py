'''Docling file format converter (CPU-parallel and GPU-ready with fallback + logging)'''
import time
from csv import writer
from datetime import datetime
from pathlib import Path
from multiprocessing import cpu_count, set_start_method, get_context
from functools import partial
from tqdm import tqdm
from docling_core.types.doc import DocItemLabel, ImageRefMode
from docling.document_converter import DocumentConverter

try:
    from easyocr import Reader
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

OCR_READER_GPU = None
OCR_READER_CPU = None
LOG_FILE = Path("conversion.log")

# Define helper functions for saving documents in various formats


def log(message: str):
    """
    Logs a message to a file and prints it to the console.

    This function appends the given message to a log file and also
    outputs the message to the standard output.

    Args:
        message (str): The message to be logged.

    Raises:
        FileNotFoundError: If the log file does not exist and cannot be created.
        IOError: If there is an error writing to the log file.
    """
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)


def _save_html(doc, file_path: Path):
    doc.save_as_html(filename=file_path, image_mode=ImageRefMode.REFERENCED, labels=[
                     DocItemLabel.FOOTNOTE])
    log(f"Saved HTML to {file_path}")


def _save_json(doc, file_path: Path):
    doc.save_as_json(file_path, image_mode=ImageRefMode.PLACEHOLDER)
    log(f"Saved JSON to {file_path}")


def _save_markdown(doc, file_path: Path):
    doc.save_as_markdown(file_path, image_mode=ImageRefMode.PLACEHOLDER)
    log(f"Saved Markdown to {file_path}")


def _save_text(doc, file_path: Path):
    file_path.write_text(doc.export_to_text())
    log(f"Saved Text to {file_path}")


def _save_doctags(doc, file_path: Path):
    file_path.write_text(doc.export_to_doctags())
    log(f"Saved Doctags to {file_path}")


def process_file(file_path, ext, output_root, format_key,
                 input_base, use_gpu, ocr_reader_gpu, ocr_reader_cpu):
    """
    Processes a file by converting its content and
    optionally performing OCR if the file is an image.
    Args:
        file_path (Path): The path to the file to be processed.
        ext (str): The file extension for the output file.
        output_root (Path): The root directory where the processed file will be saved.
        format_key (str): The format key indicating the output format
        (e.g., "html", "json", "md", "txt", "doctags").
        input_base (Path): The base directory of the input files, used to determine relative paths.
        use_gpu (bool): Whether to use GPU for OCR processing.
        ocr_reader_gpu (Reader or None): An optional pre-initialized OCR reader for GPU.
        If None, it will be initialized.
    Raises:
        FileNotFoundError: If the specified file does not exist.
        RuntimeError: If GPU is not available when required for OCR processing.
        ValueError: If an error occurs during file conversion or OCR processing.
    Notes:
        - The function uses a `DocumentConverter` to convert the file content.
        - OCR is performed on image files (e.g., .jpg, .jpeg, .png) if `use_gpu` is True.
        - The processed file is saved in a directory structure based on
        the `output_root`, `format_key`, and relative path.
    Logs:
        - Logs the number of lines detected by OCR (GPU or CPU).
        - Logs errors encountered during file processing.
    """
    if use_gpu and GPU_AVAILABLE and ocr_reader_gpu is None:
        ocr_reader_gpu = Reader(['en'], gpu=True)
        ocr_reader_cpu = Reader(['en'], gpu=False)

    converter = DocumentConverter()
    handlers = {
        "html": _save_html,
        "json": _save_json,
        "md": _save_markdown,
        "txt": _save_text,
        "doctags": _save_doctags,
    }
    save_func = handlers[format_key]

    try:
        res = converter.convert(str(file_path))

        if use_gpu and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            try:
                if GPU_AVAILABLE:
                    ocr_result = OCR_READER_GPU.readtext(str(file_path))
                    log(
                        f"GPU OCR result for {file_path.name}: {len(ocr_result)} lines detected")
                else:
                    raise RuntimeError("GPU not available")
            except (RuntimeError, ValueError):
                if OCR_READER_CPU:
                    if ocr_reader_cpu:
                        log(f"GPU OCR failed for {file_path.name}, falling back to CPU OCR.")
                        ocr_result = ocr_reader_cpu.readtext(str(file_path))
                        log(
                            f"CPU OCR result for {file_path.name}: {
                                len(ocr_result)} lines detected")

        input_name = input_base.name
        relative_path = file_path.parent.relative_to(input_base)
        target_dir = output_root / format_key / input_name / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{file_path.stem}.{ext}"
        save_func(res.document, target_file)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        log(f"Error processing {file_path.name}: {exc}")


def main():
    """
    Main entry point for the Docling Converter script.

    Prompts the user for input path and desired output format, then processes
    the input file(s) accordingly using multiprocessing. Supports GPU OCR fallback
    for image files using EasyOCR. Logs progress and status to console and file.
    """
    log("Welcome to Docling file format converter!")

    source_input = input(
        "Enter the path to the PDF, image file, or folder to convert: ").strip()
    source_path = Path(source_input)
    if not source_path.exists():
        log("File or folder does not exist. Exiting.")
        return

    log("\nSelect output format:")
    log("1. HTML   (image embedding and referencing supported)")
    log("2. JSON   (lossless serialization of Docling Document)")
    log("3. Markdown")
    log("4. Text   (plain text, no Markdown markers)")
    log("5. Doctags")
    format_choice = input("Enter the number of your choice: ").strip()

    format_map = {"1": "html", "2": "json",
                  "3": "md", "4": "txt", "5": "doctags"}
    format_key = format_map.get(format_choice)
    if not format_key:
        log("Invalid choice. Exiting.")
        return

    use_gpu = GPU_AVAILABLE and input(
        "Enable GPU OCR support for image files? (y/n): ").strip().lower() == 'y'

    base_output_dir = Path(__file__).resolve().parent / "output"
    ext = format_key
    supported_exts = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"]

    input_base = source_path if source_path.is_dir() else source_path.parent
    files = [source_path] if source_path.is_file(
    ) else [f for f in source_path.rglob("*") if f.suffix.lower() in supported_exts]

    start_time = time.time()
    log("================================================")
    log(f"Processing... {source_path}")
    log("================================================\n")

    with get_context("spawn").Pool(processes=cpu_count()) as pool:
        ocr_reader_gpu = None

        ocr_reader_cpu = None
        list(tqdm(
            pool.imap(partial(process_file, ext=ext, output_root=base_output_dir,
                              format_key=format_key, input_base=input_base, use_gpu=use_gpu,
                              ocr_reader_gpu=ocr_reader_gpu, ocr_reader_cpu=ocr_reader_cpu), files),
            total=len(files),
            desc="Converting",
            unit="file"
        ))
    log(
        f"\nTotal document processing time: {time.time() - start_time:.2f} seconds")
    log("================================================")
    log("done!")
    success_count = sum(1 for f in files if (base_output_dir / format_key /
                        input_base.name / f.parent.relative_to(input_base) /
                        f"{f.stem}.{ext}").exists())
    failure_count = len(files) - success_count

    csv_path = base_output_dir / "conversion_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        csv_writer = writer(csvfile)

        csv_writer.writerow(["File", "Status", "Timestamp"])
        for f in files:
            output_path = base_output_dir / format_key / input_base.name / \
                f.parent.relative_to(input_base) / f"{f.stem}.{ext}"
            status = "Success" if output_path.exists() else "Failed"
            csv_writer.writerow([str(f), status, datetime.now().isoformat()])
    log(f"Successfully converted: {success_count}")
    log(f"Failed conversions: {failure_count}")
    log(f"Total files processed: {len(files)}")
    if len(files) == 0:
        log("Warning: No supported input files were found.")
    log("================================================")


if __name__ == "__main__":
    set_start_method("spawn", force=True)
    main()
