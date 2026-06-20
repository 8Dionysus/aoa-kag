# Post-Release Pattern Harvest

This route defines when a repeated post-release observation may become a KAG
candidate pattern.

## Purpose

Only repeated and verified post-release patterns become KAG candidates.
Isolated incidents stay in memo, eval, release-support, or owner queues.

## Allowed Input

- owner-local release artifact refs;
- evidence refs that survived review;
- repeated post-release observations.

## Output

- `post_release_pattern_candidate` contract payloads;
- owner-routed candidate status.

## Stop Lines

- no forced owner adoption;
- no release execution;
- no proof certification;
- no runtime mutation;
- no Tree-of-Sophia canon write.

## Validation

Use `../VALIDATION.md`.
