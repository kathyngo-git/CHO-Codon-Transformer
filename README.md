# CHO-Codon-Transformer

Local use of [CodonTransformer](https://github.com/Adibvafa/CodonTransformer) (Fallahpour et al., *Nat Commun* 2025; model `adibvafa/CodonTransformer`) to back-translate antibody chains and signal peptides for expression in CHO.

- `CodonTransformer.ipynb`: unmodified public Colab notebook.
- `predict.py`: batch version of the same call, run locally from a CSV.

## What was established

- The model has 164 organisms and **no Chinese hamster option**. Mus musculus is used as the closest rodent.
- With Mus musculus, `deterministic=True` and `attention_type="original_full"`, previously generated in-house sequences were reproduced **100%** (7 of 8 tested; the eighth had been edited by hand afterwards). Homo sapiens matched only 91 to 95%, so the organism choice matters.
- Against one vendor's CHO-specific optimizer, CodonTransformer (Mus) agrees on about 62 to 68% of codons and is less GC-rich at the third position (GC3 about 78% against about 85%). Check CAI and tAI against a CHO reference before ordering.
- The model has no restriction-site avoidance. Screen the output for the enzymes in your cloning design and fix any hits by hand.

## Setup (once, CPU is sufficient)

```
python -m venv ctv            # keep the path short on Windows (long paths break pip)
ctv\Scripts\activate
pip install CodonTransformer  # pulls torch, transformers; downgrades numpy to 1.26.x
```

First run downloads the model (about 0.5 GB) from Hugging Face. Use a dedicated environment because the numpy pin conflicts with some other packages.

## Optimizing new sequences

1. Write a CSV with columns `name,protein` (optional `organism`). Use the **full protein for each chain** (signal peptide + variable + constant domain), amino acids only, no stop symbol.
2. Run:
   ```
   python predict.py input.csv output.csv --organism "Mus musculus"
   ```
3. `output.csv` holds `name, organism, protein, dna, translation_ok, length_nt`. `translation_ok` must be `True` for every row.
4. The model appends a `TGA` stop codon; `predict.py` removes it unless `--keep-stop` is given. Re-add or replace it to suit the vector.

Rules that matter:

- **Optimize the whole chain at once.** Predictions depend on context: the same signal peptide gets different codons when run alone and when run as part of a full heavy chain. Cut the signal peptide out of the full-chain result instead of optimizing it separately.
- **Keep the settings fixed** (deterministic, `original_full`, same organism) so results are reproducible. Record them with the output.
- `deterministic=False` with a `temperature` (0.2 conservative, 0.8 diverse) and `num_sequences` gives several variants; the notebook shows this. Use it only when you want alternatives to screen.
- Long chains run in under a minute on CPU each; 512 aa is the practical upper bound tested.

## After prediction

Screen every sequence before ordering: CAI, tAI, RCBS, CDC, negative cis elements and repeats, RNA folding (RNAfold MFE, CMFE, ED) and restriction sites to avoid, and confirm the translation matches the intended protein. Keep the final DNA together with its inputs (protein, organism, model settings, date).
