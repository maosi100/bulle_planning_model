from pathlib import Path
from collections import defaultdict
from extractors.bestellungs_extractor.bestellungs_extractor import BestellungsExtractor


def process_bestellungen():
    """Process bestellungen CSV file and create monthly JSON extracts"""
    
    # Path to the CSV file (hardcoded for simplicity)
    csv_file = Path("../../data/raw/Bestellungen/bulle_2023_04_01-2025_09_02_birke+bistro.csv")
    output_dir = Path("../../data/processed/Bestellungen/")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = BestellungsExtractor()
    
    try:
        print(f"Reading orders from {csv_file.name}...")
        orders = extractor.read_file(csv_file)
        
        # Group orders by month
        orders_by_month = defaultdict(list)
        for order in orders:
            month_key = order.pickup_date.strftime("%Y-%m")
            orders_by_month[month_key].append(order)
        
        # Save each month to separate JSON file
        processed_months = 0
        for month_key, month_orders in orders_by_month.items():
            output_file = output_dir / f"bestellungen_{month_key}.json"
            
            try:
                extractor.convert_to_json(month_orders, output_file)
                print(f"  ✓ Saved {len(month_orders)} orders for {month_key} to {output_file.name}")
                processed_months += 1
            except Exception as e:
                print(f"  ✗ Error saving {month_key}: {e}")
        
        print(f"\nCompleted: {len(orders)} total orders processed")
        print(f"Created {processed_months} monthly files in {output_dir}")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")


if __name__ == "__main__":
    process_bestellungen()