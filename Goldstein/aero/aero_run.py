from aero_client.utils import register_function


def aero_run(waste_water_data, n_samples: int, n_chains: int, n_reps: int,
             root_path, waste_water_site: str, n_threads: int):
    """Run the wastewater harness"""
    import os
    import sys
    from aero_client.utils import AeroOutput

    aero_path = os.path.join(root_path, 'Goldstein', 'aero')
    # assumes Chicago-WW-Reff repo is on the endpoint
    os.chdir(aero_path)
    sys.path.append(aero_path)

    import wastewater_harness
    cfg = wastewater_harness.run(n_samples, n_chains, n_reps, root_path, n_threads,
                                 waste_water_site, waste_water_data)
    print("3")
    outputs = cfg["outputs"]

    return [AeroOutput(name=name, path=path) for name, path in outputs.items()]


import os
if os.getenv('GLOBUS_COMPUTE_CLIENT_ID') is None:
    print("GLOBUS_COMPUTE_CLIENT_ID is not defined")
else:
    print(register_function(aero_run))
