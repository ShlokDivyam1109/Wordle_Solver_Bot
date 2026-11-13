# An Exact and Interpretable Solution to Wordle

Implementation of the Exact Dynamic Programming framework from Bertsimas & Paskov (MIT) for solving Wordle optimally.

## Overview

This project implements:

1. **Exact DP Solver** — Certifiably optimal Wordle policy via Bellman recursion with 5 key optimizations.
2. **Metrics & Testing** — Rigorous validation reproducing the paper's results (SALET, avg 3.421 guesses, 100% win rate in ≤5 guesses).
3. **Interpretability** — Optimal Classification Trees with Hyperplanes (OCT-H) for human-readable policy representation.
4. **Interactive Dashboard** — Web-based animated visualization of the step-by-step solving process.

## Paper

> *"An Exact and Interpretable Solution to Wordle"*
> Dimitris Bertsimas & Alex Paskov — MIT

## Key Results (Target)

| Metric | Value |
|---|---|
| Best starting word | SALET |
| Average guesses | 3.421 |
| Maximum guesses | 5 |
| Win rate | 100% |

## Project Structure

See [`docs/HIGH_LEVEL_DESIGN.md`](docs/HIGH_LEVEL_DESIGN.md) for the full high-level design document.

## Live Dashboard

https://wordle-ai-project.vercel.app/

## License

TBD

