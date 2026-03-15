"""Reference sequence retrieval — local FASTA or remote APIs.

Fetches genomic windows around variants for ORF scanning.

Pipeline position: variants.normalize → [seqfetch] → orfs → reclassify
"""
