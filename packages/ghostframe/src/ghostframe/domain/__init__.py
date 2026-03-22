"""Domain annotation module for GhostFrame.

Annotates translated ORF protein sequences against Pfam via the
EMBL-EBI HMMER JDispatcher REST API to identify known protein domains.

Pipeline position: reclassify → translate ORF → [domain.hmmer.scan()] → ranking → report
"""
