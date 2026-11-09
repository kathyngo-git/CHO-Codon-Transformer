# CHO-Codon-Transformer

Local use of [CodonTransformer](https://github.com/Adibvafa/CodonTransformer) (Fallahpour et al., *Nat Commun* 2025; model `adibvafa/CodonTransformer`) to back-translate antibody chains and signal peptides for expression in CHO.

- `CodonTransformer.ipynb`: unmodified public Colab notebook.
- `predict.py`: batch version of the same call, run locally from a CSV.

## What was established

- The model has 164 organisms and **no Chinese hamster option**. Mus musculus is used as the closest rodent.
- With Mus musculus, `deterministic=True` and `attention_type="original_full"`, previously generated in-house sequences were reproduced **100%** (7 of 8 tested; the eighth had been edited by hand afterwards). Homo sapiens matched only 91 to 95%, so the organism choice matters.
- Against one vendor's CHO-specific optimizer, CodonTransformer (Mus) agrees on about 62 to 68% of codons and is less GC-rich at the third position (GC3 about 78% against about 85%). Check CAI and tAI against a CHO reference before ordering.
- The model has no restriction-site avoidance. Screen the output for the enzymes in your cloning design and fix any hits by hand.

## Running locally (no Colab, no GPU needed)

Everything runs on your own machine. Sequences are never uploaded; the only network use is the one-time model download.

Tested on Windows 11, Python 3.12, CPU only (PyTorch 2.12, numpy 1.26.4).

**1. Create an environment (once).** Put it at a short path, because Windows long-path limits make `pip` fail in deeply nested folders:
```
python -m venv %TEMP%\ctv
%TEMP%\ctv\Scripts\python.exe -m pip install CodonTransformer
```
The package pulls in `torch` and `transformers` and pins numpy to 1.26.x, which can break other packages that need numpy 2 (for example `zarr`). A dedicated environment avoids that. Add `--system-site-packages` to the `venv` command to reuse an existing PyTorch install instead of downloading it again.

**2. First run downloads the model (once).** About 0.5 GB from Hugging Face, cached under `%USERPROFILE%\.cache\huggingface`. After that it works offline; set `HF_HUB_OFFLINE=1` to force this.

**3. Run it.**
```
%TEMP%\ctv\Scripts\python.exe predict.py input.csv output.csv --organism "Mus musculus"
```
In PowerShell use `& "$env:TEMP\ctv\Scripts\python.exe" predict.py ...`. If the console shows encoding errors, set `PYTHONIOENCODING=utf-8` first. Harmless `GenerationMixin` warnings from transformers appear on every run.

Speed on CPU (measured, once the model is cached): import and model load about 6 s, then 0.2 s for a 19 aa peptide and 0.5 s for a 473 aa chain. A GPU is used automatically if PyTorch can see one.

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
- 512 aa is the longest input tested.

## After prediction

Screen every sequence before ordering: CAI, tAI, RCBS, CDC, negative cis elements and repeats, RNA folding (RNAfold MFE, CMFE, ED) and restriction sites to avoid, and confirm the translation matches the intended protein. Keep the final DNA together with its inputs (protein, organism, model settings, date).
