import fitz  # PyMuPDF
import pdfplumber
from typing import Optional, List, Dict, Any
import re
from pathlib import Path

class DocumentParser:    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt']
    
    def parse_pdf(self, file_path: str) -> str:
        try:
            content = self._parse_pdf_pymupdf(file_path)
            if content and len(content.strip()) > 100:  
                return content
            
            content = self._parse_pdf_pdfplumber(file_path)
            return content
            
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def _parse_pdf_pymupdf(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            text += "\n\n" 
        
        doc.close()
        return self._clean_text(text)
    
    def _parse_pdf_pdfplumber(self, file_path: str) -> str:
        text = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    text += "\n\n"  
        
        return self._clean_text(text)
    
    def parse_txt(self, file_path: str) -> str:
        """Parse TXT file with encoding detection"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return self._clean_text(content)
        except UnicodeDecodeError:
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        return self._clean_text(content)
                except UnicodeDecodeError:
                    continue
            
            raise Exception("Could not decode text file with any common encoding")
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        metadata = {
            'filename': path.name,
            'size': path.stat().st_size,
            'extension': path.suffix.lower()
        }
        
        if path.suffix.lower() == '.pdf':
            try:
                doc = fitz.open(file_path)
                pdf_metadata = doc.metadata
                metadata.update({
                    'title': pdf_metadata.get('title', ''),
                    'author': pdf_metadata.get('author', ''),
                    'subject': pdf_metadata.get('subject', ''),
                    'creator': pdf_metadata.get('creator', ''),
                    'page_count': len(doc)
                })
                doc.close()
            except Exception:
                pass
        
        return metadata
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        if not text:
            return []
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = current_chunk[-overlap:] + paragraph
            else:
                current_chunk += paragraph + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_sections(self, text: str) -> List[Dict[str, str]]:

        sections = []
        
        header_patterns = [
            r'^([A-Z][A-Z\s]+)$',  
            r'^(\d+\.?\s+[A-Z][^.]*?)$', 
            r'^([A-Z][^.]*?):$', 
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            is_header = False
            for pattern in header_patterns:
                if re.match(pattern, line):
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content)
                        })
                    
                    current_section = line
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content)
            })
        
        return sections