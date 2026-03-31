import { expect, test } from '@playwright/test';

type EffectClass = 'Missense' | 'Silent' | 'Stop Gain' | 'Start Loss';

function buildVariant(
  index: number,
  gene: string,
  newClass: EffectClass,
  overrides: Partial<Record<string, unknown>> = {},
) {
  return {
    id: overrides.id ?? `${gene}_${((index % 6) + 1).toString()}_${(7000 + index).toString()}`,
    gene,
    position: overrides.position ?? 7000 + index,
    frame: overrides.frame ?? (((index % 6) + 1) as 1 | 2 | 3 | 4 | 5 | 6),
    old_class: 'Silent' as const,
    new_class: newClass,
    ref_codon: 'GCC',
    alt_codon: 'GTC',
    ref_aa: overrides.ref_aa ?? 'A',
    alt_aa: overrides.alt_aa ?? 'V',
    evidence_tier: (overrides.evidence_tier ?? 1) as 1 | 2 | 3,
    synmicdb_score: (overrides.synmicdb_score as number | null | undefined) ?? null,
    clinvar_significance: (overrides.clinvar_significance as string | null | undefined) ?? null,
    narrative: `${gene} interpretation`,
    peptides: Array.isArray(overrides.peptides) ? overrides.peptides : [],
    orf_dna: 'ATGGCCGCCTAAATGGCCGCCTAAATGGCCGCCTAA',
    orf_pos: (overrides.orf_pos as number | undefined) ?? 1,
    orf_length: (overrides.orf_length as number | undefined) ?? 36,
    window_size: 60,
    variant_in_window: 30,
    codon_pos: (overrides.codon_pos as number | null | undefined) ?? 1,
    chrom: (overrides.chrom as string | undefined) ?? '17',
    ref: 'G',
    alt: 'T',
  };
}

function buildDefaultEvents() {
  const variants = [
    buildVariant(0, 'GENE_SHARED', 'Missense', {
      id: 'GENE_SHARED_1_7000',
      position: 7000,
      frame: 1,
      ref_aa: 'A',
      alt_aa: 'V',
      synmicdb_score: 2.4,
      clinvar_significance: 'Pathogenic',
    }),
    buildVariant(1, 'GENE_SHARED', 'Stop Gain', {
      id: 'GENE_SHARED_4_7000',
      position: 7000,
      frame: 4,
      ref_aa: 'Q',
      alt_aa: '*',
      synmicdb_score: -0.6,
    }),
    buildVariant(2, 'GENE_NOBIND', 'Missense', {
      id: 'GENE_NOBIND_2_7100',
      position: 7100,
      frame: 2,
      ref_aa: 'R',
      alt_aa: 'H',
    }),
    buildVariant(3, 'GENE_ENRICH', 'Start Loss', {
      id: 'GENE_ENRICH_3_7200',
      position: 7200,
      frame: 3,
      ref_aa: 'M',
      alt_aa: 'V',
    }),
    ...Array.from({ length: 19 }, (_, index) => buildVariant(index + 4, `GENE_${index + 4}`, 'Silent')),
  ];

  const variantWindows = Object.fromEntries(
    variants.map((variant) => [`${variant.gene}_${variant.position}`, 'ATG'.repeat(30)]),
  );

  const events = [
    {
      type: 'running',
      name: 'MAF / FASTA',
      detail: 'Loading analysis input',
      elapsed_ms: 0,
    },
    {
      type: 'step',
      name: 'MAF / FASTA',
      status: 'success',
      detail: '23 variants in 0.01s',
      elapsed_ms: 10,
    },
    {
      type: 'running',
      name: 'Domain & Evidence',
      detail: 'HMMER 2/4, OpenProt 2/3, ClinVar 1/3, SynMICdb 1/3 in 0.50s',
      elapsed_ms: 500,
      progress_current: 6,
      progress_total: 13,
    },
    {
      type: 'fast_complete',
      job_id: 'demo1234',
      variants,
      summary: {
        total_input_variants: 1233,
        total_silent_variants: 248,
        total_orfs: 2158,
        total_effects: 432,
        reclassified_effects: 217,
        total_silent: 248,
        reclassified: 217,
        frames_affected: 5,
        best_ic50: null,
      },
      variant_windows: variantWindows,
      analysis_meta: {
        primary_label: 'TCGA-B5-A11H-01A-11D-A122-09',
        secondary_label: 'maf-76a53025-e904-4a46-a8f9-175ecf74b687.wxs.aliquot_ensemble_masked.maf',
        sample_count: 1,
        variant_count: 1233,
        is_demo: false,
        hla_alleles: ['HLA-A*02:01'],
      },
    },
    {
      type: 'enrich_complete',
      variant_id: 'GENE_SHARED_1_7000',
      elapsed_ms: 120,
      candidates: [
        {
          peptide_sequence: 'GILGFVFTL',
          allele: 'HLA-A*02:01',
          ic50: 12.4,
          rank: 0.9,
          score: 0.91,
          domain_hits: [],
        },
      ],
      evidence: {
        tier: 3,
        openprot_accession: 'IP_000001',
        openprot_type: 'altORF',
        synmicdb_score: 2.4,
        clinvar_significance: 'Pathogenic',
      },
    },
    {
      type: 'enrich_complete',
      variant_id: 'GENE_SHARED_4_7000',
      elapsed_ms: 160,
      candidates: [
        {
          peptide_sequence: 'LLFGYPVSL',
          allele: 'HLA-A*02:01',
          ic50: 41.0,
          rank: 1.8,
          score: 0.82,
          domain_hits: [],
        },
      ],
      evidence: {
        tier: 2,
        openprot_accession: 'IP_000002',
        openprot_type: 'altORF',
        synmicdb_score: -0.6,
        clinvar_significance: null,
      },
    },
    {
      type: 'enrich_complete',
      variant_id: 'GENE_NOBIND_2_7100',
      elapsed_ms: 180,
      candidates: [
        {
          peptide_sequence: null,
          allele: null,
          ic50: null,
          rank: null,
          score: 0.12,
          domain_hits: [],
        },
      ],
      evidence: {
        tier: 1,
        openprot_accession: null,
        openprot_type: null,
        synmicdb_score: null,
        clinvar_significance: 'Uncertain significance',
      },
    },
    {
      type: 'step',
      name: 'Domain & Evidence',
      status: 'success',
      detail: '3/4 variants enriched in 0.75s',
      elapsed_ms: 750,
    },
    {
      type: 'complete',
    },
  ];

  return events.map((event) => JSON.stringify(event)).join('\n');
}

test.describe('GhostFrame dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/analyze', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/x-ndjson',
        body: buildDefaultEvents(),
      });
    });
  });

  test('shows the default analysis label before a run', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('analysis-label')).toContainText('Awaiting analysis');
    await expect(page.getByTestId('empty-state-explainer')).toContainText(
      'GhostFrame revisits mutations labeled "Silent"',
    );
  });

  test('pipeline trace shows user-facing deep-analysis steps and a progress bar', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();
    const trace = page.getByTestId('pipeline-trace');
    await expect(trace).toBeVisible();
    await expect(trace.getByText('Peptides').first()).toBeVisible();
    await expect(trace.getByText('MHC Binding').first()).toBeVisible();
    await expect(trace.getByText('Domain & Evidence').first()).toBeVisible();
    await expect(trace.getByText('Rank & Score').first()).toBeVisible();
    await expect(page.getByTestId('pipeline-progress')).toBeVisible();
  });

  test('demo analysis hides the setup bar, updates the run label, and shows HLA context', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    await expect(page.getByTestId('analysis-label')).toContainText('TCGA-B5-A11H-01A-11D-A122-09');
    await expect(page.getByText('Configure New Analysis')).toHaveCount(0);
    await expect(page.getByTestId('variant-table-hla-note')).toContainText('HLA-A*02:01');
  });

  test('table defaults to reclassified ORF effects and explains the count chain', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    await expect(page.getByTestId('count-explainer')).toContainText(
      '1233 input variants -> 248 silent variants -> 2158 ORFs scanned -> 432 ORF effects -> 217 reclassified effects',
    );
    await expect(page.getByTestId('effect-row-helper')).toContainText('Each row is an ORF effect');
    await expect(page.locator('select')).toHaveValue('__reclassified__');
    await expect(page.getByText('4 of 432 ORF effects')).toBeVisible();
  });

  test('table shows ClinVar and SynMICdb signals without fake 0 nM values', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    await expect(page.locator('tr[data-row-status="scored"]', { hasText: 'GENE_SHARED' })).toHaveCount(2);
    await expect(page.locator('tr[data-row-status="no_binding"]', { hasText: 'GENE_NOBIND' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'ClinVar' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'SynMICdb' })).toBeVisible();
    await expect(page.locator('text=0 nM')).toHaveCount(0);
    await expect(page.locator('tr', { hasText: 'GENE_NOBIND' })).toContainText('No binder');
    await expect(page.locator('tr', { hasText: 'GENE_SHARED' }).first()).toContainText('Pathogenic');
    await expect(page.locator('tr', { hasText: 'GENE_SHARED' }).first()).toContainText('2.40');
    await expect(page.locator('tr', { hasText: 'GENE_SHARED' }).first()).toContainText('SynMIC');
  });

  test('selecting two rows at the same locus changes the selected-frame treatment', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    const rows = page.locator('tbody tr', { hasText: 'GENE_SHARED' });
    await rows.nth(0).click();
    await expect(page.getByTestId('selected-effect-label')).toContainText('Frame 1 / Missense / A->V');

    await rows.nth(1).click();
    await expect(page.getByTestId('selected-effect-label')).toContainText(
      'Frame 4 / Stop Gain / Q->STOP (*)',
    );
    await expect(page.getByTestId('selected-effect-badge')).toContainText('Frame 4 focus');
  });

  test('ClinVar and SynMICdb columns are sortable evidence signals', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    await page.getByRole('columnheader', { name: 'ClinVar' }).click();
    await expect(page.locator('tbody tr').first()).toContainText('GENE_SHARED');

    await page.getByRole('columnheader', { name: 'SynMICdb' }).click();
    await expect(page.locator('tbody tr').first()).toContainText('GENE_SHARED');
  });

  test('gene sorting works again in the compact table', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    await page.getByRole('columnheader', { name: 'Gene' }).click();
    await expect(page.locator('tbody tr').first()).toContainText('GENE_ENRICH');
  });

  test('reading-frame viewer explains START, STOP, and stop-codon symbols', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();

    const rows = page.locator('tbody tr', { hasText: 'GENE_SHARED' });
    await rows.nth(1).click();

    await expect(page.getByTestId('selected-effect-label')).toContainText('STOP (*)');
    await expect(page.getByTestId('reading-frame-viewer')).toContainText(
      '* in amino-acid labels also means stop codon',
    );
  });

  test('progress bar supports indeterminate and determinate running states', async ({ page }) => {
    await page.unroute('**/api/analyze');
    await page.route('**/api/analyze', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/x-ndjson',
        body: [
          JSON.stringify({
            type: 'running',
            name: 'MAF / FASTA',
            detail: 'Loading analysis input',
            elapsed_ms: 0,
          }),
        ].join('\n'),
      });
    });

    await page.goto('/');
    await page.getByRole('button', { name: /Use Demo Data/i }).click();
    await expect(page.getByTestId('pipeline-progress')).toHaveAttribute('data-progress-mode', 'indeterminate');

    await page.unroute('**/api/analyze');
    await page.route('**/api/analyze', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/x-ndjson',
        body: [
          JSON.stringify({
            type: 'running',
            name: 'Domain & Evidence',
            detail: 'HMMER 2/4, OpenProt 2/3, ClinVar 1/3, SynMICdb 1/3 in 0.50s',
            elapsed_ms: 500,
            progress_current: 6,
            progress_total: 13,
          }),
        ].join('\n'),
      });
    });

    await page.reload();
    await page.getByRole('button', { name: /Use Demo Data/i }).click();
    await expect(page.getByTestId('pipeline-progress')).toHaveAttribute('data-progress-mode', 'determinate');
  });
});
