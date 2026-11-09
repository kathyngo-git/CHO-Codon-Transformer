"""Run CodonTransformer locally on a CSV of protein sequences.

Input CSV columns: name, protein   (optional column: organism)
Output CSV columns: name, organism, protein, dna, translation_ok, length_nt

    python predict.py input.csv output.csv [--organism "Mus musculus"] [--keep-stop]
"""
import argparse
import csv
import warnings

import torch
from transformers import AutoTokenizer, BigBirdForMaskedLM
from CodonTransformer.CodonPrediction import predict_dna_sequence

warnings.filterwarnings("ignore")

BASES = "TCAG"
AAS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
CODON = {a + b + c: AAS[i] for i, (a, b, c) in enumerate((x, y, z) for x in BASES for y in BASES for z in BASES)}


def translate(dna):
    return "".join(CODON.get(dna[i:i + 3], "X") for i in range(0, len(dna) - len(dna) % 3, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--organism", default="Mus musculus")
    ap.add_argument("--keep-stop", action="store_true", help="keep the TGA stop codon the model appends")
    a = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained("adibvafa/CodonTransformer")
    model = BigBirdForMaskedLM.from_pretrained("adibvafa/CodonTransformer").to(device).eval()

    rows = []
    with open(a.input, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            prot = r["protein"].strip().upper().rstrip("*")
            org = (r.get("organism") or a.organism).strip()
            out = predict_dna_sequence(protein=prot, organism=org, device=device, tokenizer=tok, model=model,
                                       attention_type="original_full", deterministic=True)
            dna = out.predicted_dna
            ok = translate(dna).rstrip("*") == prot
            if not a.keep_stop and translate(dna).endswith("*"):
                dna = dna[:-3]
            rows.append({"name": r["name"], "organism": org, "protein": prot, "dna": dna,
                         "translation_ok": ok, "length_nt": len(dna)})
            print(f"{r['name']}: {len(prot)} aa -> {len(dna)} nt, translation_ok={ok}")

    with open(a.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
