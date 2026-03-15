"""Professor-facing ORF finder CLI.

Complies exactly with the assignment spec:
  - Reads a FASTA file
  - Asks for minimum ORF length (default 50)
  - Prints ORFs in the required format
"""

import click

from ghostframe.orfs.fasta import parse_file
from ghostframe.orfs.formatter import format_all_orfs
from ghostframe.orfs.scanner import find_orfs


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--min-len",
    prompt="Minimum ORF length (bases)",
    default=50,
    show_default=True,
    type=int,
    help="Minimum ORF length in bases.",
)
def main(input_file: str, min_len: int) -> None:
    """Find all open reading frames in a FASTA file across 6 reading frames."""
    records = parse_file(input_file)

    for record in records:
        orfs = find_orfs(record.sequence, min_length=min_len)
        output = format_all_orfs(record, orfs)
        if output:
            click.echo(output)
