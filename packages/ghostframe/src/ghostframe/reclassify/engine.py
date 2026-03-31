"""Core reclassification logic.

For each variant overlapping an ORF, determines whether the variant
changes the encoded amino acid in that frame.

Pipeline position: orfs → [reclassify.engine] → peptides
"""

from ghostframe.models import ORF, FrameEffect, GenomicWindow, NormalizedVariant
from ghostframe.orfs.sequence import reverse_complement
from ghostframe.reclassify import codon_effect

_EFFECT_TO_CLASS: dict[str, str] = {
    "synonymous": "Silent",
    "missense": "Missense",
    "stop_gain": "Stop Gain",
    "stop_loss": "Stop Gain",
    "start_loss": "Start Loss",
}


def reclassify(
    variant: NormalizedVariant,
    orfs: list[ORF],
    window: GenomicWindow,
) -> list[FrameEffect]:
    """Reclassify a variant's effect across all overlapping ORFs.

    Args:
        variant: Normalized variant with standardized coordinates.
            Must be an SNV — only variant.alt[0] is used. Indels and
            multi-nucleotide variants are not supported and will produce
            incorrect results without raising an error.
        orfs: List of ORFs to check for overlap. ORF positions must be
            window-local (1-based index into window.sequence), which is
            the convention used by orfs.scanner.find_orfs().
        window: Genomic window providing the reference sequence context.
            window.start is the 0-based absolute genomic offset of the
            first base of window.sequence.

    Returns:
        List of FrameEffect objects, one per overlapping ORF.
    """
    effects: list[FrameEffect] = []

    for orf in orfs:
        if orf.frame <= 3:
            # Forward strand (frames 1-3)
            orf_start_window = orf.pos - 1
            variant_window_idx = variant.pos - 1 - window.start
            offset_in_orf = variant_window_idx - orf_start_window
        else:
            # Reverse strand (frames 4-6)
            rc_orf_start = abs(orf.pos) - 1
            rc_idx = len(window.sequence) - 1 - (variant.pos - 1 - window.start)
            offset_in_orf = rc_idx - rc_orf_start

        if not (0 <= offset_in_orf < orf.length):
            continue

        codon_idx = offset_in_orf // 3
        base_in_codon = offset_in_orf % 3

        # Guard against incomplete trailing codon
        codon_start = codon_idx * 3
        if codon_start + 3 > len(orf.dna):
            continue

        ref_codon = orf.dna[codon_start : codon_start + 3]

        alt_base = variant.alt[0].upper() if orf.frame <= 3 else reverse_complement(variant.alt[0])

        alt_codon = ref_codon[:base_in_codon] + alt_base + ref_codon[base_in_codon + 1 :]

        effect = codon_effect.compare(ref_codon, alt_codon)
        new_class = _EFFECT_TO_CLASS.get(effect.effect_type, effect.effect_type)

        effects.append(
            FrameEffect(
                orf=orf,
                old_class=variant.classification,
                new_class=new_class,
                ref_aa=effect.ref_aa,
                alt_aa=effect.alt_aa,
                codon_pos=codon_idx,
                ref_codon=ref_codon,
                alt_codon=alt_codon,
            )
        )

    return effects
