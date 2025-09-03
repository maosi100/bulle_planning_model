from pathlib import Path
from time import sleep
from extractors.mengenlisten_extractor.mengenlisten_extractor import MengenlistenExtractor


def process_mengenlisten():
    """Process all mengenlisten .pdf files and create JSON extracts"""
    
    input_dir = Path("../../data/raw/Mengenlisten/")
    output_dir = Path("../../data/processed/Mengenlisten/")
    qc_dir = Path("../../data/processed/qc/")
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = MengenlistenExtractor()
    
    pdf_files = list(input_dir.glob("*.pdf"))
    processed_count = 0
    
    print(f"Found {len(pdf_files)} mengenlisten files to process")
    
    for i, pdf_file in enumerate(pdf_files):
        try:
            print(f"Processing {pdf_file.name} ({i+1}/{len(pdf_files)})...")
            
            mengenliste = extractor.read_file(pdf_file)
            
            if mengenliste:
                # Save JSON extract with date as filename
                output_path = output_dir / f"{mengenliste.report_date}.json"
                extractor.convert_to_json(mengenliste, output_path)
                
                print(f"  ✓ Extracted data for {mengenliste.report_date} to {output_path.name}")
                processed_count += 1
            else:
                print(f"  ✗ Failed to extract data from {pdf_file.name}")
            
            # Rate limiting - 5 second delay between API calls
            if i < len(pdf_files) - 1:  # Don't sleep after last file
                sleep(5)
                
        except Exception as e:
            print(f"  ✗ Error processing {pdf_file.name}: {e}")
            # Still sleep to avoid API rate limits
            if i < len(pdf_files) - 1:
                sleep(5)
    
    # Save unparsed files to QC directory
    unparsed_path = qc_dir / "unparsed_mengenlisten.txt"
    extractor.save_unparsed_blocks(unparsed_path)
    
    print(f"\nCompleted: {processed_count}/{len(pdf_files)} files processed")
    print(f"Unparsed files saved to: {unparsed_path}")


if __name__ == "__main__":
    process_mengenlisten()