"""Professor-gradable ORF finder module.

This is the core assignment deliverable — a standalone 6-frame ORF scanner
that reads FASTA input and outputs ORFs in the required format.

It has ZERO dependencies on the rest of the GhostFrame pipeline.
"""

from ghostframe.orfs.fasta import parse_file, parse_text
from ghostframe.orfs.formatter import format_all_orfs, format_orf
from ghostframe.orfs.scanner import find_orfs, find_orfs_in_frame
from ghostframe.orfs.sequence import reverse_complement, translate

__all__ = [
    "find_orfs",
    "find_orfs_in_frame",
    "format_all_orfs",
    "format_orf",
    "parse_file",
    "parse_text",
    "reverse_complement",
    "translate",
]
