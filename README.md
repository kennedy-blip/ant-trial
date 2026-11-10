# ⚡ Polars CSV Analytics Dashboard & FastAPI Backend

A high-performance local web dashboard and backend built with **FastAPI** and **Polars**. Ingests CSV files in milliseconds, automatically calculates summary statistics (**mean**, **median**, **null counts**, **skewness**, and percentiles), and generates interactive **Plotly.js** charts.

---

## 🌟 Key Features

- **Blazing Fast Polars Engine**: Leverages Apache Arrow in-memory representation and multi-threaded Polars execution for rapid summary computation.
- **Summary Statistics**:
  - **Mean** and **Median**: Easily observe central tendencies.
  - **Skewness**: Quantifies positive (right-skewed), negative (left-skewed), or symmetric distributions with color-coded badges.
  - **Null Counts & Percentages**: Accurately tracks missing cells per column.
  - **Spread & Dispersion**: Min, Max, Standard Deviation, and Quartiles (Q25, Q75).
- **Automated Interactive Visualizations**:
  - **Numeric Distributions**: Interactive Plotly histograms with bin boundaries and frequencies.
  - **Categorical Frequencies**: Horizontal bar charts displaying top categorical distributions.
  - **Pearson Correlation Heatmap**: Direct multi-column correlation matrix computed via Polars `.corr()`.
  - **Interactive Chart Studio**: Customize X and Y axes to plot custom Scatter, Bar, or Box plots on the fly.
  - **Raw Data Preview**: Paginated interactive data table displaying the first 50 rows.
- **Zero-Build Frontend**: Lightweight, responsive UI using Tailwind CSS and Plotly.js served directly from FastAPI (no Node.js build step needed).
- **Dataset Generator Included**: Standalone script (`generate_sample_data.py`) to create realistic multi-thousand row datasets with deliberate skewness, null values, and business categories.

---

## 📁 Project Structure

```text
trialsgk/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & REST endpoints
│   ├── data_processor.py    # Polars data extraction & statistical engine
│   ├── templates/
│   │   └── index.html       # Single-page interactive dashboard
│   └── static/
│       ├── css/
│       │   └── styles.css   # Custom dashboard styling & animations
│       └── js/
│           └── dashboard.js # Fetch API, sorting, filtering, & Plotly charts
├── sample_data/             # Built-in test datasets
│   ├── ecommerce_orders.csv
│   └── employee_metrics.csv
├── generate_sample_data.py  # Script to generate rich synthetic CSV files
├── requirements.txt         # Project dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Initialize a Python Virtual Environment

Open your terminal or PowerShell in the project directory:

#### On Windows (PowerShell):
```powershell
# Create the virtual environment
python -m venv .venv

# If script execution is restricted in PowerShell, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt):
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 2. Install Dependencies

With the virtual environment activated:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 3. Generate Sample Data (Optional)

The project includes pre-populated sample files in `sample_data/`. To generate larger synthetic datasets (thousands of records with custom distributions):

```bash
python generate_sample_data.py
```

This creates:
- `sample_data/ecommerce_orders.csv` (2,500 orders with log-normal sales, discounts, profit margins, and unrated orders).
- `sample_data/employee_metrics.csv` (1,200 employee records with skewed salaries, bonuses with nulls, and experience levels).

---

### 4. Run the FastAPI Application

Start the local server using Uvicorn:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or run directly with Python:

```bash
python app/main.py
```

---

### 5. Open the Dashboard

Open your browser and navigate to:

👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📊 Using the Dashboard

1. **Load a Sample Dataset**: Use the dropdown in the header to select `ecommerce_orders.csv` or `employee_metrics.csv` and click **Load**.
2. **Upload Your Own CSV**: Drag & drop any `.csv` file into the upload zone or click to browse.
3. **Inspect Summary Statistics**:
   - Filter columns using the search box or the data type dropdown.
   - Click any column header (e.g., *Skewness*, *Nulls*, *Mean*) to sort ascending or descending.
   - Skewness badges highlight whether a variable is approximately symmetric, right-skewed, or left-skewed.
4. **Explore Automated Charts**: Switch to the **Automated Charts** tab to view generated histograms and categorical bar charts.
5. **Analyze Correlations**: Switch to the **Correlation Matrix** tab to examine Pearson correlation coefficients across all numeric features.
6. **Custom Chart Studio**: Switch to **Interactive Explorer** to plot any variable against another with custom chart types (Scatter, Bar, Box Plot).
7. **Inspect Raw Rows**: Switch to **Raw Data Preview** to view the underlying records.

---

## 🛠️ REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the HTML analytics dashboard |
| `GET` | `/api/sample-files` | Lists available CSV files in `sample_data/` |
| `GET` | `/api/load-sample/{filename}` | Analyzes a sample CSV with Polars and returns statistics + charts |
| `POST` | `/api/upload` | Ingests an uploaded CSV file, executes Polars profiling, and returns JSON |
| `GET` | `/api/health` | Healthcheck endpoint (`{"status": "ok"}`) |

---

## 🧮 Statistical Formulas in Polars

Summary statistics are computed using Polars expressions:

```python
import polars as pl

df = pl.read_csv("sample_data/ecommerce_orders.csv")

# Mean & Median
mean_val = df["sales_amount"].mean()
median_val = df["sales_amount"].median()

# Missing Values
null_count = df["customer_rating"].null_count()

# Fisher-Pearson Skewness Coefficient
skewness_val = df["sales_amount"].skew()

# Pearson Correlation Matrix
numeric_cols = [c for c in df.columns if df[c].dtype.is_numeric()]
corr_matrix = df.select(numeric_cols).corr()
```

---

## ☁️ Deploying to Vercel

The project includes pre-configured [`vercel.json`](file:///c:/Users/user/Desktop/trialsgk/vercel.json) and [`api/index.py`](file:///c:/Users/user/Desktop/trialsgk/api/index.py) serverless entrypoint for instant deployment to Vercel.

### Method 1: Deploy via GitHub (Recommended)
1. Push this repository to your GitHub account (see instructions below).
2. Go to [vercel.com](https://vercel.com) and click **"Add New..."** > **"Project"**.
3. Import your GitHub repository.
4. Leave the Framework Preset as **Other** (Vercel automatically detects `vercel.json`).
5. Click **Deploy**. Vercel will bundle the serverless function, install `requirements.txt`, and deploy the dashboard live!

### Method 2: Deploy via Vercel CLI
```bash
# Install Vercel CLI globally if needed
npm install -g vercel

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

---

## 🐙 Pushing to GitHub

To link this local repository to your GitHub account:

### Option A: Using GitHub Web
1. Create a new repository on [github.com/new](https://github.com/new) (e.g., `polars-analytics-dashboard`).
2. Run the following commands in your terminal:
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

### Option B: Using GitHub CLI (`gh`)
```bash
gh repo create polars-analytics-dashboard --public --source=. --remote=origin --push
```

---
