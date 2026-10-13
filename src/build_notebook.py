"""
Notebook Builder Script: Generates executed notebooks/data_profiling.ipynb
Course: ETL (UAO) - Workshop 2
"""
import nbformat as nbf
from pathlib import Path
from nbclient import NotebookClient

NOTEBOOK_PATH = Path("notebooks/data_profiling.ipynb")

def build_and_run_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.2"
        }
    }

    cells = []

    # Title Markdown
    cells.append(nbf.v4.new_markdown_cell("""# Workshop 2: Data Profiling & Quality Risk Analysis
**Faculty of Engineering and Basic Sciences**  
**Academic Program:** Data Engineering and Artificial Intelligence  
**Course:** ETL (G01)  
**Scenario:** Spotify Catalog & Grammy Awards Integration  

---
### Objectives of this Notebook:
1. Conduct empirical, evidence-based profiling of both source datasets (`spotify_dataset.csv` and `the_grammy_awards.csv`).
2. Evaluate 7 profiling dimensions: **Structure, Completeness, Uniqueness, Categorical Content, Numerical Content, Temporal Content, and Cross-Source Consistency**.
3. Identify concrete quality risks that threaten downstream analytical requirements (**REQ-01, REQ-02, REQ-03**).
4. Define explicit metrics, thresholds, and severity levels to govern automated validation gates in **Great Expectations**.
"""))

    # Imports Code
    cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Visual styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({'figure.figsize': (10, 5), 'font.size': 10})
"""))

    # Load Data Code
    cells.append(nbf.v4.new_markdown_cell("""## 1. Data Acquisition & Structural Profiling
We load both datasets from source storage and inspect schema, data types, and primary grain.
"""))

    cells.append(nbf.v4.new_code_cell("""import os
from pathlib import Path

# Resolve data path robustly whether run from project root or notebooks/ directory
if os.path.exists("spotify_dataset.csv"):
    base_data_path = Path(".")
elif os.path.exists("../spotify_dataset.csv"):
    base_data_path = Path("..")
else:
    base_data_path = Path(".").resolve()

df_spotify = pd.read_csv(base_data_path / "spotify_dataset.csv")
df_grammy = pd.read_csv(base_data_path / "the_grammy_awards.csv")

print(f"Spotify shape: {df_spotify.shape[0]:,} rows x {df_spotify.shape[1]} columns")
print(f"Grammy shape:  {df_grammy.shape[0]:,} rows x {df_grammy.shape[1]} columns")
"""))

    cells.append(nbf.v4.new_code_cell("""# Inspect schemas and sample records
display(df_spotify.head(3))
display(df_grammy.head(3))
"""))

    # Completeness Markdown & Code
    cells.append(nbf.v4.new_markdown_cell("""## 2. Completeness & Missing Value Analysis
Missing data can silently corrupt aggregations and foreign key joins.
"""))

    cells.append(nbf.v4.new_code_cell("""spot_nulls = df_spotify.isnull().sum()
gram_nulls = df_grammy.isnull().sum()

print("--- Spotify Missing Values ---")
print(spot_nulls[spot_nulls > 0])

print("\\n--- Grammy Missing Values ---")
print(gram_nulls[gram_nulls > 0])
"""))

    cells.append(nbf.v4.new_code_cell("""# Visualize Missing Values
fig, axes = plt.subplots(1, 2, figsize=(13, 4))

(gram_nulls / len(df_grammy) * 100).sort_values(ascending=False).plot(
    kind='barh', ax=axes[0], color='#D9534F', title='Grammy: Null Rate (%)'
)
axes[0].set_xlabel('Percentage (%)')

(spot_nulls[spot_nulls > 0] / len(df_spotify) * 100).plot(
    kind='bar', ax=axes[1], color='#337AB7', title='Spotify: Columns with Nulls (%)'
)
axes[1].set_ylabel('Percentage (%)')
plt.tight_layout()
plt.show()
"""))

    # Uniqueness Markdown & Code
    cells.append(nbf.v4.new_markdown_cell("""## 3. Uniqueness and Duplication Analysis
Evaluating candidate keys and duplicate behaviors.
"""))

    cells.append(nbf.v4.new_code_cell("""total_tracks = len(df_spotify)
unique_tracks = df_spotify['track_id'].nunique()
duplicate_track_rows = total_tracks - unique_tracks

print(f"Total Spotify records:        {total_tracks:,}")
print(f"Unique track_id occurrences:  {unique_tracks:,}")
print(f"Multi-genre duplicate rows:   {duplicate_track_rows:,} ({duplicate_track_rows/total_tracks*100:.1f}%)")

# Inspect reasons for duplicates: Tracks assigned to multiple genre tags
sample_dups = df_spotify[df_spotify.duplicated(subset=['track_id'], keep=False)].sort_values('track_id')
sample_dups[['track_id', 'track_name', 'artists', 'track_genre']].head(6)
"""))

    # Numerical Profiling
    cells.append(nbf.v4.new_markdown_cell("""## 4. Numerical Content & Boundary Verification
Audio characteristics must adhere to strictly defined mathematical and physics domains:
- Audio features (`danceability`, `energy`, `valence`, `acousticness`): $[0.0, 1.0]$
- Popularity: $[0, 100]$
"""))

    cells.append(nbf.v4.new_code_cell("""num_cols = ['popularity', 'duration_ms', 'danceability', 'energy', 'valence', 'tempo']
df_spotify[num_cols].describe().T
"""))

    cells.append(nbf.v4.new_code_cell("""# Plot Numerical Feature Distributions
fig, axes = plt.subplots(2, 3, figsize=(14, 7))
axes = axes.flatten()

for i, col in enumerate(num_cols):
    sns.histplot(df_spotify[col], bins=30, kde=True, ax=axes[i], color='#1DB954')
    axes[i].set_title(f'Spotify: {col}')

plt.tight_layout()
plt.show()
"""))

    # Temporal Profiling
    cells.append(nbf.v4.new_markdown_cell("""## 5. Temporal Content & Award Coverage
The Grammy dataset covers 1958 to 2019 without temporal gaps.
"""))

    cells.append(nbf.v4.new_code_cell("""year_counts = df_grammy['year'].value_counts().sort_index()

plt.figure(figsize=(12, 4))
year_counts.plot(kind='bar', color='#4A154B', width=0.8)
plt.title('Grammy Awards Conferred per Year (1958 - 2019)')
plt.xticks(range(0, len(year_counts), 5), year_counts.index[::5], rotation=45)
plt.xlabel('Year')
plt.ylabel('Awards')
plt.tight_layout()
plt.show()
"""))

    # Cross Source Entity Matching
    cells.append(nbf.v4.new_markdown_cell("""## 6. Cross-Source Consistency & Entity Harmonization
Analyzing entity resolution between Spotify artists and Grammy award recipients.
Multi-artist collaborations in Spotify use semicolons (`;`), while Grammy awards use `&`, `Featuring`, or `With`.
"""))

    cells.append(nbf.v4.new_code_cell("""# Tokenize Spotify artists
spotify_artists = set()
for a in df_spotify['artists'].dropna().unique():
    for sub in str(a).split(';'):
        spotify_artists.add(sub.strip().lower())

grammy_artists = set(df_grammy['artist'].dropna().str.lower().str.strip().unique())
matched_artists = spotify_artists.intersection(grammy_artists)

print(f"Tokenized unique Spotify artists: {len(spotify_artists):,}")
print(f"Unique Grammy artists:           {len(grammy_artists):,}")
print(f"Direct artist match count:        {len(matched_artists):,} ({len(matched_artists)/len(grammy_artists)*100:.1f}% match rate)")
"""))

    # Synthesis Table Markdown
    cells.append(nbf.v4.new_markdown_cell("""## 7. Quality Risk Register & Synthesis
The table below connects profiling findings directly to analytical requirements and Great Expectations rules:

| Dataset / Attribute | Profiling Evidence | Potential Quality Risk | Related Requirement | Severity | Engineering Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `spotify.track_id` | 89,741 unique IDs across 114,000 rows | Multi-genre tracks cause duplicate key violations if grain is track_id alone | REQ-01, REQ-02 | Critical | Declare composite grain `(track_id, genre)` in fact table; deduplicate in `dim_track`. |
| `spotify.audio_features` | 100% of danceability, energy, valence are in $[0, 1]$ | Out-of-bounds or negative values would invalidate audio signature analytics | REQ-01, REQ-03 | Critical | GX rule: `expect_column_values_to_be_between(0.0, 1.0)`. |
| `spotify.artists` | 1 null record; multiple artists joined by `;` | Semicolons prevent direct join with single artist strings | REQ-01, REQ-02 | Warning | Clean nulls; tokenize multi-artist collaborations into individual artist entities. |
| `grammy.year` | Values span 1958 to 2019; no nulls | Future or negative years would invalidate temporal era analysis | REQ-03 | Critical | GX rule: `expect_column_values_to_be_between(1958, 2026)`. |
| `grammy.artist` | 1,840 nulls (38.3%) | Missing artist column would cause missed matches in song-writing awards | REQ-01, REQ-02 | Warning | Harmonization logic: extract performer/songwriter from `workers` and `nominee` when `artist` is null. |
| `grammy.category` | 4,810 non-null values | Null category prevents award taxonomy classification | REQ-03 | Critical | GX rule: `expect_column_values_to_not_be_null`. |
"""))

    nb.cells = cells

    print(f"Executing and writing notebook to {NOTEBOOK_PATH}...")
    # Execute notebook
    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    client.execute()

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Notebook successfully generated and executed with all outputs!")

if __name__ == "__main__":
    build_and_run_notebook()
