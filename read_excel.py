import pandas as pd
from config import config


def read_excel():
    # Read all sheets from the spectroscopy Excel file as dataframes (no header row)
    tabs = pd.read_excel(config["data_path"], header=None, sheet_name=None)

    long_dfs = []

    for tab_name, df in tabs.items():
        print(f"Processing tab: {tab_name}")
        if tab_name == "4 mA":
            print("Skipping 4 mA tab")
            continue

        for i in range(1, len(df.columns), 2):
            print(f"Processing column: {i}")
            wn = df[i - 1]
            currents = df[i]
            if wn.iloc[0] < 3000:
                print(f"Skipping column: {i} because wn[0] < 3000")
                continue
            long_dfs.append(
                pd.DataFrame(
                    {
                        "sample": tab_name,
                        "experiment": f"exp{i // 2 + 1}",
                        "wn": wn,
                        "int": currents,
                    }
                )
            )

    # Concatenate all long-form pieces into a single tidy dataframe
    long_df = pd.concat(long_dfs, ignore_index=True)

    # ------------------------------------------------------------------
    # Integrate current vs voltage file to add current (A) column
    # ------------------------------------------------------------------
    try:
        iv_df = pd.read_excel("./data/current vs voltage.xlsx")
        # Be robust to arbitrary column names: take first col as current (A), second as cell voltage
        current_col = iv_df.columns[0]
        voltage_col = iv_df.columns[1]
        iv_df = iv_df.rename(columns={current_col: "current_A", voltage_col: "cell_voltage"})

        # Extract current in mA from sample name like "50 mA" and convert to A
        long_df["current_A"] = (
            long_df["sample"].str.split().str[0].astype(float) / 1000.0
        )

        # Merge to also attach cell voltage (and to ensure we use the exact A values from the file)
        long_df = long_df.merge(
            iv_df, how="left", on="current_A"
        )
    except FileNotFoundError:
        # If the IV file is missing, we still keep long_df without the extra columns
        print("Warning: './data/current vs voltage.xlsx' not found; skipping current/voltage merge.")

    long_df.to_csv("./data/long_df.csv", index=False)
    return long_df

if __name__ == "__main__":
    long_df = read_excel()
    print(long_df)
