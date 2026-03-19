"""
PDF Processing Module
Handles PDF to image conversion and OCR text extraction
"""

import os
from typing import List, Dict
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import PyPDF2


class PDFProcessor:
    """Process PDF files for construction estimating"""
    
    def __init__(self, dpi: int = 300):
        """
        Initialize PDF processor
        
        Args:
            dpi: Resolution for image conversion (300 is standard for blueprints)
        """
        self.dpi = dpi
    
    def process_pdf(self, pdf_path: str, output_dir: str, file_id: str) -> List[Dict]:
        """
        Process PDF file - convert to images and extract text
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save processed images
            file_id: Unique identifier for this file
        
        Returns:
            List of page information dictionaries
        """
        # Create output directory for this file
        file_output_dir = os.path.join(output_dir, file_id)
        os.makedirs(file_output_dir, exist_ok=True)
        
        # Convert PDF to images
        print(f"Converting PDF to images at {self.dpi} DPI...")
        images = convert_from_path(pdf_path, dpi=self.dpi)
        
        pages_info = []
        
        for i, image in enumerate(images):
            page_number = i + 1
            print(f"Processing page {page_number}/{len(images)}...")
            
            # Save image
            image_filename = f"page_{page_number}.png"
            image_path = os.path.join(file_output_dir, image_filename)
            image.save(image_path, 'PNG', optimize=True)
            
            # Extract text with OCR
            text = self.extract_text_from_image(image)
            
            # Detect sheet type (architectural, structural, MEP, etc.)
            sheet_type = self.detect_sheet_type(text)
            
            # Extract sheet number if present
            sheet_number = self.extract_sheet_number(text)
            
            pages_info.append({
                'page_number': page_number,
                'image_path': image_path,
                'text': text,
                'sheet_type': sheet_type,
                'sheet_number': sheet_number
            })
        
        print(f"✓ Processed {len(pages_info)} pages")
        return pages_info
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image: PIL Image object
        
        Returns:
            Extracted text string
        """
        try:
            # Use Tesseract OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return ""
    
    def detect_sheet_type(self, text: str) -> str:
        """
        Detect the type of construction sheet based on text content
        
        Args:
            text: Extracted text from sheet
        
        Returns:
            Sheet type (architectural, structural, mechanical, electrical, plumbing, civil)
        """
        text_lower = text.lower()
        
        # Architectural indicators
        if any(word in text_lower for word in ['floor plan', 'elevation', 'section', 'wall type', 'room finish']):
            return 'architectural'
        
        # Structural indicators
        if any(word in text_lower for word in ['structural', 'foundation', 'beam', 'column', 'footing', 'rebar']):
            return 'structural'
        
        # Mechanical (HVAC) indicators
        if any(word in text_lower for word in ['hvac', 'duct', 'air handler', 'mechanical', 'supply air', 'return air']):
            return 'mechanical'
        
        # Electrical indicators
        if any(word in text_lower for word in ['electrical', 'panel', 'circuit', 'lighting', 'power', 'receptacle']):
            return 'electrical'
        
        # Plumbing indicators
        if any(word in text_lower for word in ['plumbing', 'water', 'sewer', 'drain', 'fixture', 'pipe']):
            return 'plumbing'
        
        # Civil indicators
        if any(word in text_lower for word in ['site plan', 'grading', 'civil', 'contour', 'drainage']):
            return 'civil'
        
        return 'general'
    
    def extract_sheet_number(self, text: str) -> str:
        """
        Extract sheet number from text (e.g., A-101, S-201, M-301)
        
        Args:
            text: Extracted text from sheet
        
        Returns:
            Sheet number if found, empty string otherwise
        """
        import re
        
        # Common sheet number patterns
        patterns = [
            r'[A-Z]-\d{3}',  # A-101, S-201, etc.
            r'[A-Z]\d{3}',   # A101, S201, etc.
            r'SHEET\s+([A-Z]-?\d{1,3})',
            r'DWG\s+([A-Z]-?\d{1,3})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.groups():
                    return match.group(1)
                return match.group(0)
        
        return ''
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict:
        """
        Extract metadata from PDF
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with metadata
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                    'subject': pdf_reader.metadata.get('/Subject', '') if pdf_reader.metadata else '',
                    'creator': pdf_reader.metadata.get('/Creator', '') if pdf_reader.metadata else '',
                }
                
                return metadata
        except Exception as e:
            print(f"Error reading PDF metadata: {str(e)}")
            return {'num_pages': 0}
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text directly from PDF (faster than OCR but may miss text in images)
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Extracted text
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def optimize_image_for_ai(self, image_path: str, max_dimension: int = 2000) -> str:
        """
        Optimize image for AI processing (resize if too large)
        
        Args:
            image_path: Path to image file
            max_dimension: Maximum width or height
        
        Returns:
            Path to optimized image
        """
        try:
            img = Image.open(image_path)
            
            # Check if resizing needed
            if max(img.size) > max_dimension:
                # Calculate new dimensions maintaining aspect ratio
                ratio = max_dimension / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                
                # Resize
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save optimized version
                optimized_path = image_path.replace('.png', '_optimized.png')
                img.save(optimized_path, 'PNG', optimize=True)
                
                return optimized_path
            
            return image_path
            
        except Exception as e:
            print(f"Error optimizing image: {str(e)}")
            return image_path
