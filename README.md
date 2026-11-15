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

## How the Algorithm Works

Based on the MIT research paper (*Bertsimas & Paskov*), Wordle is modeled as a **Markov Decision Process (MDP)** and solved to provable mathematical optimality using **Exact Dynamic Programming**:

1. **State as Search Space:** 
   The game starts with a pool of all 2,315 possible secret words. Each time a guess is made, Wordle returns tile colors (Green = right spot, Yellow = wrong spot, Gray = not in word). Any word in the pool that does not match this feedback is eliminated, rapidly shrinking the search space.

2. **Bellman Equation (Full Game-Tree Search):**
   Unlike heuristic solvers (like Shannon Entropy) that only look one step ahead, the **Exact DP Solver** considers the entire game tree. It recursively computes the exact expected number of guesses for every playable word using Bellman's equation, selecting the move that guarantees the minimal total guesses to win.

3. **Five Key Optimizations (Overcoming NP-Hardness):**
   Evaluating all combinations is computationally intractable ($2^{2,315}$ states). The paper makes this feasible with 5 core optimizations:
   - **Terminal Horizon Pruning:** At turn 5 (1 guess left), if more than 1 candidate remains, a guaranteed win is impossible and the branch is pruned with infinite cost ($\infty$).
   - **Two-Candidate Shortcut:** When only 2 candidate words remain, guessing either word yields an exact expected cost of 1.5 guesses ($50\% \times 1 + 50\% \times 2$), eliminating further recursive search.
   - **Precomputed Feedback Patterns:** Color responses for all combinations of guesses and solutions are precalculated into memory for instant $O(1)$ lookups.
   - **Theoretical Lower-Bound Pruning:** A mathematical bound $\text{LB}(s) = \frac{2|s| - 1}{|s|}$ determines the absolute best-case outcome of a branch. If this bound already exceeds the best guess found so far, the branch is immediately pruned.
   - **Candidate-First Priority:** Words that are still valid solutions are evaluated first, prioritizing moves with immediate win potential.

4. **Human Interpretability (Decision Trees):**
   Rather than using a "black box" neural network, the policy is represented using **Optimal Classification Trees with Hyperplanes (OCT-H)**. Players can navigate simple visual yes/no questions based on observed tile colors to follow the optimal strategy.

5. **Key Finding:**
   The algorithm proves that **`SALET`** is the globally optimal opening word, achieving an average of **3.421 guesses** and solving every word in $\le 5$ guesses (never losing or needing the 6th guess).

## Project Structure

See [`docs/HIGH_LEVEL_DESIGN.md`](docs/HIGH_LEVEL_DESIGN.md) for the full high-level design document.

## Live Dashboard

https://wordle-ai-project.vercel.app/

## Team Members

| Name | Roll Number |
|---|---|
| Kadali Gagan Venkata Asish | B24EE025 |
| Krishal Sukdeve | B24EE030 |
| Madan Vishwakarma | B24DS504 |
| Pulak Kumar Sarkar | B24DS505 |
| Shlok Divyam | B24CS042 |

