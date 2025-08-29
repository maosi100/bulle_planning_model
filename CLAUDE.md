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

2. **MengenlistenExtractor** 🔄 NEXT
   - OCR processing of PDF shift reports
   - Data extraction and validation
   - JSON output format alignment

3. **DataValidator** 📋 PLANNED
   - Cross-validation between fiskal and mengenlisten data
   - Plausibility checks and data consistency validation

4. **DataUnifier** 📋 PLANNED
   - Combine and normalize data from both sources
   - Resolve conflicts and create unified dataset

### Phase 2: Model Development
- **Feature Engineering**: Extract relevant predictive features
- **Model Creation**: Build sales forecasting models

## Current Status

### ✅ FiskalExtractor - Complete & Production Ready

**Implementation Details:**
- **Architecture**: Clean separation with individual model files
- **Processing**: Memory-efficient streaming for large files (tested on real data)
- **Encoding**: Automatic detection using `chardet` for German text
- **Data Models**: Pydantic validation for type safety
- **Core Logic**: Parses "Rechnung" blocks from start to "Signatur:" markers
- **JSON Output**: Complete article data including names, matching specification
- **Quality Assurance**: Captures unparsed blocks for stakeholder review

**Key Methods:**
- `read_file()`: Main processing interface
- `convert_to_json()`: Structured JSON export
- `save_unparsed_blocks()`: QA feature for missed transactions

**Testing**: Validated on April 2023 fiskal data - fast performance confirmed

### 🔄 Current Phase
Ready to begin **MengenlistenExtractor** implementation for PDF processing.