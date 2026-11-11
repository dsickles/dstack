# Domain docs

Single-context layout:

- `GLOSSARY.md` at the repo root: the project's words. Use them in code, tickets and specs.
- `docs/adr/NNNN-<slug>.md`: decisions. Read the ADRs in the area you are touching before
  changing it. Status is Accepted, Locked or Superseded; a Locked ADR changes only with
  the owner's explicit yes.
- `docs/architecture.md`: how the system works now. The code wins where they disagree; fix
  the doc in the same PR.
