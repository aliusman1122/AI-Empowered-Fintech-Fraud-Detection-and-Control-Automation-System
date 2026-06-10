# Fraud Threshold Policy

This file summarizes candidate decision thresholds for fraud-risk review.

## Cost assumptions

- False-positive cost: `1.0`
- False-negative cost: `10.0`
- Interpretation: A false negative is configured as more expensive because missing fraud is usually more costly than reviewing a legitimate transaction.

## Policy candidates

| Policy | Threshold | Precision | Recall | FPR | Flagged rate | Cost | Rationale |
|---|---:|---:|---:|---:|---:|---:|---|
| cost_optimized | 0.350 | 0.481 | 0.974 | 0.130 | 0.223 | 101.000 | Minimizes expected business cost under the configured false-positive and false-negative costs. |
| balanced_f1 | 0.600 | 0.711 | 0.831 | 0.042 | 0.129 | 156.000 | Maximizes F1 to balance precision and recall. |
| high_recall | 0.350 | 0.481 | 0.974 | 0.130 | 0.223 | 101.000 | Maintains recall of at least 95% while minimizing cost. |
| high_precision | 0.600 | 0.711 | 0.831 | 0.042 | 0.129 | 156.000 | Maintains precision of at least 70% while preserving as much recall as possible. |
| review_capacity | 0.700 | 0.769 | 0.649 | 0.024 | 0.093 | 285.000 | Keeps the flagged/review rate at or below 10%. |

## Notes

- These policies are decision-support artifacts, not automatic approval rules.
- Thresholds should be reviewed with business, compliance, and operations stakeholders before deployment.
- The demo dataset is synthetic; threshold values should not be reused for real banking data without validation.
