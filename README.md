# Penguins Take Home

Reproducible analysis of shooting conversion, partial pooling, and NHL comparison data, with a goalie-adjustment sensitivity check.

- **Read:** open [the executed notebook](Penguins%20Take%20Home.ipynb), or download [the HTML report](Penguins%20Take%20Home.html) and open it in a browser.
- **Run:** follow [the notebook instructions](README-notebook.md) with Python 3.12.
- **Share:** download [the complete reproducible ZIP](Penguins%20Take%20Home%20-%20reproducible.zip).
- **Goalie evidence:** read [the goalie pooling report](analysis/goalie_sufficiency/REPORT.md). Its code, original results, paired predictions, and sensitivity tables are included.

The notebook reproduces the analyses in the [accompanying Google Doc](https://docs.google.com/document/d/1aMTChUaMZP4bzJqDUdpGow0VulTqTc4wa3gP7suz4vk/edit) and adds the earlier goalie check. In that check, adding partially pooled goalie effects produced negligible changes in forecast performance and standardized shooter estimates. The notebook reruns this check from the supplied raw data.

All analytical inputs are bundled: the original take-home CSV and compact NHL snapshots. [Data notes](data/notebook/README.md) describe their coverage, provenance, and known source limitations. The package contains the inputs needed for these analyses; the broader NHL collection and exploratory research archive remain separate.

The goalie check retains its historical specification: tuned Gaussian penalties and all 13,269 raw attempts. The main Bayesian conversion analysis uses 13,224 attempts after its duplicate-row cleaning step. These are explicitly labeled as separate analyses.

The notebook is the executable source for the final analysis. Regenerated figures and tables are written to `analysis/notebook_results/`. To rebuild the shareable ZIP after updating the deliverable, run:

```sh
python3 scripts/package_deliverable.py
```

`MANIFEST.sha256` records checksums for every packaged source, input, and report. On macOS, verify the unpacked package with `shasum -a 256 -c MANIFEST.sha256`; on Linux, use `sha256sum -c MANIFEST.sha256`.
