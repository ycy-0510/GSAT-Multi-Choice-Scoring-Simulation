# GSAT Multi-Choice Scoring Simulation (學測多選題評分模擬)

This tool simulates the expected score (Expected Value, EV) for multiple-choice questions (e.g., GSAT/學測) under different guessing strategies. It helps analyze whether it is beneficial to guess additional options given partial knowledge.

## Features

- **Dynamic Probability Model**: Calculates EV based on "at least one correct option" constraint.
- **Customizable Inputs**:
  - $x$: Number of options known to be **Correct** (you select them).
  - $y$: Number of options known to be **Incorrect** (you eliminate them).
  - $z$: Number of additional options to guess (from the remaining pool).
- **Multiple Scoring Rules**:
  - **Custom**: Base 5 points, minus 1 for every difference (False Positive/False Negative). Min 0.
  - **GSAT Standard**: 5 (Perfect), 3 (1 Error), 1 (2 Errors), 0 (>2 Errors).
  - **Strict**: 5 points for perfect match, 0 otherwise.
  - **Empty Selection Rule**: If no options are selected ($x=0, z=0$), score is forced to 0.
- **Advanced Analysis**:
  - **Detailed Stats**: View Mean, Standard Deviation, and Score Distributions.
  - **Monte Carlo Simulation**: Run $N=k$ repeated trials to verify theoretical calculations.

## Installation

This project uses `uv` for dependency management.

```bash
# Install dependencies
uv add streamlit pandas numpy plotly
```

## Usage

Run the Streamlit application:

```bash
uv run streamlit run main.py
```

Open your browser at `http://localhost:8501`.

## How it Works

### The Scenario
A standard 5-option multiple-choice question ($A, B, C, D, E$).
- Each option has a 50% chance of being Correct/Incorrect independently...
- **Constraint**: *At least one* option must be correct (The "All False" case is impossible).

### The Math
1. **State Generation**: We generate all $2^5 = 32$ possible Answer Keys ("Worlds").
2. **Filtering**:
   - Discard the "All False" world (31 remaining).
   - Filter words compatible with user knowledge (must match known $x$ Correct and $y$ Incorrect).
3. **Scoring**:
   - For every possible number of guesses $z$, we compare your selection against all compatible worlds.
   - We calculate the average score (EV) and risk (Standard Deviation).

## License

MIT
