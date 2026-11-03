# import os 
# import uuid 
# from pathlib import Path
# from fastapi import UploadFile , HTTPException

# UPLOAD_DIR=Path("uploads/research_documents").resolve()
# ALLOWED_EXTENSIONS={".pdf" , ".docx",".txt"}
# MAX_FILE_SIZE=10*1024*1024   #10MB
# async def validate_and_save_documents(file:UploadFile):
#     if not file.filename:
#         raise ValueError("No file uploaded")
#     extension=Path(file.filename).suffix.lower()    
#     if extension not in ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=400,
#             detail="Unsupported file format"
#         )
#     file_content=await file.read()
#     if not file_content:
#         raise HTTPException(
#             status_code=400,
#             detail="Empty files are not allowed"
#         )
#     if len(file_content)>MAX_FILE_SIZE:
#         raise HTTPException(
#             status_code=413,
#             detail="File size exceeds 10 MB limit"
#         )
#     stored_filename=f"{uuid.uuid4().hex}{extension}"
#     UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
#     file_path=UPLOAD_DIR/stored_filename
#     try:
#         file_path.write_bytes(file_content)
#     except OSError as e:
#         print(f"Document storage error: {e}")

#         raise HTTPException(
#             status_code=500,
#             detail="Failed to save document"
#         )
#     finally:
#         await file.close()
#     return {
#         "original_filename": Path(file.filename).name,
#         "stored_filename": stored_filename,
#         "file_path": str(file_path),
#         "file_type": extension,
#         "file_size": len(file_content)
#     }   


import uuid
import magic
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from fastapi import UploadFile, HTTPException

UPLOAD_DIR=Path("uploads/research_documents").resolve()
ALLOWED_EXTENSIONS={".pdf" , ".docx" , ".txt"}
MAX_FILE_SIZE=10*1024*1024    #10MB 
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

def verify_file_content(extension: str, content: bytes):
    try:
        detected_mime = magic.from_buffer(content, mime=True)   
        if extension ==".pdf":
            verify_pdf(content)
        elif extension ==".docx":
            verify_docx(content)
        elif extension ==".txt":
            verify_txt(content)
        expected_mime=EXPECTED_MIME_TYPES[extension]
        if detected_mime != expected_mime:
            raise ValueError(
                f"MIME mismatch: expected {expected_mime}, detected {detected_mime}"
            )    
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