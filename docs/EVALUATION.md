# Evaluation record

The final paired blind review used 320 historically exposed questions from 47 source clusters. Both arms used R79 and the same generation contract; the graph arm additionally received retrieved public abstract graphs.

This benchmark evaluates the R79 graph add-on only. It is not a semantic acceptance of the newly packaged 1949 + 1978 + R79 full-chain router.

| Metric | Baseline | Graph | Difference |
|---|---:|---:|---:|
| Valid delivery | 320/320 (100%) | 315/320 (98.44%) | -5 questions |
| Core correct | 291/320 (90.94%) | 297/320 (92.81%) | +6 questions / +1.875 pp |
| Whole correct | 165/320 (51.56%) | 215/320 (67.19%) | +50 questions / +15.625 pp |
| Mean score | 3.2625 | 3.49375 | +0.23125 |
| Severe-error questions | 38 | 42 | +4 questions |

The 47-cluster bootstrap interval for mean-score change was `[0.09657, 0.38217]`; for whole-correct change it was `[0.08497, 0.23203]`. Four of six preregistered gates passed. Overall status remained `IMPROVEMENT_NOT_DEMONSTRATED` because five graph answers were terminally invalid and severe-error questions increased from 38 to 42.

Interpretation:

- the abstract graph materially increased whole-answer correctness on this exposed development set;
- it did not establish a production-safe improvement;
- the review is not an independent generalization estimate and not an expert gold standard;
- the public runtime therefore keeps graph use explicit, local and auditable and makes no automatic deployment claim.

