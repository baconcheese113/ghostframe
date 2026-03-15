"""Multi-frame variant effect reclassification engine.

This is GhostFrame's core value proposition — determining whether a "Silent"
variant becomes non-silent (missense, nonsense) in an overlapping ORF.

Pipeline position: seqfetch → orfs → [reclassify] → peptides
"""
