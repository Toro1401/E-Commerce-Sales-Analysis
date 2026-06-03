"""
analysis.py
Run SQL queries against ecommerce.db and generate professional charts.
Outputs: 5 PNG charts in charts/ directory + query results to console.
"""

import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be before pyplot import
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "ecommerce.db"
CHARTS_DIR = Path(__file__).parent / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Minimal light theme settings
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["text.color"] = "#1F2937"
plt.rcParams["axes.labelcolor"] = "#4B5563"
plt.rcParams["xtick.color"] = "#4B5563"
plt.rcParams["ytick.color"] = "#4B5563"

COLORS = {
    "primary":    "#4F46E5",  # Indigo
    "secondary":  "#6B7280",  # Slate
    "accent":     "#EF4444",  # Red
    "gold":       "#F59E0B",  # Muted Amber
    "bg_dark":    "#FFFFFF",  # Pure White
    "bg_card":    "#FFFFFF",  # Pure White
    "text":       "#1F2937",  # Dark grey
    "text_muted": "#4B5563",  # Muted grey
    "grid":       "#E5E7EB",  # Light grey
}

GRADIENT_PALETTE = [COLORS["primary"]] * 15


def get_connection():
    """Get SQLite connection."""
    return sqlite3.connect(str(DB_PATH))


def format_brl(x, _=None):
    """Format number as R$ Brazilian Real."""
    if x >= 1_000_000:
        return f"R$ {x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"R$ {x/1_000:.0f}K"
    return f"R$ {x:.0f}"


def style_axis(ax, title, xlabel="", ylabel=""):
    """Apply consistent styling to axis."""
    ax.set_title(title, fontsize=14, fontweight="600", color=COLORS["text"], pad=16, loc="left")
    ax.set_xlabel(xlabel, fontsize=10, color=COLORS["text_muted"], labelpad=8)
    ax.set_ylabel(ylabel, fontsize=10, color=COLORS["text_muted"], labelpad=8)
    ax.tick_params(colors=COLORS["text_muted"], labelsize=9)
    ax.set_facecolor(COLORS["bg_card"])
    ax.grid(axis="both", alpha=0.5, color=COLORS["grid"], linestyle="-", linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_color(COLORS["grid"])
        spine.set_linewidth(0.8)


# ═══════════════════════════════════════════════════════════════
# CHART 1: Top 15 Categories by Revenue (Horizontal Bar)
# ═══════════════════════════════════════════════════════════════
def chart_revenue_by_category(conn):
    query = """
    SELECT
        ct.product_category_name_english AS category,
        ROUND(SUM(oi.price), 2) AS total_revenue
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY ct.product_category_name_english
    ORDER BY total_revenue DESC
    LIMIT 15
    """
    df = pd.read_sql(query, conn)
    print("\n═══ Q1: Top 15 Categories by Revenue ═══")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(COLORS["bg_dark"])

    bars = ax.barh(
        range(len(df)),
        df["total_revenue"],
        color=COLORS["primary"],
        edgecolor="none",
        height=0.65
    )

    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([cat.replace("_", " ").title() for cat in df["category"]], fontsize=9.5, color=COLORS["text"])
    ax.invert_yaxis()

    # Add value labels directly next to bars
    max_val = df["total_revenue"].max()
    for i, val in enumerate(df["total_revenue"]):
        ax.text(
            val + max_val * 0.01, i,
            f" {format_brl(val)}",
            va="center", ha="left", fontsize=9, color=COLORS["text_muted"]
        )

    style_axis(ax, "Top 15 Product Categories by Revenue", xlabel="")
    
    # Hide grid and axes since labels are printed on bars
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.xaxis.set_tick_params(labelbottom=False, bottom=False)
    ax.yaxis.set_tick_params(left=False)

    plt.tight_layout()
    path = CHARTS_DIR / "01_revenue_by_category.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg_dark"])
    plt.close()
    print(f"  → Saved: {path}")
    return df


# ═══════════════════════════════════════════════════════════════
# CHART 2: Monthly Revenue Trend (Line Chart)
# ═══════════════════════════════════════════════════════════════
def chart_monthly_trend(conn):
    query = """
    SELECT
        STRFTIME('%Y-%m', o.order_purchase_timestamp) AS month,
        COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY month
    ORDER BY month
    """
    df = pd.read_sql(query, conn)
    df["month_dt"] = pd.to_datetime(df["month"] + "-01")

    print("\n═══ Q5: Monthly Revenue Trend ═══")
    print(df[["month", "orders", "revenue"]].to_string(index=False))

    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor(COLORS["bg_dark"])

    # Revenue line with subtle fill
    ax1.plot(df["month_dt"], df["revenue"], color=COLORS["primary"],
             linewidth=2.2, marker="o", markersize=4, label="Revenue")
    ax1.fill_between(df["month_dt"], df["revenue"], alpha=0.04, color=COLORS["primary"])

    # Orders on secondary axis (thin light gray bars)
    ax2 = ax1.twinx()
    ax2.bar(df["month_dt"], df["orders"], width=12, alpha=0.35,
            color=COLORS["secondary"], label="Orders")
    
    # Hide top spines
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    
    # Style spines and axes
    style_axis(ax1, "Monthly Revenue Trend (2016–2018)", ylabel="Revenue (R$)")
    ax1.grid(True, axis="y", alpha=0.5, color=COLORS["grid"])
    ax1.grid(False, axis="x")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(format_brl))
    
    ax2.set_ylabel("Order Count", fontsize=10, color=COLORS["text_muted"])
    ax2.tick_params(axis="y", colors=COLORS["text_muted"], labelsize=9)
    ax2.spines["left"].set_color(COLORS["grid"])
    ax2.spines["bottom"].set_color(COLORS["grid"])
    ax2.spines["right"].set_color(COLORS["grid"])

    # Annotate peak
    peak_idx = df["revenue"].idxmax()
    peak_month = df.loc[peak_idx, "month"]
    peak_val = df.loc[peak_idx, "revenue"]
    ax1.annotate(
        f"Peak: {format_brl(peak_val)} ({peak_month})",
        xy=(df.loc[peak_idx, "month_dt"], peak_val),
        xytext=(25, 20), textcoords="offset points",
        fontsize=9, color=COLORS["text"], fontweight="600",
        arrowprops=dict(arrowstyle="->", color=COLORS["secondary"], lw=0.8),
    )

    # Add seasonal markers
    for year in [2017, 2018]:
        bf_date = pd.Timestamp(f"{year}-11-24") # Standard Black Friday late Nov
        # Check if date falls within timeline
        if bf_date >= df["month_dt"].min() and bf_date <= df["month_dt"].max():
            ax1.axvline(bf_date, color=COLORS["text_muted"], alpha=0.3, linestyle=":", lw=1.2)
            ax1.text(bf_date, ax1.get_ylim()[1] * 0.90, f"Black Friday {year}  ",
                     fontsize=8.5, color=COLORS["text_muted"], ha="right", style="italic")

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               fontsize=9.5, frameon=False)

    plt.tight_layout()
    path = CHARTS_DIR / "02_monthly_revenue_trend.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg_dark"])
    plt.close()
    print(f"  → Saved: {path}")
    return df


# ═══════════════════════════════════════════════════════════════
# CHART 3: Category × Month Revenue Heatmap
# ═══════════════════════════════════════════════════════════════
def chart_category_month_heatmap(conn):
    query = """
    WITH top_cats AS (
        SELECT ct.product_category_name_english AS category
        FROM order_items oi
        JOIN orders o   ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN category_translation ct ON p.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY category
        ORDER BY SUM(oi.price) DESC
        LIMIT 10
    )
    SELECT
        ct.product_category_name_english AS category,
        CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) AS month_num,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
      AND ct.product_category_name_english IN (SELECT category FROM top_cats)
    GROUP BY ct.product_category_name_english, month_num
    ORDER BY ct.product_category_name_english, month_num
    """
    df = pd.read_sql(query, conn)

    print("\n═══ Q11: Category × Month Heatmap Data ═══")
    print(df.head(20).to_string(index=False))

    # Pivot for heatmap
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    df["month_name"] = df["month_num"].map(month_names)

    pivot = df.pivot_table(index="category", columns="month_num", values="revenue", fill_value=0)
    pivot.columns = [month_names[m] for m in pivot.columns]

    # Sort by total revenue
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False).drop("total", axis=1)

    # Format category names for clean display
    pivot.index = [cat.replace("_", " ").title() for cat in pivot.index]

    # Clean annotations: show "123k" instead of full numbers, leave small values blank
    annot_df = pivot.copy()
    for col in annot_df.columns:
        annot_df[col] = annot_df[col].apply(lambda x: f"{x/1000:.0f}k" if x >= 15000 else "")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor(COLORS["bg_dark"])

    sns.heatmap(
        pivot,
        annot=annot_df, fmt="",
        cmap="Blues",
        linewidths=0.8, linecolor="white",
        cbar_kws={"label": "Revenue (R$)", "shrink": 0.65},
        ax=ax,
        annot_kws={"fontsize": 8.5, "fontweight": "500", "color": "#1F2937"}
    )

    style_axis(ax, "Revenue Heatmap: Top 10 Categories × Month")
    ax.grid(False) # Heatmap doesn't need gridlines
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.setp(ax.get_yticklabels(), rotation=0)

    # Style colorbar label
    cbar = ax.collections[0].colorbar
    cbar.set_label("Revenue (R$)", color=COLORS["text_muted"], fontsize=10)
    cbar.ax.tick_params(colors=COLORS["text_muted"], labelsize=8)

    plt.tight_layout()
    path = CHARTS_DIR / "03_category_month_heatmap.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg_dark"])
    plt.close()
    print(f"  → Saved: {path}")
    return pivot


# ═══════════════════════════════════════════════════════════════
# CHART 4: Quarterly Revenue for Top 5 Categories (Grouped Bar)
# ═══════════════════════════════════════════════════════════════
def chart_quarterly_top_categories(conn):
    query = """
    WITH top_cats AS (
        SELECT ct.product_category_name_english AS category
        FROM order_items oi
        JOIN orders o   ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN category_translation ct ON p.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY category
        ORDER BY SUM(oi.price) DESC
        LIMIT 5
    )
    SELECT
        ct.product_category_name_english AS category,
        STRFTIME('%Y', o.order_purchase_timestamp) AS year,
        CASE
            WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
            WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
            WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
            ELSE 'Q4'
        END AS quarter,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
      AND ct.product_category_name_english IN (SELECT category FROM top_cats)
      AND STRFTIME('%Y', o.order_purchase_timestamp) IN ('2017', '2018')
    GROUP BY category, year, quarter
    ORDER BY category, year, quarter
    """
    df = pd.read_sql(query, conn)
    df["period"] = df["year"] + " " + df["quarter"]

    print("\n═══ Q8: Quarterly Revenue — Top 5 Categories ═══")
    print(df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor(COLORS["bg_dark"])

    categories = df["category"].unique()
    periods = sorted(df["period"].unique())
    x = range(len(periods))

    # Cohesive minimalist color palette
    cat_colors = ["#4F46E5", "#0D9488", "#3B82F6", "#F43F5E", "#F59E0B"]

    for i, cat in enumerate(categories):
        cat_data = df[df["category"] == cat]
        values = []
        for p in periods:
            match = cat_data[cat_data["period"] == p]
            values.append(match["revenue"].values[0] if len(match) > 0 else 0)
        
        display_label = cat.replace("_", " ").title()
        ax.plot(x, values, label=display_label, color=cat_colors[i % len(cat_colors)],
                linewidth=2.2, marker="o", markersize=4)

    ax.set_xticks(x)
    ax.set_xticklabels(periods, fontsize=9.5)

    style_axis(ax, "Quarterly Revenue Trends: Top 5 Categories (2017–2018)", ylabel="Revenue (R$)")
    ax.grid(True, axis="y", alpha=0.5, color=COLORS["grid"])
    ax.grid(False, axis="x")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_brl))
    
    # Legend to the right side, borderless and neat
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9.5, frameon=False)

    plt.tight_layout()
    path = CHARTS_DIR / "04_quarterly_top_categories.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg_dark"])
    plt.close()
    print(f"  → Saved: {path}")
    return df


# ═══════════════════════════════════════════════════════════════
# CHART 5: Regional Revenue by Top Categories (Stacked Bar)
# ═══════════════════════════════════════════════════════════════
def chart_regional_revenue(conn):
    query = """
    WITH top_states AS (
        SELECT c.customer_state AS state
        FROM order_items oi
        JOIN orders o    ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        ORDER BY SUM(oi.price) DESC
        LIMIT 8
    ),
    top_cats AS (
        SELECT ct.product_category_name_english AS category
        FROM order_items oi
        JOIN orders o   ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN category_translation ct ON p.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY category
        ORDER BY SUM(oi.price) DESC
        LIMIT 5
    )
    SELECT
        c.customer_state AS state,
        ct.product_category_name_english AS category,
        ROUND(SUM(oi.price), 2) AS revenue
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN customers c  ON o.customer_id = c.customer_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND c.customer_state IN (SELECT state FROM top_states)
      AND ct.product_category_name_english IN (SELECT category FROM top_cats)
    GROUP BY c.customer_state, ct.product_category_name_english
    ORDER BY c.customer_state
    """
    df = pd.read_sql(query, conn)

    print("\n═══ Q9/Q10: Regional Revenue by Category ═══")
    print(df.to_string(index=False))

    pivot = df.pivot_table(index="state", columns="category", values="revenue", fill_value=0)
    # Sort states by total revenue
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=True).drop("total", axis=1)

    # Clean category names for the legend
    pivot.columns = [col.replace("_", " ").title() for col in pivot.columns]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor(COLORS["bg_dark"])

    # Cohesive minimalist color palette
    cat_colors = ["#4F46E5", "#0D9488", "#3B82F6", "#F43F5E", "#F59E0B"]

    pivot.plot(kind="barh", stacked=True, ax=ax,
               color=cat_colors[:len(pivot.columns)],
               edgecolor="none", width=0.6)

    style_axis(ax, "Regional Revenue Breakdown: Top 8 States × Top 5 Categories",
               xlabel="Revenue (R$)")
    ax.grid(True, axis="x", alpha=0.5, color=COLORS["grid"])
    ax.grid(False, axis="y")
    
    # Hide left spine for clean horizontal bar look
    ax.spines["left"].set_visible(False)
    ax.yaxis.set_tick_params(left=False)

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_brl))
    
    # Legend to the right side, borderless and neat
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9.5, frameon=False)

    plt.tight_layout()
    path = CHARTS_DIR / "05_regional_revenue.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg_dark"])
    plt.close()
    print(f"  → Saved: {path}")
    return pivot


# ═══════════════════════════════════════════════════════════════
# RUN REMAINING QUERIES (print results only)
# ═══════════════════════════════════════════════════════════════
def run_print_queries(conn):
    """Run and print results for queries not tied to charts."""

    # Q2: Top 15 categories by order count
    print("\n═══ Q2: Top 15 Categories by Order Count ═══")
    df = pd.read_sql("""
        SELECT ct.product_category_name_english AS category,
               COUNT(DISTINCT o.order_id) AS total_orders,
               COUNT(oi.order_item_id) AS total_items
        FROM order_items oi
        JOIN orders o     ON oi.order_id = o.order_id
        JOIN products p   ON oi.product_id = p.product_id
        JOIN category_translation ct ON p.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY category ORDER BY total_orders DESC LIMIT 15
    """, conn)
    print(df.to_string(index=False))

    # Q3: Average order value by category
    print("\n═══ Q3: Top 15 Categories by Avg Order Value ═══")
    df = pd.read_sql("""
        SELECT ct.product_category_name_english AS category,
               COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
               ROUND(SUM(oi.price), 2) AS total_revenue
        FROM order_items oi
        JOIN orders o     ON oi.order_id = o.order_id
        JOIN products p   ON oi.product_id = p.product_id
        JOIN category_translation ct ON p.product_category_name = ct.product_category_name
        WHERE o.order_status = 'delivered'
        GROUP BY category HAVING total_orders >= 50
        ORDER BY avg_order_value DESC LIMIT 15
    """, conn)
    print(df.to_string(index=False))

    # Q4: Revenue share
    print("\n═══ Q4: Revenue Share — Top 10 vs Rest ═══")
    df = pd.read_sql("""
        WITH category_revenue AS (
            SELECT ct.product_category_name_english AS category, SUM(oi.price) AS revenue
            FROM order_items oi
            JOIN orders o     ON oi.order_id = o.order_id
            JOIN products p   ON oi.product_id = p.product_id
            JOIN category_translation ct ON p.product_category_name = ct.product_category_name
            WHERE o.order_status = 'delivered'
            GROUP BY category
        ),
        ranked AS (
            SELECT category, revenue, ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rn
            FROM category_revenue
        ),
        total AS (SELECT SUM(revenue) AS grand_total FROM category_revenue)
        SELECT
            CASE WHEN rn <= 10 THEN category ELSE 'All Others' END AS category_group,
            ROUND(SUM(revenue), 2) AS total_revenue,
            ROUND(SUM(revenue) * 100.0 / (SELECT grand_total FROM total), 2) AS pct_share
        FROM ranked GROUP BY category_group ORDER BY total_revenue DESC
    """, conn)
    print(df.to_string(index=False))

    # Q6: Quarterly revenue
    print("\n═══ Q6: Revenue by Quarter ═══")
    df = pd.read_sql("""
        SELECT
            STRFTIME('%Y', o.order_purchase_timestamp) AS year,
            CASE
                WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                ELSE 'Q4'
            END AS quarter,
            COUNT(DISTINCT o.order_id) AS orders,
            ROUND(SUM(oi.price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered' AND o.order_purchase_timestamp IS NOT NULL
        GROUP BY year, quarter ORDER BY year, quarter
    """, conn)
    print(df.to_string(index=False))

    # Q7: Day of week
    print("\n═══ Q7: Revenue by Day of Week ═══")
    df = pd.read_sql("""
        SELECT
            CASE CAST(STRFTIME('%w', o.order_purchase_timestamp) AS INTEGER)
                WHEN 0 THEN 'Sunday'   WHEN 1 THEN 'Monday'   WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END AS day_of_week,
            CAST(STRFTIME('%w', o.order_purchase_timestamp) AS INTEGER) AS day_num,
            COUNT(DISTINCT o.order_id) AS orders,
            ROUND(SUM(oi.price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered' AND o.order_purchase_timestamp IS NOT NULL
        GROUP BY day_of_week, day_num ORDER BY day_num
    """, conn)
    print(df.to_string(index=False))

    # Q12: Payment method by category tier
    print("\n═══ Q12: Payment Methods by Category Tier ═══")
    df = pd.read_sql("""
        WITH cat_tiers AS (
            SELECT ct.product_category_name_english AS category,
                   NTILE(3) OVER (ORDER BY SUM(oi.price) DESC) AS tier
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN category_translation ct ON p.product_category_name = ct.product_category_name
            GROUP BY category
        ),
        order_tiers AS (
            SELECT oi.order_id,
                   MIN(ct_tier.tier) AS tier
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN category_translation ct ON p.product_category_name = ct.product_category_name
            JOIN cat_tiers ct_tier ON ct.product_category_name_english = ct_tier.category
            GROUP BY oi.order_id
        )
        SELECT
            CASE ot.tier WHEN 1 THEN 'Top Tier' WHEN 2 THEN 'Mid Tier' WHEN 3 THEN 'Low Tier' END AS category_tier,
            op.payment_type,
            COUNT(*) AS payment_count,
            ROUND(SUM(op.payment_value), 2) AS total_payment_value,
            ROUND(AVG(op.payment_installments), 1) AS avg_installments
        FROM order_tiers ot
        JOIN order_payments op ON ot.order_id = op.order_id
        JOIN orders o ON ot.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY category_tier, op.payment_type
        ORDER BY category_tier, total_payment_value DESC
    """, conn)
    print(df.to_string(index=False))


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  E-COMMERCE SALES ANALYSIS — Brazilian Olist Dataset")
    print("=" * 60)

    conn = get_connection()

    # Generate charts (also prints query results)
    chart_revenue_by_category(conn)
    chart_monthly_trend(conn)
    chart_category_month_heatmap(conn)
    chart_quarterly_top_categories(conn)
    chart_regional_revenue(conn)

    # Run and print remaining queries
    run_print_queries(conn)

    conn.close()

    print("\n" + "=" * 60)
    print(f"  All charts saved to: {CHARTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
