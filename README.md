# ✈️ Airport Details Finder

A Streamlit web app to search **86,000+ airports** worldwide by name, IATA code,
ICAO code, city, or country. Results are shown on an interactive map
(Folium/Leaflet) with clickable markers, plus a full details table.

## ✨ Features

- Search by airport name, IATA code, ICAO code, city, country code, or country name
  (e.g. `CMB`, `srilanka`, `colombo`, `LK`)
- Interactive map with one marker per airport — hover for the name, click for details
- Relevance sorting (exact IATA matches first)
- Fast: data is loaded once and cached (`@st.cache_data`)
- Handles missing/invalid coordinates gracefully

## 📁 Project Structure

```
airport-finder/
├── app.py                  # Streamlit app (entry point)
├── data/
│   └── airports.csv        # Airport dataset (OurAirports)
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
├── .streamlit/
│   └── config.toml         # Streamlit app configuration
├── .github/
│   └── workflows/
│       └── ci.yml          # CI: lint & smoke-test the app
└── README.md
```

## 🚀 Local Setup

1. **Install Python 3.9+** (from <https://www.python.org/downloads/>).

2. **Clone the repo** (or copy the folder) and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```
   Open <http://localhost:8501> in your browser.

> The `data/airports.csv` file is already included in the repo.
> If you want a fresh copy: <https://davidmegginson.github.io/ourairports-data/>

## ☁️ Deploy to Streamlit Cloud + GitHub

1. **Create a GitHub repository** (public or private) and push this project to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Airport Details Finder app"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to <https://cloud.streamlit.io> and sign in.
   - Click **New app** → **Connect an existing repo**.
   - Select your GitHub account and the repository you just pushed.
   - Pick the `main` branch.
   - Streamlit Cloud auto-detects `app.py` and `requirements.txt` — no
     configuration needed.
   - Click **Deploy**. You'll get a live URL like
     `https://<app-name>.streamlit.app`.

3. **Future updates:** push changes to the `main` branch and Streamlit Cloud
   will automatically rebuild and redeploy the app.

## ⚙️ Configuration

- `.streamlit/config.toml` — theme and server defaults
- `.streamlit/secrets.toml` (git-ignored) — for any API keys/secrets you add later

## 📄 Data

Airport data from [OurAirports](https://davidmegginson.github.io/ourairports-data/)
(`airports.csv`, MIT-licensed).
