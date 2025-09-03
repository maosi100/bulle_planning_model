from pathlib import Path
from extractors.fiskal_extractor.fiskal_extractor import FiskalExtractor


def process_fiskaljournale():
    """Process all fiskaljournal .txt files and create JSON extracts"""
    
    input_dir = Path("../../data/raw/Fiskaljournale/")
    output_dir = Path("../../data/processed/Fiskaljournale/")
    qc_dir = Path("../../data/processed/qc/")
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = FiskalExtractor()
    
    txt_files = list(input_dir.glob("*.txt"))
    processed_count = 0
    
    print(f"Found {len(txt_files)} fiskaljournal files to process")
    
    for txt_file in txt_files:
        try:
            print(f"Processing {txt_file.name}...")
            
            transactions = extractor.read_file(txt_file)
            
            # Save JSON extract
            output_path = output_dir / f"{txt_file.name}.json"
            extractor.convert_to_json(transactions, output_path)
            
            print(f"  ✓ Extracted {len(transactions)} transactions to {output_path.name}")
            processed_count += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {txt_file.name}: {e}")
    
    # Save unparsed blocks to QC directory
    unparsed_path = qc_dir / "unparsed_fiskal_blocks.txt"
    extractor.save_unparsed_blocks(unparsed_path)
    
    print(f"\nCompleted: {processed_count}/{len(txt_files)} files processed")
    print(f"Unparsed blocks saved to: {unparsed_path}")


if __name__ == "__main__":
    process_fiskaljournale()