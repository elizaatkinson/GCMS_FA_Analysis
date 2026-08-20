# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 15:31:26 2026

@author: ea2915
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from openpyxl import Workbook


# =============================
# Load packages and import data
# =============================
rawdata = pd.read_excel("rawdata.xlsx")
df = pd.read_excel("sample_info.xlsx")

# Define the FA names
FA_names = ["C16:0", "C16:1", "C17:0", "C18:0", "C18:1", "C18:2"]

# Add rawdata to the data frame that contains other sample information
df = df.merge(rawdata, on="Name", how="left")


# ======================================
# Normalization, cleaning, and grouping
# ======================================
used_IS = "C17:0"  # internal standard used for the experiment

# Normalizing peak areas based on the peak of the internal standard,
# the IS added to the sample, and the amount of culture used in the FAME
df_norm = df.copy()
for col_name in FA_names:
    df_norm[col_name] = df[col_name] / df[used_IS] * df["IS"] / df["culture_used"]

# Sum all FAs except the internal standard used
FAs = [fa for fa in FA_names if fa != used_IS]
df_norm["total_FA"] = df_norm[FAs].sum(axis=1)

# Calculate lipid content
# 1000 converts µg FA to mg FA; *100 converts fraction to percent
df_norm["lipid_content"] = (df_norm["total_FA"] / 1000) * 100 / df_norm["CDW_culture"]

# Remove unnecessary columns
rm_col = [used_IS, "Name", "IS", "culture_used", "Type", "Level"]
df_norm = df_norm.drop(columns=[c for c in rm_col if c in df_norm.columns])

# Calculate C16/C18 ratio
df_norm["C16_C18_ratio"] = (
    (df_norm["C16:0"] + df_norm["C16:1"]) /
    (df_norm["C18:0"] + df_norm["C18:1"] + df_norm["C18:2"])
)

# Calculate saturation
df_norm["saturation"] = (
    (df_norm["C16:0"] + df_norm["C18:0"]) /
    (df_norm["C16:0"] + df_norm["C16:1"] + df_norm["C18:0"] + df_norm["C18:1"] + df_norm["C18:2"])
)

# Group samples by Strain to calculate mean and SD
numeric_cols = df_norm.select_dtypes(include=[np.number]).columns.tolist()
df_norm_grouped = (
    df_norm.groupby("Strain")[numeric_cols]
    .agg(["mean", "std"])
)

# Flatten multi-index column names to match the R-style output
flattened_cols = []
for col, stat in df_norm_grouped.columns:
    if stat == "mean":
        flattened_cols.append(col)
    elif stat == "std":
        flattened_cols.append(f"{col}_sd")
    else:
        flattened_cols.append(f"{col}_{stat}")

df_norm_grouped.columns = flattened_cols
df_norm_grouped = df_norm_grouped.reset_index()


# =================
# FA distribution
# =================
# Calculate the % each FA contributes to total FAs
df_percent = df_norm.copy()
df_percent[FAs] = df_percent[FAs].div(df_percent["total_FA"], axis=0) * 100

# Group samples by Strain to calculate mean and SD
numeric_cols_percent = df_percent.select_dtypes(include=[np.number]).columns.tolist()
df_percent_grouped = (
    df_percent.groupby("Strain")[numeric_cols_percent]
    .agg(["mean", "std"])
)

# Flatten multi-index column names to match the R-style output
flattened_cols = []
for col, stat in df_percent_grouped.columns:
    if stat == "mean":
        flattened_cols.append(col)
    elif stat == "std":
        flattened_cols.append(f"{col}_sd")
    else:
        flattened_cols.append(f"{col}_{stat}")

df_percent_grouped.columns = flattened_cols
df_percent_grouped = df_percent_grouped.reset_index()


# =======================
# Export all dataframes
# =======================
df_list_path = Path("df_list_python.xlsx")
if df_list_path.exists():
    df_list_path.unlink()

with pd.ExcelWriter("df_list_python.xlsx", engine="openpyxl") as writer:
    df_norm.to_excel(writer, sheet_name="df_norm", index=False)
    df_norm_grouped.to_excel(writer, sheet_name="df_norm_grouped", index=False)
    df_percent.to_excel(writer, sheet_name="df_percent", index=False)
    df_percent_grouped.to_excel(writer, sheet_name="df_percent_grouped", index=False)


# =========
# Plotting
# =========
# Personalized theme settings
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 16,
    "legend.fontsize": 12,
})

# Set colors
col_bar_fa = ['#4472C4', '#9DC3E6', '#BF9000', '#FFD966', '#FFF2CC']
col_growth = ['darkgrey']
col_ratios = ['#D62728', '#17BECF']


# ===========================
# Reshaping data for plotting
# ===========================
# Mean dataframe: columns without _sd
mean_cols = [c for c in df_percent_grouped.columns if not c.endswith("_sd")]
df_mean = df_percent_grouped[mean_cols].melt(
    id_vars=["Strain"],
    var_name="fatty_acid",
    value_name="mean"
)

# SD dataframe: only columns with _sd
sd_cols = ["Strain"] + [c for c in df_percent_grouped.columns if c.endswith("_sd")]
df_sd = df_percent_grouped[sd_cols].melt(
    id_vars=["Strain"],
    var_name="fatty_acid",
    value_name="sd"
)
df_sd["fatty_acid"] = df_sd["fatty_acid"].str.replace("_sd", "", regex=False)

# Merge the two dataframes
df_plot = pd.merge(df_mean, df_sd, on=["Strain", "fatty_acid"], how="inner")

# Optional cleanup
# del df_mean, df_sd


# =============================
# Create bar plots of % of FAs
# =============================
def grouped_barplot(ax, data, categories, colors, ylabel, ylim=None, legend_title=None):
    strains = data["Strain"].unique().tolist()
    n_groups = len(strains)
    n_cats = len(categories)
    x = np.arange(n_groups)
    width = 0.6 / n_cats

    for i, cat in enumerate(categories):
        sub = data[data["fatty_acid"] == cat].set_index("Strain").reindex(strains)
        xpos = x - 0.3 + width / 2 + i * width
        ax.bar(
            xpos,
            sub["mean"],
            width=width,
            color=colors[i],
            edgecolor="black",
            label=cat
        )
        ax.errorbar(
            xpos,
            sub["mean"],
            yerr=sub["sd"],
            fmt="none",
            ecolor="black",
            elinewidth=1,
            capsize=4
        )

    ax.set_xticks(x)
    ax.set_xticklabels(strains, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(axis="y", linestyle="--", color="grey", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if ylim is not None:
        ax.set_ylim(*ylim)
    if legend_title is None:
        ax.legend(frameon=False)
    else:
        ax.legend(title=legend_title, frameon=False)


# Plot 1: FA percentages
fig1, ax1 = plt.subplots(figsize=(12, 8))
plot1_data = df_plot[df_plot["fatty_acid"].isin(FAs)].copy()
grouped_barplot(
    ax1,
    plot1_data,
    FAs,
    col_bar_fa,
    ylabel="% of each Fatty Acid",
    ylim=(0, 60),
    legend_title="fatty acid"
)
fig1.tight_layout()
fig1.savefig("result_plot1FA.jpg", dpi=300)


# Plot 2: Lipid content
# Build a plot-ready dataframe for lipid content from df_norm_grouped
lipid_plot = df_norm_grouped[["Strain", "lipid_content", "lipid_content_sd"]].copy()
lipid_plot = lipid_plot.rename(columns={"lipid_content": "mean", "lipid_content_sd": "sd"})

fig2, ax2 = plt.subplots(figsize=(12, 8))
x = np.arange(len(lipid_plot))
ax2.errorbar(
    x,
    lipid_plot["mean"],
    yerr=lipid_plot["sd"],
    fmt="none",
    ecolor="black",
    elinewidth=1,
    capsize=4,
    zorder=1
)
ax2.scatter(x, lipid_plot["mean"], color=col_growth[0], s=80, zorder=2)
ax2.set_xticks(x)
ax2.set_xticklabels(lipid_plot["Strain"], fontweight="bold")
ax2.set_ylabel("Lipid content [%]")
ax2.set_xlabel("")
ax2.set_ylim(0, 25)
ax2.set_yticks([5, 10, 15, 20, 25])
ax2.grid(axis="y", linestyle="--", color="grey", alpha=0.5)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
legend_elements = [Line2D([0], [0], marker='o', color='w', label='lipid_content', markerfacecolor=col_growth[0], markersize=10)]
ax2.legend(handles=legend_elements, frameon=False)
fig2.tight_layout()
fig2.savefig("result_plot1growth.jpg", dpi=300)


# Plot 3: C16/C18 ratio and saturation
ratio_cols = ["C16_C18_ratio", "saturation"]
ratio_plot = df_norm_grouped[["Strain", "C16_C18_ratio", "C16_C18_ratio_sd", "saturation", "saturation_sd"]].copy()
ratio_mean = ratio_plot[["Strain", "C16_C18_ratio", "saturation"]].melt(
    id_vars=["Strain"], var_name="fatty_acid", value_name="mean"
)
ratio_sd = ratio_plot[["Strain", "C16_C18_ratio_sd", "saturation_sd"]].melt(
    id_vars=["Strain"], var_name="fatty_acid", value_name="sd"
)
ratio_sd["fatty_acid"] = ratio_sd["fatty_acid"].str.replace("_sd", "", regex=False)
ratio_df = ratio_mean.merge(ratio_sd, on=["Strain", "fatty_acid"])

fig3, ax3 = plt.subplots(figsize=(12, 8))
grouped_barplot(
    ax3,
    ratio_df,
    ratio_cols,
    col_ratios,
    ylabel="C16/C18 ratio and saturation",
    ylim=(0, 0.5),
    legend_title=None
)
fig3.tight_layout()
fig3.savefig("result_plot_ratios.jpg", dpi=300)


# Save combined figure
fig_combined, axes = plt.subplots(2, 1, figsize=(14, 14), gridspec_kw={"height_ratios": [1.2, 1]})

# Recreate FA plot on combined figure
grouped_barplot(
    axes[0],
    plot1_data,
    FAs,
    col_bar_fa,
    ylabel="% of each Fatty Acid",
    ylim=(0, 60),
    legend_title="fatty acid"
)

# Recreate lipid content plot on combined figure
x = np.arange(len(lipid_plot))
axes[1].errorbar(
    x,
    lipid_plot["mean"],
    yerr=lipid_plot["sd"],
    fmt="none",
    ecolor="black",
    elinewidth=1,
    capsize=4,
    zorder=1
)
axes[1].scatter(x, lipid_plot["mean"], color=col_growth[0], s=80, zorder=2)
axes[1].set_xticks(x)
axes[1].set_xticklabels(lipid_plot["Strain"], fontweight="bold")
axes[1].set_ylabel("Lipid content [%]")
axes[1].set_xlabel("")
axes[1].set_ylim(0, 25)
axes[1].set_yticks([5, 10, 15, 20, 25])
axes[1].grid(axis="y", linestyle="--", color="grey", alpha=0.5)
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
axes[1].legend(handles=legend_elements, frameon=False)

fig_combined.tight_layout()
fig_combined.savefig("result_plot1.jpg", dpi=300)
plt.close('all')

print("Pipeline completed successfully.")
print("Generated files:")
print("- df_list.xlsx")
print("- result_plot1FA.jpg")
print("- result_plot1growth.jpg")
print("- result_plot_ratios.jpg")
print("- result_plot1.jpg")
