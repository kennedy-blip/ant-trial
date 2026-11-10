"""
Data Processor Module powered by Polars.
Handles fast CSV ingestion, summary statistics calculation (mean, median, null counts, skewness),
correlation analysis, and structured chart payload generation.
"""

import math
import time
from typing import Dict, Any, List, Optional
import polars as pl


def sanitize_numeric(val: Any, decimals: int = 4) -> Optional[float]:
    """Safely sanitize float values for JSON compliance (handles NaN, inf, None)."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None


def get_skewness_description(skew: Optional[float]) -> str:
    """Interprets skewness coefficient according to standard statistical rules."""
    if skew is None:
        return "N/A"
    if skew > 1.0:
        return "Highly positive (right-skewed)"
    elif 0.5 < skew <= 1.0:
        return "Moderately positive"
    elif -0.5 <= skew <= 0.5:
        return "Approximately symmetric"
    elif -1.0 <= skew < -0.5:
        return "Moderately negative"
    else:
        return "Highly negative (left-skewed)"


def compute_histogram_bins(series: pl.Series, num_bins: int = 15) -> Dict[str, Any]:
    """
    Computes equal-width histogram bins and frequencies using Polars.
    Returns bin labels, counts, and bin boundaries.
    """
    clean_series = series.drop_nulls()
    if clean_series.len() == 0:
        return {"labels": [], "counts": [], "min": None, "max": None}

    min_val = clean_series.min()
    max_val = clean_series.max()

    if min_val is None or max_val is None or min_val == max_val:
        return {
            "labels": [str(min_val)],
            "counts": [clean_series.len()],
            "min": sanitize_numeric(min_val),
            "max": sanitize_numeric(max_val),
        }

    min_f = float(min_val)
    max_f = float(max_val)
    bin_width = (max_f - min_f) / num_bins

    # Create bin boundaries
    bins = [min_f + i * bin_width for i in range(num_bins + 1)]
    counts = [0] * num_bins
    labels = []

    for i in range(num_bins):
        low = bins[i]
        high = bins[i + 1]
        labels.append(f"{low:.2f} - {high:.2f}")

    # Count elements in each bin
    values = clean_series.to_list()
    for v in values:
        try:
            fv = float(v)
            if math.isnan(fv) or math.isinf(fv):
                continue
            idx = int((fv - min_f) / bin_width)
            if idx >= num_bins:
                idx = num_bins - 1
            elif idx < 0:
                idx = 0
            counts[idx] += 1
        except (ValueError, TypeError):
            continue

    return {
        "labels": labels,
        "counts": counts,
        "bin_edges": [round(b, 2) for b in bins],
        "min": sanitize_numeric(min_f),
        "max": sanitize_numeric(max_f),
    }


def analyze_dataframe(df: pl.DataFrame, file_name: str = "dataset.csv") -> Dict[str, Any]:
    """
    Analyzes a Polars DataFrame and returns:
    1. Overall dataset metadata (rows, columns, total nulls, memory).
    2. Comprehensive summary statistics per column (mean, median, null counts, skewness, min, max, std).
    3. Visual chart data (histograms, categorical frequency distributions, correlation matrix).
    4. Data preview (first 50 rows).
    """
    start_time = time.perf_counter()

    total_rows = df.height
    total_cols = df.width

    if total_rows == 0:
        return {
            "error": "The provided CSV file contains no data rows.",
            "file_name": file_name,
        }

    # Classify columns by datatype
    numeric_cols: List[str] = []
    categorical_cols: List[str] = []
    datetime_cols: List[str] = []
    boolean_cols: List[str] = []

    for col_name, dtype in zip(df.columns, df.dtypes):
        if dtype.is_numeric():
            numeric_cols.append(col_name)
        elif dtype.is_temporal():
            datetime_cols.append(col_name)
        elif dtype == pl.Boolean:
            boolean_cols.append(col_name)
        else:
            categorical_cols.append(col_name)

    # 1. Column-by-column Summary Statistics
    summary_stats = []
    total_null_cells = 0

    for col in df.columns:
        s = df[col]
        dtype_str = str(s.dtype)
        null_count = s.null_count()
        total_null_cells += null_count
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        n_unique = s.n_unique()

        stat_row: Dict[str, Any] = {
            "column": col,
            "dtype": dtype_str,
            "count": total_rows - null_count,
            "null_count": null_count,
            "null_pct": null_pct,
            "n_unique": n_unique,
            "is_numeric": s.dtype.is_numeric(),
            "mean": None,
            "median": None,
            "skewness": None,
            "skewness_desc": "N/A",
            "min": None,
            "max": None,
            "std": None,
            "q25": None,
            "q75": None,
        }

        if s.dtype.is_numeric():
            clean_s = s.drop_nulls()
            if clean_s.len() > 0:
                mean_val = clean_s.mean()
                median_val = clean_s.median()
                skew_val = clean_s.skew()
                min_val = clean_s.min()
                max_val = clean_s.max()
                std_val = clean_s.std()
                q25_val = clean_s.quantile(0.25)
                q75_val = clean_s.quantile(0.75)

                stat_row["mean"] = sanitize_numeric(mean_val)
                stat_row["median"] = sanitize_numeric(median_val)
                stat_row["skewness"] = sanitize_numeric(skew_val)
                stat_row["skewness_desc"] = get_skewness_description(stat_row["skewness"])
                stat_row["min"] = sanitize_numeric(min_val)
                stat_row["max"] = sanitize_numeric(max_val)
                stat_row["std"] = sanitize_numeric(std_val)
                stat_row["q25"] = sanitize_numeric(q25_val)
                stat_row["q75"] = sanitize_numeric(q75_val)
        else:
            # For categorical/string columns, grab top 3 frequent values as sample
            top_counts = (
                s.drop_nulls()
                .value_counts()
                .sort(by="count", descending=True)
                .head(3)
            )
            top_vals = [f"{row[0]} ({row[1]})" for row in top_counts.iter_rows()]
            stat_row["top_values"] = top_vals

        summary_stats.append(stat_row)

    # 2. Automated Interactive Chart Payloads
    chart_data: Dict[str, Any] = {
        "histograms": {},
        "categorical_bars": {},
        "boxplots": {},
        "correlation_matrix": None,
    }

    # Numeric Distributions (Histograms & Box Plot data)
    for col in numeric_cols:
        s = df[col]
        clean_s = s.drop_nulls()
        if clean_s.len() > 0:
            hist_info = compute_histogram_bins(clean_s, num_bins=16)
            chart_data["histograms"][col] = hist_info

            # Pre-compute box plot five-number summary
            q1 = sanitize_numeric(clean_s.quantile(0.25))
            med = sanitize_numeric(clean_s.median())
            q3 = sanitize_numeric(clean_s.quantile(0.75))
            min_v = sanitize_numeric(clean_s.min())
            max_v = sanitize_numeric(clean_s.max())
            mean_v = sanitize_numeric(clean_s.mean())

            chart_data["boxplots"][col] = {
                "min": min_v,
                "q1": q1,
                "median": med,
                "q3": q3,
                "max": max_v,
                "mean": mean_v,
            }

    # Categorical Frequency Distributions (Top 10 categories per column)
    for col in categorical_cols:
        s = df[col].drop_nulls()
        if s.len() > 0:
            vc = (
                s.value_counts()
                .sort(by="count", descending=True)
                .head(10)
            )
            labels = [str(r[0]) for r in vc.iter_rows()]
            counts = [int(r[1]) for r in vc.iter_rows()]
            chart_data["categorical_bars"][col] = {
                "labels": labels,
                "counts": counts,
            }

    # Boolean columns (True vs False)
    for col in boolean_cols:
        s = df[col].drop_nulls()
        if s.len() > 0:
            vc = s.value_counts().sort(by="count", descending=True)
            labels = [str(r[0]) for r in vc.iter_rows()]
            counts = [int(r[1]) for r in vc.iter_rows()]
            chart_data["categorical_bars"][col] = {
                "labels": labels,
                "counts": counts,
            }

    # Correlation Matrix for Numeric Columns (using Polars .corr())
    if len(numeric_cols) >= 2:
        try:
            corr_df = df.select(numeric_cols).corr()
            corr_matrix = []
            for row in corr_df.iter_rows():
                corr_matrix.append([sanitize_numeric(val, 3) for val in row])

            chart_data["correlation_matrix"] = {
                "columns": numeric_cols,
                "matrix": corr_matrix,
            }
        except Exception:
            chart_data["correlation_matrix"] = None

    # 3. Data Preview (First 50 rows)
    preview_limit = min(50, total_rows)
    preview_df = df.head(preview_limit)
    preview_rows = []
    for row in preview_df.iter_rows():
        sanitized_row = []
        for v in row:
            if v is None:
                sanitized_row.append("")
            elif isinstance(v, float):
                sanitized_row.append(sanitize_numeric(v, 2))
            else:
                sanitized_row.append(str(v))
        preview_rows.append(sanitized_row)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    memory_mb = round(df.estimated_size() / (1024 * 1024), 3)

    return {
        "file_name": file_name,
        "processing_time_ms": elapsed_ms,
        "kpis": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "numeric_columns_count": len(numeric_cols),
            "categorical_columns_count": len(categorical_cols),
            "temporal_columns_count": len(datetime_cols),
            "boolean_columns_count": len(boolean_cols),
            "total_null_cells": total_null_cells,
            "null_percentage": round((total_null_cells / (total_rows * total_cols)) * 100, 2) if total_rows * total_cols > 0 else 0.0,
            "memory_usage_mb": memory_mb,
        },
        "column_categories": {
            "numeric": numeric_cols,
            "categorical": categorical_cols,
            "temporal": datetime_cols,
            "boolean": boolean_cols,
            "all": df.columns,
        },
        "summary_statistics": summary_stats,
        "chart_data": chart_data,
        "preview": {
            "columns": df.columns,
            "rows": preview_rows,
            "total_rows": total_rows,
            "preview_count": preview_limit,
        },
    }


def read_csv_with_polars(source: Any, file_name: str = "dataset.csv") -> Dict[str, Any]:
    """
    Reads a CSV from a file path or in-memory byte buffer using Polars,
    then executes full profiling and chart generation.
    """
    try:
        # High-performance Polars CSV read with schema inference
        df = pl.read_csv(
            source,
            infer_schema_length=10000,
            ignore_errors=True,
            null_values=["", "NA", "N/A", "null", "NULL", "None", "nan", "NaN"],
        )
    except Exception as e1:
        try:
            # Fallback with alternate encoding
            df = pl.read_csv(
                source,
                encoding="latin1",
                infer_schema_length=10000,
                ignore_errors=True,
                null_values=["", "NA", "N/A", "null", "NULL", "None", "nan", "NaN"],
            )
        except Exception as e2:
            return {
                "error": f"Failed to parse CSV using Polars: {str(e2)} (initial attempt: {str(e1)})",
                "file_name": file_name,
            }

    return analyze_dataframe(df, file_name=file_name)
