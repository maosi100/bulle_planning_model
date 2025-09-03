# Bulle Planning Model - Development Context

## Project Architecture & Current State

**Business Purpose**: Bakery sales prediction model using historical data from registers, shift reports, and orders.

**Current Phase**: Phase 1 Complete (Data Processing) - Ready for Phase 2 (Model Development)

**Data Sources**:
1. **Fiskaljournale** - Register transaction data (.txt → JSON)
2. **Mengenlisten** - Employee shift reports (.pdf → JSON via Gemini API)
3. **Bestellungen** - Customer orders (.csv → JSON)

**Processing Pipeline**: Raw Data → Individual Extractors → Processed JSON → DataUnifier → Consolidated Data

## Key Implementation Decisions Made

**Error Handling Strategy**: Individual entry failures don't break entire file processing (resilient parsing)
**Price Handling**: Bestellungen prices converted from cents to euros (660 cents = €6.60)
**Data Unification**: Uses lookup table (`data/master/lookup_table.json`) to map article variants to master articles
**QC Strategy**: All unmapped/unparsed items saved to `../../data/processed/qc/` for review
**API Management**: Gemini API calls include 5-second rate limiting

## Component Status & Technical Details

### ✅ Extractors (Complete)
**FiskalExtractor** (`src/extractors/fiskal_extractor/`)
- Parses "Rechnung" blocks from register .txt files
- Handles German encoding with `chardet`
- Outputs transaction JSON with LineItem arrays

**MengenlistenExtractor** (`src/extractors/mengenlisten_extractor/`)
- Uses Gemini 2.5 Flash API for PDF → structured JSON
- Individual entry error handling (skips invalid, keeps valid)
- Date-keyed JSON output format

**BestellungsExtractor** (`src/extractors/bestellungs_extractor/`)
- CSV processing with price conversion (cents → euros)
- Groups by order UUID, outputs monthly JSON files

### ✅ Data Unification (Complete)
**DataUnifier** (`src/data_unifier/`)
- Combines all three data sources by date
- Maps articles using `ArticleLookupTable` (249 variant mappings)
- Returns `(consolidated_data, unmapped_data)` tuple
- Creates `ConsolidatedProductData` objects per date

### ✅ Production Scripts (Complete)
**Core Processing Scripts**:
- `process_fiskaljournale.py` - .txt → JSON
- `process_mengenlisten.py` - .pdf → JSON (with API rate limiting)  
- `process_bestellungen.py` - .csv → monthly JSON
- `process_unified_data.py` - unified processing + QC file generation

**Helper Scripts**:
- `reprocess_unparsed_mengenlisten.py` - retry failed PDFs
- `extract_unmapped_bestellungen.py` - analyze unmapped items

## File Structure & Key Classes

### Data Models (Pydantic)
```
ConsolidatedProductData  # Daily unified data with total_revenue + master_articles
MasterArticleData       # Article data with sales, quantity, leftover, sold_out_time
ArticleLookupTable     # Maps article variants to master names (249 mappings)
Transaction, LineItem   # Fiskal data models
Mengenliste, MengenlisteEntry # Mengenlisten data models  
Order, BestellungLineItem # Bestellungen data models
```

### Key Method Signatures
```python
# DataUnifier - returns unmapped data for QC handling
def unify_monthly_data(fiskal_path, mengenlisten_dir, bestellungen_path=None) -> Tuple[Dict[str, ConsolidatedProductData], Dict[str, Dict[str, List[str]]]]

# All Extractors follow this pattern
def read_file(file_path: Path) -> List[DataModel]
def convert_to_json(data: List[DataModel], output_path: Path) -> None
```

### Directory Structure
```
src/bulle_planning_model/
├── extractors/
│   ├── fiskal_extractor/        # Register data processing
│   ├── mengenlisten_extractor/  # PDF shift reports (Gemini API)
│   └── bestellungs_extractor/   # Order CSV processing
├── data_unifier/               # Combines all data sources
├── process_*.py               # Production scripts
└── test_*.py                 # Test scripts (legacy)

data/
├── raw/           # Input data files  
├── processed/     # Generated JSON files
│   ├── qc/       # Quality control & unmapped items
│   └── master/   # lookup_table.json (249 mappings)
```

## Next Development Phase

**Ready for**: Phase 2 - Model Development
- Feature engineering from consolidated data
- Predictive model creation  
- Sales forecasting implementation

**Technical debt**: None - all components production ready
**Testing**: Integration tests available for core extractors