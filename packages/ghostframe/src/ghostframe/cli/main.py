"""GhostFrame main CLI — full pipeline commands.

This is the broader CLI for running the GhostFrame analysis pipeline.
The professor-facing ORF assignment is in cli/orfs.py.
"""

import click


@click.group()
def cli() -> None:
    """GhostFrame — Multi-frame variant impact scanner."""


@cli.command()
def analyze() -> None:
    """Run the GhostFrame analysis pipeline.

    Output table columns: variant_id, frame, old_class, new_class,
    ref_aa, alt_aa, evidence_tier.
    """
    raise NotImplementedError("Pipeline analysis not yet implemented")
