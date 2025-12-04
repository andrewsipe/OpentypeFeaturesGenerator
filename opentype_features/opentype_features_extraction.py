"""
Extract existing substitutions from GSUB table.

Used to avoid duplicate feature generation.
"""

from typing import Dict, Set

from fontTools.ttLib import TTFont


class ExistingSubstitutionExtractor:
    """Extracts all existing substitutions from GSUB."""

    def __init__(self, font: TTFont):
        self.font = font

    def extract_all(self) -> Dict[str, Set]:
        """
        Extract all existing substitutions by type.

        Returns:
            {
                'ligatures': set of component tuples,
                'single': set of (input, output) tuples,
            }
        """
        result = {
            "ligatures": set(),
            "single": set(),
        }

        if "GSUB" not in self.font:
            return result

        gsub = self.font["GSUB"].table
        if not hasattr(gsub, "LookupList") or not gsub.LookupList:
            return result

        for lookup in gsub.LookupList.Lookup:
            if lookup.LookupType == 1:  # Single substitution
                for subtable in lookup.SubTable:
                    if hasattr(subtable, "mapping"):
                        for inp, out in subtable.mapping.items():
                            result["single"].add((inp, out))

            elif lookup.LookupType == 4:  # Ligature substitution
                for subtable in lookup.SubTable:
                    if hasattr(subtable, "ligatures"):
                        for first, lig_list in subtable.ligatures.items():
                            for lig in lig_list:
                                components = tuple([first] + lig.Component)
                                result["ligatures"].add(components)

        return result
