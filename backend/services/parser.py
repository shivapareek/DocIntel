import fitz  # PyMuPDF
import pdfplumber
from typing import Optional, List, Dict, Any
import re
from pathlib import Path

class DocumentParser:
    """
    Document parser with fallback mechanisms for PDF and TXT files
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt']
    
    def parse_pdf(self, file_path: str) -> str:
        """
        Parse PDF file with fallback from PyMuPDF to pdfplumber
        """
        try:
            # First try PyMuPDF (faster)
            content = self._parse_pdf_pymupdf(file_path)
            if content and len(content.strip()) > 100:  # Reasonable content threshold
                return content
            
            # Fallback to pdfplumber (better for complex layouts)
            content = self._parse_pdf_pdfplumber(file_path)
            return content
            
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def _parse_pdf_pymupdf(self, file_path: str) -> str:
        """Parse PDF using PyMuPDF"""
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            text += "\n\n"  # Add page separator
        
        doc.close()
        return self._clean_text(text)
    
    def _parse_pdf_pdfplumber(self, file_path: str) -> str:
        """Parse PDF using pdfplumber"""
        text = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    text += "\n\n"  # Add page separator
        
        return self._clean_text(text)
    
    def parse_txt(self, file_path: str) -> str:
        """Parse TXT file with encoding detection"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return self._clean_text(content)
        except UnicodeDecodeError:
            # Fallback to other encodings
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
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove page numbers and headers/footers (basic patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text, flags=re.IGNORECASE)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract document metadata"""
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
        """
        Split text into overlapping chunks for better context preservation
        """
        if not text:
            return []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                current_chunk = current_chunk[-overlap:] + paragraph
            else:
                current_chunk += paragraph + "\n\n"
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Extract sections based on headers (basic implementation)
        """
        sections = []
        
        # Basic header patterns
        header_patterns = [
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headers
            r'^(\d+\.?\s+[A-Z][^.]*?)$',  # Numbered headers
            r'^([A-Z][^.]*?):$',  # Colon headers
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a header
            is_header = False
            for pattern in header_patterns:
                if re.match(pattern, line):
                    # Save previous section
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content)
                        })
                    
                    # Start new section
                    current_section = line
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Add the last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content)
            })
        
        return sections