"""MHC binding prediction adapters.

Wraps external MHC-I binding predictors (MHCflurry, NetMHCpan) to score
mutant peptides for neoantigen potential.

Pipeline position: peptides → [mhc] → reports
Future dependencies: mhcflurry (optional)
"""
