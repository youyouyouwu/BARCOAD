# BARCOAD

Streamlit app for generating 50 x 30 mm barcode labels.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The Korean font used by the label renderer is bundled under `assets/fonts`, so
the app does not require Linux packages during deployment.
