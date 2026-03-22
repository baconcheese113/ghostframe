"""Pfam domain annotation via the EMBL-EBI HMMER JDispatcher REST API.

Submits a protein sequence to the remote hmmscan service, polls until
the job finishes, then parses the domtblout text format into DomainHit
objects.

Rate limits: EBI uses IP-based temporary blocks. We use a linear-backoff
polling loop (3 + attempt seconds). No JSON output is available from this
service; we parse space-delimited domtblout directly.
"""

import time

import httpx

from ghostframe.models import DomainHit

_SUBMIT_URL = "https://www.ebi.ac.uk/Tools/services/rest/hmmer_hmmscan/run"
_BASE_URL = "https://www.ebi.ac.uk/Tools/services/rest/hmmer_hmmscan"
_EMAIL = "ghostframe@example.com"
_EVALUE_CUTOFF = 0.01  # i-Evalue threshold (domtblout column 12)
_MAX_POLL = 30  # max polling attempts (~2 min total)


def scan(protein_seq: str) -> list[DomainHit]:
    """Scan a protein sequence against Pfam via the EMBL-EBI HMMER API.

    Args:
        protein_seq: Amino acid sequence string (uppercase, single-letter codes).

    Returns:
        List of DomainHit objects for Pfam domains with i-Evalue < 0.01,
        sorted by start position. Returns an empty list if no hits pass
        the threshold or the sequence is too short for hmmscan.

    Raises:
        httpx.HTTPError: On network failure or non-2xx response.
        RuntimeError: If the HMMER job fails on the remote server.
    """
    job_id = _submit(protein_seq)
    _wait(job_id)
    return _parse_domtblout(_fetch_domtblout(job_id))


def _submit(protein_seq: str) -> str:
    resp = httpx.post(
        _SUBMIT_URL,
        data={"email": _EMAIL, "sequence": protein_seq, "database": "pfam-a"},
        timeout=30.0,
    )
    resp.raise_for_status()
    job_id = resp.text.strip()
    if job_id.startswith("<"):
        # XML error response
        raise RuntimeError(f"HMMER submission failed: {job_id}")
    return job_id


def _wait(job_id: str) -> None:
    for attempt in range(_MAX_POLL):
        resp = httpx.get(f"{_BASE_URL}/status/{job_id}", timeout=10.0)
        resp.raise_for_status()
        status = resp.text.strip()
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"HMMER job {job_id} failed on remote server")
        time.sleep(3 + attempt)
    raise RuntimeError(f"HMMER job {job_id} did not finish after {_MAX_POLL} polls")


def _fetch_domtblout(job_id: str) -> str:
    resp = httpx.get(f"{_BASE_URL}/result/{job_id}/domtblout", timeout=30.0)
    resp.raise_for_status()
    return resp.text


def _parse_domtblout(text: str) -> list[DomainHit]:
    hits: list[DomainHit] = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = line.split()
        if len(cols) < 19:
            continue
        try:
            i_evalue = float(cols[12])
        except ValueError:
            continue
        if i_evalue >= _EVALUE_CUTOFF:
            continue
        # Strip Pfam version suffix: "PF00071.29" → "PF00071"
        accession = cols[1].split(".")[0]
        hits.append(
            DomainHit(
                accession=accession,
                name=cols[0],
                start=int(cols[17]),
                end=int(cols[18]),
                score=float(cols[13]),
            )
        )
    hits.sort(key=lambda h: h.start)
    return hits
