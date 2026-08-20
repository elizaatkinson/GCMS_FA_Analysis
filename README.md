# Fatty Acid GC–MS Analysis Pipeline

This script processes GC–MS fatty-acid data by combining raw peak-area measurements with sample metadata, normalizing each fatty acid to an internal standard, calculating summary lipid metrics, exporting processed tables to Excel, and generating publication-style figures.

## What the script does

The workflow:

1. reads raw peak-area data from `rawdata.xlsx`
2. reads sample metadata from `sample_info.xlsx`
3. merges both tables using the `Name` column
4. normalizes fatty-acid peak areas using the chosen internal standard (`C17:0`), the amount of internal standard added, and the culture volume used
5. calculates:
   - normalized values for each fatty acid
   - total fatty acids excluding the internal standard
   - lipid content
   - `C16_C18_ratio`
   - saturation
6. creates grouped mean and standard-deviation tables by `Strain`
7. calculates percent contribution of each fatty acid to total fatty acids
8. exports processed datasets to an Excel workbook
9. generates several figures for fatty-acid composition and lipid traits

## Input files

Place these files in the same directory as the script:

- `rawdata.xlsx`
- `sample_info.xlsx`

### Expected key columns

#### In `rawdata.xlsx`
- `Name`
- `C16:0`
- `C16:1`
- `C17:0`
- `C18:0`
- `C18:1`
- `C18:2`

#### In `sample_info.xlsx`
- `Name`
- `Strain`
- `IS`
- `culture_used`
- `CDW_culture`

Additional columns such as `Type` and `Level` may be present and are removed from the normalized export if found.

## Fatty acids used

The script defines the following fatty-acid names:

- `C16:0`
- `C16:1`
- `C17:0`
- `C18:0`
- `C18:1`
- `C18:2`

The internal standard is set as:

- `used_IS = "C17:0"`

## Calculations

### 1. Internal-standard normalization

For each fatty acid column, the normalized value is calculated as:

$$
\text{Normalized FA} = \frac{\text{FA peak area}}{\text{Internal standard peak area}} \times \frac{\text{IS added}}{\text{culture used}}
$$

where the internal standard peak area is taken from `C17:0`.

### 2. Total fatty acids

Total fatty acids are calculated by summing all measured fatty acids except the internal standard:

$$
\text{total FA} = C16{:}0 + C16{:}1 + C18{:}0 + C18{:}1 + C18{:}2
$$

### 3. Lipid content

Lipid content is calculated as:

$$
\text{lipid content} = \frac{\text{total FA}}{1000} \times \frac{100}{\text{CDW culture}}
$$

This converts fatty acids from micrograms to milligrams and expresses lipid content as a percentage of cell dry weight.

### 4. `C16_C18_ratio`

$$
\text{C16/C18 ratio} = \frac{C16{:}0 + C16{:}1}{C18{:}0 + C18{:}1 + C18{:}2}
$$

### 5. Saturation

$$
\text{saturation} = \frac{C16{:}0 + C18{:}0}{C16{:}0 + C16{:}1 + C18{:}0 + C18{:}1 + C18{:}2}
$$

### 6. Fatty-acid distribution

For the fatty-acid composition plot, each fatty acid is converted to a percentage of total fatty acids:

$$
\text{FA percentage} = \frac{\text{normalized FA}}{\text{total FA}} \times 100
$$

## Grouped summary outputs

The script groups samples by `Strain` and calculates mean and standard deviation for numeric columns.

Grouped outputs are produced for:

- normalized values and derived metrics
- fatty-acid percentage composition

Standard-deviation columns are named using the suffix `_sd`.

## Output files

### Excel workbook

The script writes:

- `df_list_python.xlsx`

with the following sheets:

- `df_norm` — normalized per-sample data and derived metrics
- `df_norm_grouped` — grouped mean and SD values by strain
- `df_percent` — per-sample fatty-acid percentages
- `df_percent_grouped` — grouped mean and SD fatty-acid percentages by strain

### Figures

The script saves:

- `result_plot1FA.jpg` — grouped bar chart of fatty-acid composition percentages
- `result_plot1growth.jpg` — scatter plot with error bars for lipid content
- `result_plot_ratios.jpg` — grouped bar chart for `C16_C18_ratio` and saturation
- `result_plot1.jpg` — combined figure with fatty-acid composition and lipid content panels

## Plot descriptions

### 1. Fatty-acid composition plot

A grouped bar chart showing mean percentage contribution of each fatty acid per strain, with standard-deviation error bars.

### 2. Lipid content plot

A point plot showing mean lipid content per strain with standard-deviation error bars.

### 3. Ratio plot

A grouped bar chart showing:

- `C16_C18_ratio`
- `saturation`

for each strain.

### 4. Combined figure

A two-panel figure combining:

- fatty-acid composition
- lipid content

## Dependencies

Install the required packages before running:

```bash
pip install pandas numpy matplotlib openpyxl
```

## How to run

Run the script from a directory containing `rawdata.xlsx` and `sample_info.xlsx`:

```bash
python your_script_name.py
```

## Notes and caveats

- The script assumes that `Name` uniquely links rows between the two input workbooks.
- The internal standard is hard-coded as `C17:0`.
- Total fatty acids exclude the internal standard by design.
- The final print statement mentions `df_list.xlsx`, but the actual file written is `df_list_python.xlsx`.
- The import `Workbook` from `openpyxl` is not used in the script.
- If any required fatty-acid or metadata columns are missing, the script will fail unless the code is adapted.

## Typical use case

Use this script when you want to:

- normalize GC–MS fatty-acid peak areas
- compare lipid traits across strains
- export processed tables for downstream analysis
- generate figure-ready summaries of fatty-acid composition and lipid content
