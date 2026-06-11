"""
Clay Partner Tier Analysis - Charts
=====================================
Generates 4 charts from the scraped partner data.
Run from the project root: python dashboard/charts.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "dashboard"

# Clay logo colors (exact shades from clay.com brand)
YELLOW  = "#fcd251"   # logo yellow
ORANGE  = "#f76659"   # logo orange
BLUE    = "#02c5e3"   # logo blue
BLACK   = "#1A1A1A"   # wordmark near-black (4th color when needed)

BG      = "#FFFFFF"   # clean white background
TEXT    = "#1A1A1A"

# 4 tiers = 4 colors, ordered from highest to lowest
COLORS = {
    "Elite Studio":    YELLOW,
    "Studio":          ORANGE,
    "Advanced Artisan": BLUE,
    "Artisan":         BLACK,
}

import matplotlib as mpl
mpl.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    BG,
    "savefig.facecolor": BG,
    "text.color":        TEXT,
    "axes.labelcolor":   TEXT,
    "xtick.color":       TEXT,
    "ytick.color":       TEXT,
    "axes.edgecolor":    "#CCCCCC",
    "font.family":       "sans-serif",
})

TIER_ORDER = ["Elite Studio", "Studio", "Advanced Artisan", "Artisan"]

def load_data():
    plist = pd.read_csv(PROCESSED / "partners_list.csv")
    pdetail = pd.read_csv(PROCESSED / "partners_detail.csv")
    df = plist.merge(pdetail, on="slug", how="left")
    df["expertise_count"] = df["expertise"].fillna("").apply(
        lambda x: len(x.split(",")) if x else 0)
    df["language_count"] = df["language"].fillna("").apply(
        lambda x: len(x.split(",")) if x else 0)
    df["profile_length"] = df["description_len"].fillna(0)
    return df


# ---- Chart 1: Tier pyramid ----------------------------------------
def chart_tier_pyramid(df):
    counts = df.groupby("tier").size().reindex(TIER_ORDER)
    pct = (counts / counts.sum() * 100).round(1)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(
        TIER_ORDER,
        counts.values,
        color=[COLORS[t] for t in TIER_ORDER],
        edgecolor="white", linewidth=0.5
    )
    for bar, count, p in zip(bars, counts.values, pct.values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{count} ({p}%)", va="center", fontsize=11, color="#333")

    ax.set_xlabel("Number of Partners", fontsize=11)
    ax.set_title("Clay Partner Tier Distribution\n170 partners, June 2026",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_xlim(0, counts.max() * 1.25)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(left=False)
    plt.tight_layout()
    plt.savefig(OUT / "chart1_tier_pyramid.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved chart1_tier_pyramid.png")


# ---- Chart 2: Expertise breadth by tier ---------------------------
def chart_expertise_breadth(df):
    avg = df[df["expertise_count"] > 0].groupby("tier")["expertise_count"]\
        .mean().reindex(TIER_ORDER)
    profile = df.groupby("tier")["profile_length"]\
        .mean().reindex(TIER_ORDER) / 1000  # in thousands

    fig, ax1 = plt.subplots(figsize=(8, 5))
    x = range(len(TIER_ORDER))
    bars = ax1.bar(x, avg.values,
                   color=[COLORS[t] for t in TIER_ORDER],
                   edgecolor="white", linewidth=0.5, width=0.5)
    for bar, val in zip(bars, avg.values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f"{val:.1f}", ha="center", fontsize=11, fontweight="bold")

    ax2 = ax1.twinx()
    ax2.plot(x, profile.values, color="#be82fa",
             marker="o", linewidth=2, markersize=7, label="Avg profile length (k chars)")
    ax2.set_ylabel("Avg Profile Length (k chars)", fontsize=10, color="#be82fa")
    ax2.tick_params(axis="y", labelcolor="#be82fa")

    ax1.set_xticks(x)
    ax1.set_xticklabels(TIER_ORDER, fontsize=10)
    ax1.set_ylabel("Avg Expertise Tags Listed", fontsize=11)
    ax1.set_title("Expertise Breadth & Profile Richness by Tier",
                  fontsize=13, fontweight="bold", pad=15)
    ax1.set_ylim(0, avg.max() * 1.3)
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.spines[["top", "left"]].set_visible(False)
    line_patch = mpatches.Patch(color="#be82fa", label="Avg profile length (k chars)")
    ax1.legend(handles=[line_patch], loc="upper right", fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT / "chart2_expertise_breadth.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved chart2_expertise_breadth.png")


# ---- Chart 3: Salesforce vs HubSpot by tier -----------------------
def chart_crm_penetration(df):
    crm = df.groupby("tier")[["mentions_hubspot", "mentions_salesforce"]]\
        .mean().reindex(TIER_ORDER) * 100

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(TIER_ORDER))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], crm["mentions_salesforce"],
               width=width, color=BLUE, label="Salesforce")
    bars2 = ax.bar([i + width/2 for i in x], crm["mentions_hubspot"],
               width=width, color=ORANGE, label="HubSpot")

    for bars in [bars1, bars2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1,
                    f"{h:.0f}%", ha="center", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(TIER_ORDER, fontsize=10)
    ax.set_ylabel("% of Partners Mentioning CRM", fontsize=11)
    ax.set_title("CRM Ecosystem by Tier\nSalesforce dominates at higher tiers",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_ylim(0, 120)
    ax.legend(fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "chart3_crm_penetration.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved chart3_crm_penetration.png")


# ---- Chart 4: Minimum engagement by tier --------------------------
def chart_min_engagement(df):
    df2 = df.copy()
    df2["min_eng_clean"] = df2["min_engagement"].fillna("").apply(
        lambda x: x.split(",")[0].strip() if x else "Unknown"
    )
    df2 = df2[df2["min_eng_clean"].isin(["1 month", "3 months", "6 months"])]

    pivot = df2.groupby(["tier", "min_eng_clean"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(TIER_ORDER)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(8, 5))
    engagement_colors = {
    "1 month":  BLUE,
    "3 months": ORANGE,
    "6 months": YELLOW,
    }
    bottom = pd.Series([0.0] * len(TIER_ORDER), index=TIER_ORDER)
    for col in ["1 month", "3 months", "6 months"]:
        if col in pct.columns:
            ax.bar(TIER_ORDER, pct[col], bottom=bottom,
                   label=col, color=engagement_colors[col],
                   edgecolor="white", linewidth=0.5)
            for i, (tier, val) in enumerate(zip(TIER_ORDER, pct[col])):
                if val > 8:
                    ax.text(i, bottom[tier] + val / 2,
                            f"{val:.0f}%", ha="center",
                            va="center", fontsize=10, color="white",
                            fontweight="bold")
            bottom += pct[col]

    ax.set_ylabel("% of Partners", fontsize=11)
    ax.set_title("Minimum Engagement Length by Tier\n3-month commitments dominate at Elite",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_ylim(0, 110)
    ax.legend(fontsize=10, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "chart4_min_engagement.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved chart4_min_engagement.png")


if __name__ == "__main__":
    df = load_data()
    chart_tier_pyramid(df)
    chart_expertise_breadth(df)
    chart_crm_penetration(df)
    chart_min_engagement(df)
    print("\nAll charts saved to dashboard/")