"""
AQG Demo Report Script
Run: python demo_report.py
"""
import csv
import sys
sys.path.insert(0, ".")

from scoring.gold_checker.checker import gold_accuracy
from scoring.agreement.kappa import cohens_kappa

gold = {}
with open("data/gold_items.csv", "r") as f:
    for row in csv.DictReader(f):
        gold[row["item_id"]] = row["gold_label"]

annotations = []
with open("data/sample_annotations.csv", "r") as f:
    for row in csv.DictReader(f):
        annotations.append({"item_id": row["item_id"], "annotator_id": row["annotator_id"], "label": row["label"]})

gold_result = gold_accuracy(annotations, gold)

annotator_ids = sorted(set(r["annotator_id"] for r in annotations))
labels_by_annotator = {aid: [r["label"] for r in annotations if r["annotator_id"] == aid] for aid in annotator_ids}

kappa_pairs = {}
ids = list(annotator_ids)
for i in range(len(ids)):
    for j in range(i + 1, len(ids)):
        a, b = ids[i], ids[j]
        la, lb = labels_by_annotator[a], labels_by_annotator[b]
        if len(la) == len(lb) and len(la) > 0:
            kappa_pairs[f"Annotator {a} vs Annotator {b}"] = round(cohens_kappa(la, lb), 4)

SEP = "=" * 52
print()
print(SEP)
print("   ANNOTATION QUALITY GUARDIAN - DEMO REPORT")
print(SEP)
print()
print("  [1] GOLD STANDARD ACCURACY")
print("  " + "-" * 40)
overall_pct = gold_result["overall_accuracy"] * 100
print(f"  Overall Project Accuracy : {overall_pct:.2f}%")
print()
for ann_id, stats in gold_result["per_annotator"].items():
    pct = stats["accuracy"] * 100
    bar = "X" * int(pct / 10) + "." * (10 - int(pct / 10))
    print(f"  Annotator {ann_id}  [{bar}]  {pct:.1f}%  ({stats['correct']}/{stats['total']} correct)")

print()
print("  [2] INTER-ANNOTATOR AGREEMENT (Cohen Kappa)")
print("  " + "-" * 40)
for pair, kappa in kappa_pairs.items():
    if kappa >= 0.8: level = "Almost Perfect"
    elif kappa >= 0.6: level = "Substantial"
    elif kappa >= 0.4: level = "Moderate"
    elif kappa >= 0.2: level = "Fair"
    else: level = "Poor"
    print(f"  {pair} : {kappa}  ({level})")

print()
print("  [3] PROJECT SUMMARY")
print("  " + "-" * 40)
print(f"  Total Annotations Processed : {len(annotations)}")
print(f"  Unique Annotators           : {len(annotator_ids)}")
print(f"  Gold Items Checked          : {len(gold)}")
print(f"  Overall Data Quality Score  : {overall_pct:.2f}%")
print()
print(SEP)
