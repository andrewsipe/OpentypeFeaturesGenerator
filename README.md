# OpenType Tools

OpenType feature generation and management tools.

## Overview

Unified tool for detecting, generating, and managing OpenType features in fonts. Automatically detects glyph naming patterns and generates appropriate feature code with proper name table labels.

## Scripts

### `Opentype_FeaturesGenerator.py`
**Main OpenType features tool** - Three modes of operation:

1. **Feature Generation (default)**: Automatically detects and adds OpenType features
2. **Audit/Repair Mode**: Audits and repairs existing stylistic sets
3. **Wrapper Subcommand**: Adds minimal OpenType table scaffolding

**Supported Features:**
- Standard Ligatures (liga): f_f, f_i, f_f_i, fi, fl, etc.
- Stylistic Sets (ss01-ss20): .ss01, .ss02, etc. suffixes
- Small Caps (smcp): .sc, .smallcap suffixes
- Old-style Figures (onum): .oldstyle, .onum suffixes
- Lining Figures (lnum): .lining, .lnum suffixes
- Tabular Figures (tnum): .tabular, .tnum suffixes
- Proportional Figures (pnum): .proportional, .pnum suffixes
- Swashes (swsh): .swsh, .swash suffixes
- Discretionary Ligatures (dlig): Complex/decorative ligatures
- Contextual Alternates (calt): Context-sensitive variations

**Usage:**
```bash
# Analyze font (show detected features)
python Opentype_FeaturesGenerator.py font.otf

# Apply all detected features
python Opentype_FeaturesGenerator.py font.otf --apply

# Apply with custom stylistic set labels
python Opentype_FeaturesGenerator.py font.otf --apply -ss "14,Diamond Bullets" -ss "1,Swash Capitals"

# Audit existing stylistic sets
python Opentype_FeaturesGenerator.py font.otf --audit

# Repair existing stylistic sets
python Opentype_FeaturesGenerator.py font.otf --audit --apply -ss "14,Diamond Bullets" --add-missing-params

# Add table scaffolding (wrapper subcommand)
python Opentype_FeaturesGenerator.py wrapper font.otf --enrich --drop-kern

# Process multiple fonts
python Opentype_FeaturesGenerator.py font1.otf font2.otf --apply

# Recursive directory processing
python Opentype_FeaturesGenerator.py /path/to/fonts -R --apply
```

**Options:**
- `--apply` - Apply detected features to the font
- `--audit` - Audit existing stylistic sets for issues
- `-ss, --stylistic-set` - Custom stylistic set label (format: "number,name")
- `--add-missing-params` - Add missing FeatureParams when repairing
- `--enrich` - Enrich font by migrating legacy kern tables
- `--drop-kern` - Drop legacy kern table after migration
- `-R, --recursive` - Process directories recursively
- `--dry-run` - Preview changes without modifying files

## Structure

- `Opentype_FeaturesGenerator.py` - Main entry point script
- `opentype_features/` - Support package with modular components
  - `opentype_features_config.py` - Configuration constants
  - `opentype_features_results.py` - Result handling
  - `opentype_features_validation.py` - Validation framework
  - `opentype_features_detection.py` - Glyph detection engine
  - `opentype_features_extraction.py` - Existing substitution extraction
  - `opentype_features_wrapper.py` - Table scaffolding and enrichment
- `core/` - Included core utilities library

## Dependencies

See `requirements.txt`:
- `fontFeatures` - Font feature processing (optional but recommended)
- `lxml` - XML processing for TTX operations
- Core dependencies (fonttools, rich) provided by included `core/` library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/andrewsipe/OpentypeFeaturesGenerator.git
cd OpentypeFeaturesGenerator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Related Tools

- [FontFileTools](https://github.com/andrewsipe/FontFileTools) - Other font processing utilities
- [FontNameID](https://github.com/andrewsipe/FontNameID) - Update font metadata

