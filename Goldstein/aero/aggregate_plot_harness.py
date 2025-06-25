import datetime
from pathlib import Path
from typing import Dict, Union
import os
import subprocess
import yaml

PathLike = Union[str, bytes, os.PathLike]


def run_aggregate_plot(plot_r: PathLike, cfg: Dict, cfg_file: PathLike):
    # Rscript doesn't return error code or raise exception error,
    # so check that the plot is created as expected
    expected_plot = os.path.join(cfg["out_dir"], cfg["aggregate_plot_name"])
    args = ["Rscript", plot_r, cfg_file]
    res = subprocess.run(args, check=False, capture_output=True, text=True)
    if not os.path.exists(expected_plot):
        raise ValueError(res.stderr)

    cfg["outputs"]["aggregate_plot"] = expected_plot


def write_cfg(cfg: Dict):
    out_dir = cfg["out_dir"]
    cfg_file = os.path.join(out_dir, f"aggregate_plot_cfg_{cfg['ts']}.yaml")
    with open(cfg_file, "w") as f_out:
        yaml.safe_dump(cfg, f_out)
    return cfg_file


def run(obrien_data, calumet_data, stickney_south_data, stickney_north_data, root_path: PathLike):
    out_path = Path(root_path, 'Goldstein', 'aero', 'output')
    out_path.mkdir(exist_ok=True)
    plot_r = str(Path(root_path, "Goldstein", "aero", "aggregate_plot.R"))

    now = datetime.datetime.now()
    ts = now.strftime('%Y%m%d_%H%M%S')
    cfg = {
        "out_dir": str(out_path),
        "ts": ts,
        "obrien": obrien_data,
        "calumet": calumet_data,
        "stickney_south": stickney_south_data,
        "stickney_north": stickney_north_data,
        "aggregate_plot_name": f"aggregate_rt_plot_{ts}.png",
        "outputs": {},
    }
    cfg_file = write_cfg(cfg)
    run_aggregate_plot(plot_r, cfg, cfg_file)

    return cfg


if __name__ == "__main__":
    import sys

    root_path = "/lcrc/project/EMEWS/bebop-2.0/ncollier/repos/Chicago-WW-Reff"
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], root_path)
