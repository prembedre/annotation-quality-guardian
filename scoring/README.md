# 📊 Scoring Engine — Annotation Quality Guardian

## Overview

The scoring module computes quality metrics for annotation data. It is organized into four sub-modules, each targeting a different dimension of quality.

## Sub-modules

| Directory      | Description                                  | Status       |
|----------------|----------------------------------------------|--------------|
| `gold_checker` | Gold-standard validation (accuracy vs. gold) | ✅ Active    |
| `agreement`    | Inter-annotator agreement (Cohen/Fleiss κ)   | ✅ Active    |
| `behavior`     | Behavioral anomaly detection                 | 🔜 Planned  |
| `embeddings`   | Embedding-based outlier detection            | 🔜 Planned  |

## Usage

```python
from scoring.gold_checker.checker import gold_accuracy
from scoring.agreement.kappa import cohens_kappa, fleiss_kappa

# Gold-standard accuracy
accuracy = gold_accuracy(annotations, gold_items)

# Inter-annotator agreement
kappa = cohens_kappa(annotator_a_labels, annotator_b_labels)
```
