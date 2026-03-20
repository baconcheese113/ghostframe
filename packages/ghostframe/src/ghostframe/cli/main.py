"""GhostFrame main CLI — full pipeline commands.

This is the broader CLI for running the GhostFrame analysis pipeline.
The professor-facing ORF assignment is in cli/orfs.py.
"""

from pathlib import Path

import click

from ghostframe.pipeline import fast_lane
from ghostframe.reports import export


@click.group()
def cli() -> None:
    """GhostFrame — Multi-frame variant impact scanner."""


@cli.command()
@click.argument("maf", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--fasta",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Reference FASTA path.",
)
@click.option(
    "--min-len",
    default=50,
    show_default=True,
    type=int,
    help="Minimum ORF length (bases).",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file (.json or .tsv).",
)
def analyze(maf: Path, fasta: Path | None, min_len: int, output: Path | None) -> None:
    """Run the GhostFrame fast lane analysis pipeline."""
    result = fast_lane.run(maf, fasta, min_len)

    n = len(result.reclassified_variants)
    click.echo(f"Variants processed: {n} reclassification effects found")
    click.echo("")
    if result.summary.sankey_data:
        click.echo(f"{'From':<30} {'To':<30} {'Count':>6}")
        click.echo("-" * 68)
        for row in result.summary.sankey_data:
            click.echo(f"{row['from']:<30} {row['to']:<30} {row['count']:>6}")
    else:
        click.echo("No reclassifications found in the silent variant windows.")

    if output is not None:
        if str(output).endswith(".json"):
            export.to_json(result, output)
        else:
            export.to_tsv(result, output)
        click.echo(f"\nResults written to {output}")
