import uuid
import magic
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from fastapi import UploadFile, HTTPException
import fitz
import re

UPLOAD_DIR=Path("uploads/research_documents").resolve()
ALLOWED_EXTENSIONS={".pdf" , ".docx" , ".txt"}
MAX_FILE_SIZE=10*1024*1024                        #10MB 
EXPECTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain"
}
def verify_pdf(content:bytes):
    if not content.startswith(b"%PDF"):
        raise ValueError("Invalid PDF file content")
    if b"%%EOF" not in content[-2048:]:
        raise ValueError("Malformed PDF file")

def verify_docx(content:bytes):
    try:
        with ZipFile(BytesIO(content)) as archive:
            files = archive.namelist()
            if "[Content_Types].xml" not in files:
                raise ValueError("Invalid DOCX file structure")
            if "word/document.xml" not in files:
                raise ValueError("Invalid DOCX document")
            if archive.testzip() is not None:
                raise ValueError("Corrupted DOCX archive")
    except BadZipFile:
        raise ValueError("Invalid DOCX file : not valid ZIP archive")        

def verify_txt(content:bytes):
    try:
        content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("TXT file must use valid UTF-8 encoding")

# def verify_file_content(extension: str, content: bytes):
#     try:
#         detected_mime = magic.from_buffer(content, mime=True)   
#         if extension ==".pdf":
#             verify_pdf(content)
#         elif extension ==".docx":
#             verify_docx(content)
#         elif extension ==".txt":
#             verify_txt(content)
#         expected_mime=EXPECTED_MIME_TYPES[extension]
#         if detected_mime != expected_mime:
#             raise ValueError(
#                 f"MIME mismatch: expected {expected_mime}, detected {detected_mime}"
#             )    
#     except Exception as e:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid document: {str(e)}"
#         )


def verify_file_content(extension: str, content: bytes):
    try:

        if extension == ".pdf":
            verify_pdf(content)

            detected_mime = magic.from_buffer(content, mime=True)

            if detected_mime != "application/pdf":
                raise ValueError(
                    f"MIME mismatch: expected application/pdf, "
                    f"detected {detected_mime}"
                )

        elif extension == ".docx":
            # DOCX structural validation is more reliable
            verify_docx(content)

        elif extension == ".txt":
            verify_txt(content)

        else:
            raise ValueError("Unsupported document format")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document: {str(e)}"
        )


async def validate_and_save_documents(file:UploadFile):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )
    extension=Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format"
        )
    content=await file.read(MAX_FILE_SIZE + 1)
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Empty files are not allowed"
        )
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10 MB limit"
        )
    verify_file_content(extension, content)    
    stored_filename=f"{uuid.uuid4().hex}{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path=UPLOAD_DIR/stored_filename
    try:
        file_path.write_bytes(content)
    except OSError as e:
        print(f"Document storage error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to save document"
        )
    finally:
        await file.close()

    return {
        "original_filename": Path(file.filename).name,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_type": extension,
        "file_size": len(content)
    }                

def extract_pdf_text(file_path:Path):
    pages=[]
    try:
        with fitz.open(file_path) as pdf:
            for page_number , page in enumerate(pdf, start=1):
                text=page.get_text()
                if text.strip():
                    pages.append({
                        "page_number":page_number,
                        "text":text
                    })
    except Exception as e:
        print(f"PDF text extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail="failed to extract text from PDF"
        )   
    return pages             

def extract_docx_text(file_path:Path):
    from docx import Document
    try:
        doc=Document(file_path)
        pages=[]
        for i, para  in enumerate(doc.paragraphs, start=1):
            if para.text.strip():
                pages.append({
                    "page_number":i,
                    "text":para.text
                })
    except Exception as e:
        print(f"DOCX text extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from DOCX"
        )            
    return pages

def extract_txt_text(file_path:Path):
    try:
        with open(file_path, "r" , encoding="utf-8-sig") as f:
            pages=[]
            for i, line in enumerate(f, start=1):
                if line.strip():
                    pages.append({
                        "page_number":i,
                        "text":line.strip()
                    })
    except Exception as e:
        print(f"TXT text extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from TXT"
        )
    return pages



def extract_document_text(file_path: str, file_type: str) -> list[dict]:

    if file_type == ".pdf":
        pages = extract_pdf_text(file_path)

    elif file_type == ".docx":
        pages = extract_docx_text(file_path)

    elif file_type == ".txt":
        pages = extract_txt_text(file_path)

    else:
        raise ValueError("Unsupported document format")

    if not pages:
        raise ValueError("Document contains no extractable text")

    return pages

def clean_extracted_text(pages:list[dict]):
    cleaned_pages=[]
    for page in pages:
        text=page["text"]
        text = text.replace("\r\n", "\n").replace("\r", "\n")                    # Normalize line endings
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)             # Remove null bytes and unwanted control characters
        text = re.sub(r"[ \t]+", " ", text)                                      # Remove excessive spaces and tabs
        text = re.sub(r"\n{3,}", "\n\n", text)                                   # Remove excessive blank lines
        text=text.strip()
        if text:
            cleaned_pages.append({
                "page_number":page["page_number"],
                "text":text
            })
    if not cleaned_pages:
        raise ValueError("No readable text found after cleaning")            
    return cleaned_pages

def chunk_text(pages:list[dict] , chunk_size:int=1000 , overlap:int=200):
    if chunk_size <=100:
        raise ValueError("Chunk size must be greater than 100 characters.....")
    if overlap >= chunk_size:
        raise ValueError("Overlap must be less than chunk size..........")
    chunks=[]
    chunk_index=0
    for page in pages:
        text=page["text"]
        start=0
        while start < len(text):
            end=start + chunk_size
            chunk_text=text[start:end]
            if chunk_text:
                chunks.append({
                    "chunk_index":chunk_index,
                    "page_number":page["page_number"],
                    "text":chunk_text
                })
                chunk_index+=1
            if end == len(text):
                break
            start=end-overlap
    if not chunks:
        raise ValueError("No text chunks created from the document")
    return chunks            

