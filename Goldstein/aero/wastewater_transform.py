from aero_client.utils import register_function


def transform(output: str):  # -> AeroOutput
    import pandas as pd
    import numpy as np
    from aero_client.utils import AeroOutput

    # load input
    odata = pd.read_csv(output)

    # keep relevant info, rename
    odata = odata.loc[
        odata.method != 0, ["sars_cov_2", "sample_collect_date"]
    ].reset_index(drop=True)
    odata.columns = ["gene_copy", "date"]

    # convert date to numerical (equivalent to what R does)
    reference_date = pd.Timestamp("1970-01-01")
    odata["date"] = pd.to_datetime(odata["date"])
    odata["num_date"] = (odata["date"] - reference_date).dt.days

    # assign year
    odata["year"] = np.nan
    odata.loc[odata["num_date"] < 19358, "year"] = 2022
    odata.loc[(odata["num_date"] >= 19358) & (odata["num_date"] < 19724), "year"] = 2023
    odata.loc[odata["num_date"] >= 19724, "year"] = 2024

    # calculate yearday and time
    odata["yearday"] = odata["num_date"]
    odata.loc[odata["year"] == 2022, "yearday"] = (
        odata.loc[odata["year"] == 2022, "num_date"] - (52 * 365) - 12
    )
    odata.loc[odata["year"] == 2023, "yearday"] = (
        odata.loc[odata["year"] == 2023, "num_date"] - (53 * 365) - 12
    )
    odata.loc[odata["year"] == 2024, "yearday"] = (
        odata.loc[odata["year"] == 2024, "num_date"] - (54 * 365) - 12
    )

    odata["year_day"] = odata["num_date"] - (52 * 365) - 12
    odata['new_time'] = odata['year_day'] - (odata['year_day'].iloc[0] - 1)

    # calculate values
    odata["sum_genes"] = odata["gene_copy"]
    odata["log_gene_copies"] = np.log10(odata["gene_copy"])

    odata["epi_week2"] = (odata["yearday"] - 1) / 7 + 1
    odata["epi_week"] = np.floor(odata["epi_week2"])

    odata.to_csv(output, index=False)
    return AeroOutput(name="output", path=output)


print(register_function(transform))
