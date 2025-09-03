# Bulle Planning Model

A Python application for predicting bakery sales based on historical data from multiple sources.

## Project Overview

This application combines data from two primary sources to build predictive models for bakery sales:

1. **Fiskaljournale** - Monthly register extracts in .txt format containing transaction data
2. **Mengenlisten** - PDF files of paper shift reports filled out by employees, processed via OCR

## Architecture

The application follows a two-phase approach:

### Phase 1: Data Extraction & Processing
- **FiskalExtractor**: Processes .txt register files into structured JSON
- **MengenlistenExtractor**: Uses OCR to extract data from PDF shift reports into JSON  
- **DataValidator**: Validates extracted data for consistency and completeness
- **DataUnifier**: Combines and normalizes data from both sources

### Phase 2: Model Development
- **Feature Engineering**: Identifies and extracts relevant features from unified data
- **Model Creation**: Builds predictive models for sales forecasting

## Data Flow

```
Fiskaljournale (.txt) → FiskalExtractor → JSON
Mengenlisten (.pdf) → MengenlistenExtractor (OCR) → JSON
                                ↓
                         DataValidator → Plausibility Check
                                ↓  
                         DataUnifier → Combined JSON
                                ↓
                    Feature Engineering → Model Training
```

## Implementation Plan

### Phase 1: Data Extraction & Processing
1. **FiskalExtractor** ✅ COMPLETE
   - Pydantic data models (LineItem, Transaction, ExtractMetadata)
   - Generator-based file processing with encoding detection
   - Transaction block parsing (UUID, date, bill number, items, totals)
   - JSON serialization matching diagram specification
   - Quality assurance with unparsed block capture

2. **MengenlistenExtractor** ✅ COMPLETE
   - Gemini API integration for direct PDF processing
   - Pydantic data models (Mengenliste, MengenlisteEntry, MengenlisteMetadata)
   - JSON output format with date-keyed structure
   - Robust error handling and unparsed block tracking

3. **Integration Tests** ✅ COMPLETE
   - Comprehensive unittest-based integration tests for both extractors
   - Real test data validation using actual files
   - Single API call optimization for MengenlistenExtractor tests
   - Graceful handling of missing API keys

4. **DataUnifier** ✅ COMPLETE
   - Processes monthly fiskal extracts and mengenlisten directories
   - Creates consolidated daily product data (one ConsolidatedProductData per date)
   - Uses existing lookup tables for article name mapping to master articles
   - Generates quality control files for unmapped items
   - Monthly processing with JSON output capability

### Phase 2: Model Development
- **Feature Engineering**: Extract relevant predictive features
- **Model Creation**: Build sales forecasting models

## Current Status

### ✅ FiskalExtractor - Complete & Production Ready

**Implementation Details:**
- **Architecture**: Clean separation with individual model files
- **Processing**: Memory-efficient streaming for large files
- **Encoding**: Automatic detection using `chardet` for German text
- **Data Models**: Pydantic validation for type safety
- **Core Logic**: Parses "Rechnung" blocks from start to "Signatur:" markers
- **JSON Output**: List format with complete transaction data
- **Quality Assurance**: Captures unparsed blocks for stakeholder review

### ✅ MengenlistenExtractor - Complete & Production Ready

**Implementation Details:**
- **Architecture**: Modular design with separate client, models, and extractor
- **API Integration**: Google Gemini 2.5 Flash for direct PDF processing
- **Data Models**: Pydantic validation (Mengenliste, MengenlisteEntry, MengenlisteMetadata)
- **Core Logic**: Structured prompt engineering for German bakery terminology
- **JSON Output**: Date-keyed format with production/sales day tracking
- **Error Handling**: Robust fallback with unparsed block capture

### ✅ Integration Tests - Complete

**Testing Coverage:**
- **FiskalExtractor**: 5 comprehensive integration tests using real journal data
- **MengenlistenExtractor**: 5 optimized tests with single API call sharing
- **Test Organization**: Consolidated test files in `tests/test_files/`
- **API Handling**: Graceful skipping when GEMINI_API_KEY unavailable

### ✅ DataUnifier - Complete & Production Ready

**Implementation Details:**
- **Architecture**: Modular design with separate data models and lookup table handling
- **Data Models**: ConsolidatedProductData, MasterArticleData, ArticleLookupTable (Pydantic)
- **Lookup Integration**: Uses existing `data/master/lookup_table.json` with 249 variant mappings
- **Core Logic**: Monthly processing - processes full fiskal extract + mengenlisten directory
- **Date Grouping**: Groups fiskal transactions by date, loads mengenlisten files by date
- **Data Merging**: Combines both sources into daily ConsolidatedProductData objects
- **Quality Control**: Unmapped items written to `data/qc/unmapped_items_YYYY-MM-DD.json`
- **JSON Output**: `write_monthly_consolidated_data()` method for serialization

**Key Methods:**
- `unify_monthly_data(fiskal_extract_path, mengenlisten_dir_path)` - Main processing method
- `write_monthly_consolidated_data(consolidated_data, output_path)` - JSON export
- Handles mengenlisten-only articles (creates entries with zero sales)
- Proper fiskal transaction parsing from extractor JSON format

**File Structure:**
```
src/bulle_planning_model/data_unifier/
├── consolidated_product_data.py  # ConsolidatedProductData model
├── master_article_data.py        # MasterArticleData model  
├── article_lookup_table.py       # ArticleLookupTable model
└── data_unifier.py              # Main DataUnifier class
```

### 🔄 Current Phase
DataUnifier complete and tested. Ready for Phase 2: Model Development.