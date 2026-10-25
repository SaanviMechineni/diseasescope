import pandas as pd
import numpy as np

# -----------------------------------
# LOAD DATASET
# -----------------------------------

file_path = "data/india_5_diseases_enriched.xlsx"

df = pd.read_excel(
    file_path,
    sheet_name="All Diseases (combined)"
)

print("=" * 60)
print("DISEASE INCIDENCE ANALYSIS")
print("=" * 60)

print("\nDATASET SHAPE:")
print(df.shape)

# -----------------------------------
# Q1: MEAN DISEASE INCIDENCE
# -----------------------------------

print("\n" + "=" * 60)
print("Q1: MEAN DISEASE INCIDENCE")
print("=" * 60)

disease_mean = (
    df.groupby("Disease")["Incidence_per_100k"]
    .mean()
    .reset_index()
)

disease_mean.columns = [
    "Disease",
    "Mean_Incidence"
]

print("\nMean incidence for each disease:")
print(disease_mean)
# -----------------------------------
# Q1: NUMPY MEAN VERIFICATION
# -----------------------------------

print("\nNumPy Mean Verification:")

for disease in df["Disease"].unique():

    values = df.loc[
        df["Disease"] == disease,
        "Incidence_per_100k"
    ].dropna()

    mean_value = np.mean(values)

    print(f"{disease}: {mean_value:.2f}")
    # -----------------------------------
# SAVE Q1 RESULT
# -----------------------------------

disease_mean["Mean_Incidence"] = disease_mean["Mean_Incidence"].round(2)

disease_mean.to_csv(
    "data/disease_mean.csv",
    index=False
)

print("\nQ1 result saved to data/disease_mean.csv")
# -----------------------------------
# Q2: FILTER SPECIFIC DISEASE
# -----------------------------------

print("\n" + "=" * 60)
print("Q2: FILTER SPECIFIC DISEASE")
print("=" * 60)

selected_disease = "Dengue"

disease_data = df[
    df["Disease"] == selected_disease
]

print(f"\nFiltered data for: {selected_disease}")

print(
    disease_data[
        [
            "Disease",
            "State",
            "Region",
            "Year",
            "Cases",
            "Deaths",
            "Incidence_per_100k"
        ]
    ].to_string(index=False)
)
# -----------------------------------
# Q2: FILTER MULTIPLE DISEASES
# -----------------------------------

selected_diseases = [
    "Dengue",
    "Malaria"
]

filtered_data = df[
    df["Disease"].isin(selected_diseases)
]

print("\nFiltered diseases:")
print(selected_diseases)

print("\nNumber of filtered records:")
print(len(filtered_data))
# -----------------------------------
# Q2: FILTER BY DISEASE, YEAR AND REGION
# -----------------------------------

selected_disease = "Dengue"
selected_year = 2024
selected_region = "South"

filtered_data = df[
    (df["Disease"] == selected_disease) &
    (df["Year"] == selected_year) &
    (df["Region"] == selected_region)
]

print("\nDisease + Year + Region Filter:")

print(
    filtered_data[
        [
            "Disease",
            "State",
            "Region",
            "Year",
            "Cases",
            "Deaths",
            "Incidence_per_100k"
        ]
    ].to_string(index=False)
)
# -----------------------------------
# Q3: IMPUTE MISSING INCIDENCE DATA
# -----------------------------------

print("\n" + "=" * 60)
print("Q3: IMPUTE MISSING INCIDENCE DATA")
print("=" * 60)

# Check missing values before imputation
missing_before = df["Incidence_per_100k"].isnull().sum()

print("\nMissing incidence values BEFORE imputation:")
print(missing_before)

# Impute missing incidence using
# disease-wise median
df["Incidence_per_100k"] = (
    df.groupby("Disease")["Incidence_per_100k"]
    .transform(
        lambda x: x.fillna(x.median())
    )
)

# Check missing values after imputation
missing_after = df["Incidence_per_100k"].isnull().sum()

print("\nMissing incidence values AFTER imputation:")
print(missing_after)
# -----------------------------------
# Q4: GROUP AND SUMMARIZE BY
# DISEASE AND STATE
# -----------------------------------

print("\n" + "=" * 60)
print("Q4: GROUP AND SUMMARIZE BY DISEASE AND STATE")
print("=" * 60)

state_summary = (
    df.groupby(["Disease", "State"])
    .agg(
        Mean_Incidence=("Incidence_per_100k", "mean"),
        Total_Cases=("Cases", "sum"),
        Total_Deaths=("Deaths", "sum")
    )
    .reset_index()
)

# Round incidence for cleaner output
state_summary["Mean_Incidence"] = (
    state_summary["Mean_Incidence"].round(2)
)

print("\nDisease-State Summary:")
print(state_summary.to_string(index=False))
# Save Q4 summary

state_summary.to_csv(
    "data/disease_state_summary.csv",
    index=False
)

print("\nQ4 result saved to data/disease_state_summary.csv")
# -----------------------------------
# HIGHEST INCIDENCE STATE FOR EACH DISEASE
# -----------------------------------

highest_incidence = (
    state_summary
    .loc[
        state_summary.groupby("Disease")["Mean_Incidence"]
        .idxmax()
    ]
)

print("\nHighest incidence state for each disease:")

print(
    highest_incidence[
        [
            "Disease",
            "State",
            "Mean_Incidence"
        ]
    ].to_string(index=False)
)
# -----------------------------------
# Q5: INCIDENCE TRENDS BY REGION
# -----------------------------------

print("\n" + "=" * 60)
print("Q5: INCIDENCE TRENDS BY REGION")
print("=" * 60)

region_summary = (
    df.groupby(
        ["Disease", "Region", "Year"]
    )["Incidence_per_100k"]
    .mean()
    .reset_index()
)

region_summary["Incidence_per_100k"] = (
    region_summary["Incidence_per_100k"].round(2)
)

print("\nRegional incidence summary:")
print(region_summary.head(20).to_string(index=False))
# -----------------------------------
# Q5: REGIONAL TREND PLOT
# -----------------------------------

import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(12, 6))

sns.lineplot(
    data=region_summary,
    x="Year",
    y="Incidence_per_100k",
    hue="Region",
    marker="o"
)

plt.title("Disease Incidence Trends by Region")
plt.xlabel("Year")
plt.ylabel("Mean Incidence per 100,000")
plt.legend(title="Region")
plt.grid(True)

plt.tight_layout()

# Save BEFORE plt.show(): show() hands the figure to the window and closes it,
# so saving afterwards writes an empty canvas.
plt.savefig(
    "data/regional_incidence_trends.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
# -----------------------------------
# Q5: DISEASE-SPECIFIC REGIONAL TREND
# -----------------------------------

selected_disease = "Dengue"

disease_region_data = region_summary[
    region_summary["Disease"] == selected_disease
]

plt.figure(figsize=(12, 6))

sns.lineplot(
    data=disease_region_data,
    x="Year",
    y="Incidence_per_100k",
    hue="Region",
    marker="o"
)

plt.title(
    f"{selected_disease} Incidence Trends by Region"
)

plt.xlabel("Year")
plt.ylabel("Incidence per 100,000")
plt.legend(title="Region")
plt.grid(True)

plt.tight_layout()

plt.savefig(
    "data/dengue_regional_trends.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
# Save Q5 regional summary

region_summary.to_csv(
    "data/regional_incidence_summary.csv",
    index=False
)

print(
    "\nQ5 result saved to "
    "data/regional_incidence_summary.csv"
)
