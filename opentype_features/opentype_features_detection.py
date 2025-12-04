"""
Unified glyph detection engine.

Single-pass classification of all glyphs for feature detection.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fontTools.agl import toUnicode
from fontTools.ttLib import TTFont

from .opentype_features_config import CONFIG


@dataclass
class GlyphClassification:
    """Classification of a single glyph."""

    name: str
    is_ligature: bool = False
    ligature_components: List[str] = field(default_factory=list)

    is_stylistic_alternate: bool = False
    ss_number: Optional[int] = None
    base_glyph: Optional[str] = None

    is_small_cap: bool = False
    is_figure_variant: bool = False
    figure_variant_type: Optional[str] = None  # onum, lnum, tnum, pnum

    is_swash: bool = False
    is_contextual_alternate: bool = False

    is_mark: bool = False
    mark_class: Optional[str] = None  # combining, accent, etc.


class UnifiedGlyphDetector:
    """Single-pass glyph pattern detector."""

    # Compile patterns once
    SS_PATTERN = re.compile(r"^(.+)\.ss(\d{2})$")
    SC_PATTERN = re.compile(r"^(.+)\.(sc|smallcap)$")
    SWSH_PATTERN = re.compile(r"^(.+)\.(swsh|swash)$")
    CALT_PATTERN = re.compile(r"^(.+)\.(calt|alt)(\d+)?$")
    DLIG_PATTERN = re.compile(r"^(.+)\.dlig$")

    FIGURE_SUFFIXES = {
        "onum": [".oldstyle", ".onum"],
        "lnum": [".lining", ".lnum"],
        "tnum": [".tabular", ".tnum"],
        "pnum": [".proportional", ".pnum"],
    }

    def __init__(self, font: TTFont):
        self.font = font
        self.glyph_order = set(font.getGlyphOrder())
        self.best_cmap = font.getBestCmap() or {}
        self.inv_cmap = self._invert_cmap()

    def _invert_cmap(self) -> Dict[str, List[int]]:
        """Invert cmap: glyph name -> list of codepoints."""
        inv = {}
        for cp, gname in self.best_cmap.items():
            inv.setdefault(gname, []).append(cp)
        return inv

    def classify_all_glyphs(self) -> Dict[str, GlyphClassification]:
        """Classify all glyphs in a single pass."""
        classifications = {}

        for glyph_name in self.glyph_order:
            classification = GlyphClassification(name=glyph_name)

            # Check each pattern
            self._check_ligature(glyph_name, classification)
            self._check_stylistic_set(glyph_name, classification)
            self._check_small_cap(glyph_name, classification)
            self._check_figure_variant(glyph_name, classification)
            self._check_swash(glyph_name, classification)
            self._check_contextual_alternate(glyph_name, classification)
            self._check_mark(glyph_name, classification)

            classifications[glyph_name] = classification

        return classifications

    def _check_ligature(self, glyph_name: str, classification: GlyphClassification):
        """Check if glyph is a ligature."""
        components = self._parse_ligature_components(glyph_name)
        if components:
            classification.is_ligature = True
            classification.ligature_components = components

    def _parse_ligature_components(self, glyph_name: str) -> List[str]:
        """Parse ligature components with validation."""
        import unicodedata

        base = glyph_name.split(".")[0]

        if "_" in base:
            parts = base.split("_")
        elif len(base) == 2 and all(ch.isalpha() for ch in base):
            part1, part2 = base[0], base[1]

            # Check if this is a precomposed Unicode ligature
            try:
                uni = toUnicode(base)
                if uni and len(uni) == 1:
                    cp = ord(uni)
                    name = unicodedata.name(chr(cp), "")
                    if "LIGATURE" in name:
                        return []
            except Exception:
                pass

            if part1 not in self.glyph_order or part2 not in self.glyph_order:
                return []

            parts = [part1, part2]
        else:
            return []

        resolved = []
        for part in parts:
            if part.startswith("uni") and len(part) >= 7:
                hex_part = part[3:7]
                try:
                    codepoint = int(hex_part, 16)
                    glyph = self.best_cmap.get(codepoint)
                    if not glyph:
                        return []
                    resolved.append(glyph)
                except ValueError:
                    return []
            else:
                if part in self.glyph_order:
                    resolved.append(part)
                else:
                    return []

        if len(resolved) < 2:
            return []

        # Validate: at least half components should have Unicode
        valid_components = sum(
            1 for comp in resolved if comp in self.best_cmap.values()
        )
        if valid_components < len(resolved) / 2:
            return []

        return resolved

    def _check_stylistic_set(
        self, glyph_name: str, classification: GlyphClassification
    ):
        """Check if glyph is a stylistic alternate."""
        match = self.SS_PATTERN.match(glyph_name)
        if match:
            base_name = match.group(1)
            ss_num = int(match.group(2))
            if 1 <= ss_num <= 99 and base_name in self.glyph_order:
                classification.is_stylistic_alternate = True
                classification.ss_number = ss_num
                classification.base_glyph = base_name

    def _check_small_cap(self, glyph_name: str, classification: GlyphClassification):
        """Check if glyph is a small cap."""
        match = self.SC_PATTERN.match(glyph_name)
        if match:
            base_name = match.group(1)
            if base_name in self.glyph_order:
                classification.is_small_cap = True
                classification.base_glyph = base_name

    def _check_figure_variant(
        self, glyph_name: str, classification: GlyphClassification
    ):
        """Check if glyph is a figure variant."""
        for variant_type, suffixes in self.FIGURE_SUFFIXES.items():
            for suffix in suffixes:
                if glyph_name.endswith(suffix):
                    base_name = glyph_name[: -len(suffix)]
                    if base_name in self.glyph_order:
                        classification.is_figure_variant = True
                        classification.figure_variant_type = variant_type
                        classification.base_glyph = base_name
                        return

    def _check_swash(self, glyph_name: str, classification: GlyphClassification):
        """Check if glyph is a swash."""
        match = self.SWSH_PATTERN.match(glyph_name)
        if match:
            base_name = match.group(1)
            if base_name in self.glyph_order:
                classification.is_swash = True
                classification.base_glyph = base_name

    def _check_contextual_alternate(
        self, glyph_name: str, classification: GlyphClassification
    ):
        """Check if glyph is a contextual alternate."""
        match = self.CALT_PATTERN.match(glyph_name)
        if match:
            base_name = match.group(1)
            if base_name in self.glyph_order:
                classification.is_contextual_alternate = True
                classification.base_glyph = base_name

    def _check_mark(self, glyph_name: str, classification: GlyphClassification):
        """Check if glyph is a mark."""
        import unicodedata

        # Unicode category check
        if glyph_name in self.inv_cmap:
            for cp in self.inv_cmap[glyph_name]:
                cat = unicodedata.category(chr(cp))
                if cat in ("Mn", "Mc", "Me"):
                    classification.is_mark = True
                    classification.mark_class = "unicode"
                    return

        # Pattern-based detection
        lower = glyph_name.lower()
        for pattern in CONFIG.MARK_PATTERNS:
            if re.match(pattern, lower):
                classification.is_mark = True
                classification.mark_class = "pattern"
                return

    def get_features(self) -> Dict[str, any]:
        """Extract features from classifications."""
        classifications = self.classify_all_glyphs()

        features = {
            "liga": [],
            "dlig": [],
            "stylistic_sets": {},
            "smcp": [],
            "onum": [],
            "lnum": [],
            "tnum": [],
            "pnum": [],
            "swsh": [],
            "calt": [],
        }

        for glyph_name, classification in classifications.items():
            if classification.is_ligature:
                # Check if it's discretionary (has .dlig suffix)
                if self.DLIG_PATTERN.match(glyph_name):
                    features["dlig"].append(
                        (classification.ligature_components, glyph_name)
                    )
                else:
                    features["liga"].append(
                        (classification.ligature_components, glyph_name)
                    )

            if classification.is_stylistic_alternate:
                ss_num = classification.ss_number
                base = classification.base_glyph
                features["stylistic_sets"].setdefault(ss_num, []).append(
                    (base, glyph_name)
                )

            if classification.is_small_cap and classification.base_glyph:
                features["smcp"].append((classification.base_glyph, glyph_name))

            if classification.is_figure_variant and classification.base_glyph:
                variant_type = classification.figure_variant_type
                if variant_type:
                    features[variant_type].append(
                        (classification.base_glyph, glyph_name)
                    )

            if classification.is_swash and classification.base_glyph:
                features["swsh"].append((classification.base_glyph, glyph_name))

            if classification.is_contextual_alternate and classification.base_glyph:
                features["calt"].append((classification.base_glyph, glyph_name))

        return features
