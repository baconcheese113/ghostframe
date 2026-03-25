"""Candidate ranking and scoring for neoantigen prioritization.

Combines MHC binding percentile rank, external evidence tier, and Pfam domain
presence into a single score in [0, 1] per reclassified variant. Higher scores
indicate higher-priority neoantigen candidates.

Pipeline position: mhc.predict() + domain.scan() + evidence.lookup()
    → ranking.scorer.score()
    → ranking.ranker.rank()
    → explain.narrator.explain()
"""
