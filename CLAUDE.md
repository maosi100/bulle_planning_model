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

4. **DataValidator** 📋 PLANNED
   - Cross-validation between fiskal and mengenlisten data
   - Plausibility checks and data consistency validation

5. **DataUnifier** 📋 PLANNED
   - Combine and normalize data from both sources
   - Resolve conflicts and create unified dataset

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

### 🔄 Current Phase
Ready to begin **DataValidator** implementation for cross-validation between extractors.