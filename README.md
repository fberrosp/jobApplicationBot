# jobApplicationBot

## Installation

- Download zip or clone the repo `git clone git@github.com:fberrosp/jobApplicationBot.git`
    - (Optional) Install conda `https://docs.conda.io/en/latest/miniconda.html`
    - (Optional) Create a new conda environment and install dependencies `conda env create --name jobApplicationBot --file environment.yml`
    - (Optional) Activate conda environment `conda activate jobApplicationBot`
- Install dependencies with `pip install -r requirements.yaml` (skip if already installed with conda)
- Rename `credentials_sample.json` to `credentials.json`
- Enter your linkedin credentials on `credentials.json`
- Modify config.py according to your job search preferences
- Run `python3 linkedin.py`
- Check Applied Jobs DATA .txt file is generate under /data folder