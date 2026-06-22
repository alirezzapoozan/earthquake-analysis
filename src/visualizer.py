import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_histogram(df: pd.DataFrame, output_dir) -> None:

    plt.figure(figsize=(12, 6))

    sns.histplot(data=df, x="mag", hue="source", kde=True, multiple="stack", bins=20)
    plt.title("Distribution of Earthquake Magnitudes by Source")
    plt.xlabel("Magnitude")
    plt.ylabel("Count")
    plt.tight_layout()

    plt.savefig(f"{output_dir}/01_magnitude_distribution.png", dpi=300)

    plt.close()


def plot_weekly_trend(df: pd.DataFrame, output_dir) -> None:

    df_temp = df.copy()
    df_temp.set_index("time", inplace=True)
    weekly_stats = df_temp.resample("W").agg(
        mag=("mag", "mean"), count=("mag", "count")
    )

    fig, ax1 = plt.subplots(figsize=(30, 10))
    ax2 = ax1.twinx()

    sns.lineplot(
        data=weekly_stats,
        x=weekly_stats.index,
        y="count",
        ax=ax1,
        color="b",
        marker="o",
        label="Count",
    )

    sns.lineplot(
        data=weekly_stats,
        x=weekly_stats.index,
        y="mag",
        ax=ax2,
        color="r",
        marker="s",
        label="Avg Mag",
    )

    plt.title("Weekly Trend of Earthquake Count and Avg Magnitude")
    ax1.set_ylabel("Earthquake Count", color="b")
    ax2.set_ylabel("Average Magnitude", color="r")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    ax2.get_legend().remove()

    plt.tight_layout()

    plt.savefig(f"{output_dir}/02_weekly_trend.png", dpi=300)

    plt.close()


def plot_scatter(df: pd.DataFrame, output_dir) -> None:

    plt.figure(figsize=(12, 6))

    sns.scatterplot(
        data=df,
        x="mag",
        y="depth",
        hue="category",
        size="dist_to_tokyo",
        sizes=(20, 200),
        alpha=0.7,
    )

    plt.gca().invert_yaxis()
    plt.title("Earthquake Depth vs. Magnitude")
    plt.xlabel("Magnitude")
    plt.ylabel("Depth (km)")
    plt.tight_layout()

    plt.savefig(f"{output_dir}/03_scatter_depth_vs_mag.png", dpi=300)

    plt.close()


def plot_boxplot(df: pd.DataFrame, output_dir) -> None:

    plt.figure(figsize=(12, 6))

    sns.boxenplot(data=df, x="category", y="depth", order=["weak", "medium", "strong"])

    plt.gca().invert_yaxis()
    plt.title("Depth Distribution across Magnitude Categories")
    plt.tight_layout()

    plt.savefig(f"{output_dir}/04_boxplot_depth_by_categories.png", dpi=300)

    plt.close()


def plot_heatmap_geo_and_distance(df: pd.DataFrame, output_dir) -> None:

    corr = df.select_dtypes(include="number").corr()

    plt.figure(figsize=(18, 12))

    sns.heatmap(corr, annot=True, cmap="Blues", linewidths=0.7)

    plt.title("Earthquake Distribution Relative to Tokyo")
    plt.tight_layout()

    plt.savefig(f"{output_dir}/05_earthquake_heatmap_geo_and_distance.png", dpi=300)

    plt.close()


def generate_plots(df: pd.DataFrame, output_dir) -> None:
    os.makedirs(output_dir, exist_ok=True)

    sns.set_theme(style="whitegrid", context="talk", palette="deep")

    plot_histogram(df, output_dir)
    plot_weekly_trend(df, output_dir)
    plot_scatter(df, output_dir)
    plot_boxplot(df, output_dir)
    plot_heatmap_geo_and_distance(df, output_dir)
