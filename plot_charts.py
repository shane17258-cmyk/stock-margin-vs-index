import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "Arial Unicode MS", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def plot_single(data_file, title, output_file, ylabel_idx, ylabel_margin):
    filepath = os.path.join(DATA_DIR, data_file)
    df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    df["index_value"] = pd.to_numeric(df["index_value"], errors="coerce")
    df["margin_change"] = pd.to_numeric(df["margin_change"], errors="coerce")

    df = df.dropna(subset=["index_value"])
    df = df[df["date"] >= "2026-01-01"]
    df = df.set_index("date")

    fig, ax1 = plt.subplots(figsize=(16, 7))

    ax1.plot(df.index, df["index_value"], color="#1a73e8", linewidth=2, label=ylabel_idx)
    ax1.set_xlabel("日期", fontsize=13)
    ax1.set_ylabel(ylabel_idx, color="#1a73e8", fontsize=13)
    ax1.tick_params(axis="y", labelcolor="#1a73e8")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    margin = df["margin_change"].dropna()
    colors = ["#e74c3c" if v > 0 else "#2ecc71" if v < 0 else "#999" for v in margin]
    ax2.bar(margin.index, margin, color=colors, alpha=0.6, width=1.2, label="融資增減(張)")
    ax2.set_ylabel(ylabel_margin, color="#e74c3c", fontsize=13)
    ax2.tick_params(axis="y", labelcolor="#e74c3c")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best", fontsize=11)

    plt.title(title, fontsize=16, fontweight="bold", pad=15)
    fig.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, output_file), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {output_file}")

def plot_all():
    print("Generating charts...")
    plot_single(
        "twse_data.csv",
        "台股上市加權指數 vs 融資增減 (2026)",
        "twse_chart.png",
        "上市加權指數",
        "融資增減 (張)",
    )
    plot_single(
        "tpex_data.csv",
        "台股上櫃指數 vs 融資增減 (2026)",
        "tpex_chart.png",
        "上櫃指數",
        "融資增減 (張)",
    )
    print("Done!")

if __name__ == "__main__":
    plot_all()
