import os
from typing import Optional
from pathlib import Path
from google import genai
from google.genai import types
from loguru import logger
from dotenv import load_dotenv


class GeminiClient:
    def __init__(self) -> None:
        load_dotenv()
        try:
            self.client = genai.Client(
                api_key=os.environ["GEMINI_API_KEY"],
            )
        except Exception as e:
            logger.exception(f"Could not connect to AI Service: {e}")
            raise

    def generate_response(self, file_path: Path) -> Optional[str]:
        try:
            logger.debug(f"Processing PDF: {file_path}")

            prompt = self._create_prompt(file_path.name)

            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=file_path.read_bytes(), mime_type="application/pdf"
                    ),
                    prompt,
                ],
            )

            if response.text:
                logger.debug(f"Successfully processed PDF: {file_path}")
                return self._clean_json_response(response.text)
            else:
                logger.warning(f"API returned empty response for {file_path}")
                return None

        except Exception as e:
            logger.error(
                f"Failed to process PDF {file_path} with the following Exception: {e}"
            )
            return None

    def _create_prompt(self, file_path: str) -> str:
        template = """
        <task>
        Extract data from this German bakery shift report (Mengenliste) PDF and return it as JSON only.
        </task>

        <document_structure>
        - Header: "Backtag [DAY] (für [DAY])" at top
        - Main table columns: Mengenliste | Aktuelle Menge | Retoure | Ausverkauft/Notizen
        - Footer: May contain weather info, staff names
        </document_structure>

        <extraction_rules>
        - Mengenliste: Extract product names exactly as written
        - Aktuelle Menge: Always extract, if required format into full integers
        - Retoure: Only extract clear integers (ignore -, 0, O, ✓, symbols)
        - Ausverkauft/Notizen: Only extract times in HH:MM format, ignore other text
        - Skip unclear/illegible entries rather than guessing
        - Do not extract anything from the Footer
        - Follow the output format rigorously
        </extraction_rules>

        <date_logic>
        1. Try to find explicit date in document first
        2. If none found, use filename date as scan date
        3. Calculate business date: compare scan date day-of-week with sales_day mentioned in document
        4. Work backwards to find correct business date
        </date_logic>

        <output_format>
        {{
          "YYYY-MM-DD": {{
            "production_day": "day mentioned for Backtag",
            "sales_day": "day mentioned for 'Für Tag' - right after 'Backtag'", 
            "articles": [
              {{
                "article_name": "Article Name",
                "stock": "Aktuelle Menge",
                "leftover": "Retoure",
                "sold_out": "Ausverkauft/Notizen"
              }}
            ]
          }}
        }}
        </output_format>

        <quality_guidelines>
        - Accuracy over completeness - skip unclear data
        - Use null for missing/unclear fields, not empty strings
        - Keep product sections separate, don't merge
        - Ensure valid JSON syntax
        - Do not guess the sold_out times when they're unclearly written. check the <opening hours> for plausibility
        </quality_guidelines>

        <opening hours>
        The opening hours of the bakery are:
        Monday: closed
        Tuesday to Friday: 07:00 until 15:00
        Saturday: 07:00 until 13:00
        Sunday: 07:00 until 11:00
        </opening hours>

        <file name>
        The file name for the current file is {file_path}
        <file name>
        """
        return template.format(file_path=file_path)

    def _clean_json_response(self, response_text: str) -> str:
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        return clean_text.strip()
