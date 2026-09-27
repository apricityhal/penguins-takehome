"""Package the final notebook, input snapshots, and goalie sensitivity evidence."""
from pathlib import Path
import hashlib
import json
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "README.md",
    "README-notebook.md",
    "Penguins Take Home.ipynb",
    "Penguins Take Home.html",
    "requirements-notebook.txt",
    "scripts/package_deliverable.py",
    "data/raw/shot-data.csv",
    "data/notebook/README.md",
    "data/notebook/nhl_2024_player_games.csv",
    "data/notebook/nhl_all_situations_halves.csv",
    "data/notebook/nhl_birth_dates.csv",
    "data/notebook/nhl_match_rng.json",
    "data/notebook/nhl_seasons.csv",
    "data/notebook/nhl_sources.json",
    "analysis/goalie_sufficiency/REPORT.md",
    "analysis/goalie_sufficiency/check_goalies.py",
    "analysis/goalie_sufficiency/support_audit.py",
    "analysis/goalie_sufficiency/support_audit.md",
    "analysis/goalie_sufficiency/protocol.json",
    "analysis/goalie_sufficiency/results.json",
    "analysis/goalie_sufficiency/candidate_scores.json",
    "analysis/goalie_sufficiency/support_audit.json",
    "analysis/goalie_sufficiency/predictions.csv.gz",
    "analysis/goalie_sufficiency/shooter_sensitivity.csv",
    "analysis/goalie_sufficiency/goalie_conditional_sensitivity.csv",
]


def main():
    for name in FILES:
        if not (ROOT / name).is_file():
            raise FileNotFoundError(f"Required deliverable file: {name}")
    notebook = json.loads((ROOT / "Penguins Take Home.ipynb").read_text())
    if any(output.get("output_type") == "error"
           for cell in notebook["cells"] for output in cell.get("outputs", [])):
        raise ValueError("Resolve notebook error outputs before packaging.")
    manifest = ROOT / "MANIFEST.sha256"
    manifest.write_text("".join(
        f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}\n"
        for name in sorted(FILES)
    ))
    target = ROOT / "Penguins Take Home - reproducible.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted([*FILES, manifest.name]):
            archive.write(ROOT / name, arcname=name)
    with ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Archive integrity check failed.")
    print(f"Packaged {len(FILES) + 1} files into {target.name} ({target.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
