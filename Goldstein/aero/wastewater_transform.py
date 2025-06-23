from aero_client.utils import register_function


def transform(output: str):  # -> AeroOutput
    import pandas as pd
    import numpy as np
    from aero_client.utils import AeroOutput

    # load input
    odata = pd.read_csv(output)

    odata = odata.loc[
        odata.method != 0, ["sars_cov_2", "sample_collect_date"]
    ].reset_index(drop=True)
    odata.columns = ["gene_copy", "date"]

    # convert date to numerical (equivalent to what R does)
    reference_date = pd.Timestamp("1970-01-01")
    odata["date"] = pd.to_datetime(odata["date"])
    odata["num_date"] = (odata["date"] - reference_date).dt.days
    odata["year"] = np.nan
    odata["year"] = odata["date"].dt.year.astype(np.float32)

    odata["yearday"] = odata["date"].dt.day_of_year

    # days since first day of 2022
    ts_2022 = pd.Timestamp("2022-01-01")
    # not 0 based
    odata["year_day"] = (odata["date"] - ts_2022).dt.days + 1
    odata['new_time'] = odata['year_day'] - (odata['year_day'].iloc[0] - 1)

    # calculate values
    odata["sum_genes"] = odata["gene_copy"]
    odata["log_gene_copies"] = np.where(odata["gene_copy"] == 0, 0, np.log10(odata["gene_copy"]))

    odata["epi_week2"] = (odata["yearday"] - 1) / 7 + 1
    odata["epi_week"] = np.floor(odata["epi_week2"])

    # foo
    odata.to_csv(output, index=False)
    return AeroOutput(name="output", path=output)

print(register_function(transform))
