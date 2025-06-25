from aero_client.utils import register_function


def aero_run_aggregate_plot(obrien_data, calumet_data, stickney_south_data, stickney_north_data, root_path):
    """Run the wastewater harness"""
    import os
    import sys
    from aero_client.utils import AeroOutput

    aero_path = os.path.join(root_path, "Goldstein", "aero")
    # assumes Chicago-WW-Reff repo is on the endpoint
    os.chdir(aero_path)
    sys.path.append(aero_path)

    import aggregate_plot_harness

    cfg = aggregate_plot_harness.run(
        obrien_data, calumet_data, stickney_south_data, stickney_north_data, root_path
    )
    outputs = cfg["outputs"]

    return [AeroOutput(name=name, path=path) for name, path in outputs.items()]


import os

if os.getenv("GLOBUS_COMPUTE_CLIENT_ID") is None:
    print("GLOBUS_COMPUTE_CLIENT_ID is not defined")
else:
    print(register_function(aero_run_aggregate_plot))
