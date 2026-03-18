"""One-off script: compute and print the 6×6 seed centroid similarity matrix."""

import os
import sys

# Load .env so OPENAI_API_KEY is available
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# Clear any cached settings so fresh env vars are picked up
from app.config import get_settings

get_settings.cache_clear()

from app.clustering import SEED_ARCHETYPES, compute_seed_centroids, cosine_similarity

print("Computing seed centroids (calling OpenAI API)...")
centroids = compute_seed_centroids()
names = [a["name"] for a in SEED_ARCHETYPES]

# Compute pairwise similarity matrix
matrix: list[list[float]] = []
for name_a in names:
    row = [cosine_similarity(centroids[name_a], centroids[name_b]) for name_b in names]
    matrix.append(row)

# Print matrix
col_width = 22
header = " " * col_width + "".join(n[:20].rjust(col_width) for n in names)
print("\n" + header)
print("-" * len(header))
for i, name_a in enumerate(names):
    row_str = name_a.ljust(col_width) + "".join(f"{matrix[i][j]:.4f}".rjust(col_width) for j in range(len(names)))
    print(row_str)

# Collect off-diagonal similarities
pairwise = []
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        pairwise.append((names[i], names[j], matrix[i][j]))

similarities = [s for _, _, s in pairwise]
print(f"\nMin pairwise similarity: {min(similarities):.4f}")
print(f"Max pairwise similarity: {max(similarities):.4f}")
print(f"Mean pairwise similarity: {sum(similarities) / len(similarities):.4f}")

# Escalation criterion #4: any archetype >0.95 similar to 3+ others
print("\n--- Escalation Criteria ---")
flagged_4 = False
for i, name_a in enumerate(names):
    high_count = sum(1 for j in range(len(names)) if i != j and matrix[i][j] > 0.95)
    if high_count >= 3:
        print(f"FLAGGED #4: {name_a} is >0.95 similar to {high_count} other archetypes")
        flagged_4 = True
if not flagged_4:
    print("Criterion #4 (degenerate assignment): CLEAR")

# Escalation criterion #5: all >0.95 or all <0.1
all_high = all(s > 0.95 for s in similarities)
all_low = all(s < 0.1 for s in similarities)
if all_high or all_low:
    print(f"FLAGGED #5: {'all >0.95' if all_high else 'all <0.1'} — uniform similarity")
    sys.exit(1)
else:
    print("Criterion #5 (uniform similarity): CLEAR")
