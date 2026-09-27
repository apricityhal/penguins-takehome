# Penguins Take Home notebook

Open **Penguins Take Home.ipynb** in a notebook editor, select **Python (Penguins Take Home)**, and run all cells in order. The notebook reproduces the analyses in the [document](https://docs.google.com/document/d/1aMTChUaMZP4bzJqDUdpGow0VulTqTc4wa3gP7suz4vk/edit): NHL opportunity generation, cleaning, partial pooling, the three conversion models, player estimates, and the NHL variation and detection-power comparisons. It also reproduces the earlier goalie partial-pooling sensitivity, with the full supporting report and results included in `analysis/goalie_sufficiency/`.

`location_on_net` remains in the cleaned data and enters the conditional on-net model and its historical placement distribution. The one-stage count models select their own inputs. The include/exclude comparison for the 68 flagged goals is retained because the document reports that analysis.

## Run

Use Python 3.12 and install the pinned dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-notebook.txt
.venv/bin/python -m ipykernel install --prefix .venv --name penguins-take-home --display-name "Python (Penguins Take Home)"
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 "Penguins Take Home.ipynb"
.venv/bin/jupyter nbconvert --to html "Penguins Take Home.ipynb"
```

The notebook's data inputs are `data/raw/shot-data.csv` and the compact source snapshots in `data/notebook/`. Its goalie-check cell invokes the included `analysis/goalie_sufficiency/check_goalies.py` using the notebook's Python environment. Keep these directories with the notebook when sharing it. `data/notebook/nhl_sources.json` records source snapshots and checksums; [data notes](data/notebook/README.md) describe coverage and known source limitations. `nhl_match_rng.json` contains the initial random-generator state for the reported forward sample; the notebook recomputes every simulated draw. Model fits and results are recomputed from the inputs. Outputs are written to `analysis/notebook_results/`, including the regenerated goalie results in its `goalie_pooling/` subdirectory. Source data remain unchanged.

Development RMSE averages the two chronological development-fold MSEs before taking the square root. Validation forecasts 2024 from earlier seasons. The final player display fits a shared baseline to all take-home seasons; the forecasting comparison includes season effects. Normal player effects are on the log-odds scale. The notebook states the assumptions behind the detection-power calculation.

## Goalie partial-pooling check

The earlier check uses all 13,269 raw attempts and prediction-tuned Gaussian penalties for shooter and goalie effects. Its historical validation found no consistent, practically meaningful gain from adding goalie effects: combined per-attempt log loss was 0.264388 for shooters alone and 0.264412 with goalies. At the selected goalie penalty, the largest standardized shooter adjustment was 0.0144 goals per 100 attempts. These results support the modeling decision within this sample. The main Bayesian model learns its pooling scale and uses 13,224 cleaned attempts; the goalie check is a separate sensitivity.

To run only the goalie check and its exposure audit:

```sh
.venv/bin/python analysis/goalie_sufficiency/check_goalies.py --output-dir analysis/notebook_results/goalie_pooling
.venv/bin/python analysis/goalie_sufficiency/support_audit.py --output-dir analysis/notebook_results/goalie_support
```

The included [goalie report](analysis/goalie_sufficiency/REPORT.md) explains the chronological tuning, uncertainty intervals, and limitations. Saved original results accompany the scripts, while these commands write new results to separate output directories.

The delivered notebook contains 35 cells, including 22 code cells and four figures. The HTML report provides a readable copy with the same executed outputs. Package installation requires internet access; the analysis uses bundled local inputs.
