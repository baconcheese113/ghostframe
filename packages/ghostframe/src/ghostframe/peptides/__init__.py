"""Peptide kmer generation for MHC binding prediction.

Generates sliding-window peptides (8-11mers) spanning mutant positions.
Translation itself lives in orfs/sequence.py.

Pipeline position: reclassify → [peptides] → mhc
"""
