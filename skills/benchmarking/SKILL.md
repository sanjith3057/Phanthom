# Benchmarking & Evaluations
**Protocol Status**: Active Observation

This directory contains scripts and configurations for evaluating the merged `PHANTOM-3B` models against standard datasets.

### Core Metrics Tracked
- **MMLU (Massive Multitask Language Understanding)**: Evaluates the raw factual capability of the final merge.
- **HumanEval (Python)**: Tests the strength of the Qwen-Coder traits injected into the model.
- **AgentBench / ToolBench**: Measures how accurately PHANTOM triggers its internal `<TOOL_CALL>` tags in response to complex system instructions.

### Usage
Execute benchmarking runs via:
`python src/benchmarks/run_evals.py --model outputs/phantom-slerp`
