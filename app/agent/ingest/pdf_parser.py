import fitz
import os
import re
from typing import List
from app.agent.core.schemas import ParsedSection, LawFamily

class PDFParser:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.family_map = {
            "Dowry and Bridal Gifts Act 1976": LawFamily.DOWRY_ACT,
            "The Child Marriage Restraint Act": LawFamily.CHILD_MARRIAGE,
            "The Dissolution of Muslim Marriages Act, 1939": LawFamily.DISSOLUTION,
            "The Muslim Family Laws Ordinance": LawFamily.MUSLIM_FAMILY_LAWS,
            "The Protection of Parents Ordinance": LawFamily.PARENT_PROTECTION,
            "The West Pakistan Family Courts Act": LawFamily.FAMILY_COURTS
        }

    def parse_all(self) -> List[ParsedSection]:
        all_sections = []
        for folder_name, family in self.family_map.items():
            folder_path = os.path.join(self.data_path, folder_name)
            if not os.path.exists(folder_path):
                continue
            
            for filename in os.listdir(folder_path):
                if filename.endswith(".pdf"):
                    pdf_path = os.path.join(folder_path, filename)
                    sections = self.parse_pdf(pdf_path, family, filename)
                    all_sections.extend(sections)
        return all_sections

    def parse_pdf(self, pdf_path: str, family: LawFamily, filename: str) -> List[ParsedSection]:
        sections = []
        doc = fitz.open(pdf_path)
        
        # Extract year from filename
        year_match = re.search(r"(19|20)\d{2}", filename)
        year = int(year_match.group(0)) if year_match else 0
        
        is_amendment = "Amendment" in filename or "Ordinance" in filename and year > 1964 # Heuristic
        if "Muslim Family Laws Ordinance, 1961" in filename:
            is_amendment = False # Primary law

        full_text = ""
        for page_num, page in enumerate(doc):
            text = page.get_text()
            # Simple heuristic to split into sections
            # Look for "Section X" or "X." at start of lines
            # This is a crude split, recovery script will refine this
            full_text += f"\n--- PAGE {page_num + 1} ---\n{text}"

        # For now, we store the full text per page as a "pseudo-section"
        # The OCR Recovery script will handle the heavy lifting of section splitting
        for page_num, page in enumerate(doc):
            sections.append(ParsedSection(
                law_family=family,
                pdf_filename=filename,
                section_number=f"Page {page_num + 1}",
                body=page.get_text(),
                page_number=page_num + 1,
                is_amendment=is_amendment,
                year=year
            ))
            
        doc.close()
        return sections

if __name__ == "__main__":
    parser = PDFParser(r"D:\wakeel-ai-be\Wakeel-AI-data")
    results = parser.parse_all()
    print(f"Parsed {len(results)} pages across 18 PDFs.")
