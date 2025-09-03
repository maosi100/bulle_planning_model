from pathlib import Path
from collections import defaultdict
import re
import tempfile
import shutil
import json
from data_unifier.data_unifier import DataUnifier


def get_month_key_from_fiskal_filename(filename: str) -> str:
    """Extract YYYY-MM format from fiskal filename like 'Birke April 2023.txt.json'"""
    months = {
        "Januar": "01", "Februar": "02", "Maerz": "03", "März": "03",
        "April": "04", "Mai": "05", "Juni": "06", "Juli": "07",
        "August": "08", "September": "09", "Oktober": "10",
        "November": "11", "Dezember": "12", "Fabruar": "02"
    }
    
    for month_name, month_num in months.items():
        if month_name in filename:
            year_match = re.search(r"(20\d{2})", filename)
            if year_match:
                return f"{year_match.group(1)}-{month_num}"
    return None


def get_month_key_from_date(date_str: str) -> str:
    """Extract YYYY-MM format from date string like '2024-04-11'"""
    return date_str[:7]


def create_monthly_mengenlisten_dirs(mengenlisten_dir: Path) -> dict:
    """Group mengenlisten files by month and create temporary directories"""
    monthly_files = defaultdict(list)
    
    # Group mengenlisten files by month
    for json_file in mengenlisten_dir.glob("*.json"):
        date_str = json_file.stem  # e.g., '2024-04-11'
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            month_key = get_month_key_from_date(date_str)
            monthly_files[month_key].append(json_file)
    
    # Create temporary directories for each month
    temp_dirs = {}
    for month_key, files in monthly_files.items():
        temp_dir = Path(tempfile.mkdtemp())
        for file in files:
            shutil.copy2(file, temp_dir)
        temp_dirs[month_key] = temp_dir
    
    return temp_dirs


def cleanup_temp_dirs(temp_dirs: dict):
    """Clean up temporary directories"""
    for temp_dir in temp_dirs.values():
        shutil.rmtree(temp_dir)


def process_unified_data():
    """Process all months from processed directories and create unified data"""
    
    # Directory paths
    bestellungen_dir = Path("../../data/processed/Bestellungen/")
    fiskaljournale_dir = Path("../../data/processed/Fiskaljournale/")
    mengenlisten_dir = Path("../../data/processed/Mengenlisten/")
    output_dir = Path("../../data/processed/Unified_data/")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if directories exist
    if not all([fiskaljournale_dir.exists(), mengenlisten_dir.exists()]):
        print("Error: Required directories not found:")
        print(f"  Fiskaljournale: {fiskaljournale_dir.exists()}")
        print(f"  Mengenlisten: {mengenlisten_dir.exists()}")
        return
    
    unifier = DataUnifier()
    
    # Get bestellungen files
    bestellungen_files = {}
    if bestellungen_dir.exists():
        for json_file in bestellungen_dir.glob("bestellungen_*.json"):
            month_match = re.search(r"bestellungen_(\d{4}-\d{2})\.json", json_file.name)
            if month_match:
                bestellungen_files[month_match.group(1)] = json_file
    
    # Get fiskal files
    fiskal_files = {}
    for json_file in fiskaljournale_dir.glob("*.json"):
        month_key = get_month_key_from_fiskal_filename(json_file.name)
        if month_key:
            fiskal_files[month_key] = json_file
    
    # Create monthly mengenlisten directories
    print("Grouping mengenlisten files by month...")
    mengenlisten_monthly_dirs = create_monthly_mengenlisten_dirs(mengenlisten_dir)
    
    try:
        # Get all available months
        all_months = (
            set(bestellungen_files.keys()) | 
            set(fiskal_files.keys()) | 
            set(mengenlisten_monthly_dirs.keys())
        )
        
        print(f"Found {len(all_months)} months to process: {sorted(all_months)}")
        
        processed_months = 0
        for month_key in sorted(all_months):
            fiskal_path = fiskal_files.get(month_key)
            bestellungen_path = bestellungen_files.get(month_key)
            mengenlisten_temp_dir = mengenlisten_monthly_dirs.get(
                month_key, Path(tempfile.mkdtemp())
            )
            
            # Skip months where we don't have fiskal data
            if not fiskal_path:
                print(f"Skipping {month_key}: Missing fiskal data")
                continue
            
            print(f"\nProcessing {month_key}...")
            print(f"  Fiskal: {fiskal_path.name}")
            print(f"  Bestellungen: {bestellungen_path.name if bestellungen_path else 'Not available'}")
            print(f"  Mengenlisten: {len(list(mengenlisten_temp_dir.glob('*.json')))} files")
            
            try:
                consolidated_data, unmapped_data = unifier.unify_monthly_data(
                    fiskal_path, mengenlisten_temp_dir, bestellungen_path
                )
                
                # Write consolidated data
                output_file = output_dir / f"consolidated_{month_key}.json"
                unifier.write_monthly_consolidated_data(consolidated_data, output_file)
                
                # Write unmapped items to QC directory
                if unmapped_data:
                    qc_dir = Path("../../data/processed/qc")
                    qc_dir.mkdir(parents=True, exist_ok=True)
                    
                    for date_str, unmapped_items in unmapped_data.items():
                        qc_data = {
                            "date": date_str,
                            **unmapped_items
                        }
                        qc_file_path = qc_dir / f"unmapped_items_{date_str}.json"
                        with open(qc_file_path, "w", encoding="utf-8") as f:
                            json.dump(qc_data, f, indent=2, ensure_ascii=False)
                
                print(f"  ✓ Processed {len(consolidated_data)} days -> {output_file.name}")
                if unmapped_data:
                    print(f"    QC: {len(unmapped_data)} days with unmapped items")
                processed_months += 1
                
            except Exception as e:
                print(f"  ✗ Error processing {month_key}: {e}")
        
        print(f"\nCompleted: {processed_months}/{len(all_months)} months processed")
        print(f"Consolidated files saved to: {output_dir}")
        print("QC files saved to: ../../data/processed/qc/")
        
    finally:
        print("\nCleaning up temporary directories...")
        cleanup_temp_dirs(mengenlisten_monthly_dirs)


if __name__ == "__main__":
    process_unified_data()