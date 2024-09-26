from aero_client.utils import register_function


def aero_run(input_data, n_samples: int, n_chains: int, n_reps: int,
             root_path, n_threads: int):
    import os
    import sys
    from aero_client.utils import AeroOutput

    aero_path = os.path.join(root_path, 'Goldstein', 'aero')
    # assumes Chicago-WW-Reff repo is on the endpoint
    os.chdir(aero_path)
    sys.path.append(aero_path)

    import wastewater_harness
    cfg = wastewater_harness.run(n_samples, n_chains, n_reps, root_path, n_threads, input_data)
    outputs = cfg["outputs"]

    return [AeroOutput(name=name, path=path) for name, path in outputs.items()]


print(register_function(aero_run))
