import yaml
import os
import datetime
from typing import Dict, Union
import subprocess

PathLike = Union[str, bytes, os.PathLike]


def write_cfg(cfg: Dict):
    # TODO: how to set in production
    out_dir = '/home/nick/Documents/repos/Chicago-WW-Reff/Goldstein/output'
    cfg['out_dir'] = out_dir
    cfg_file = os.path.join(out_dir, f"cfg_{cfg['ts']}.yaml")
    with open(cfg_file, 'w') as f_out:
        yaml.safe_dump(cfg, f_out)
    return cfg_file


def stage_data(cfg: Dict):
    # TODO: AERO to get ww_data
    cfg['ww_data'] = '/home/nick/Documents/repos/Chicago-WW-Reff/Goldstein/WW_paper-1/data/Obriendata.csv'


def run_rt_plot(plot_r: PathLike, cfg, cfg_file: PathLike):
    # Rscript doesn't return error code or raise exception error,
    # so check that the plot is created as expected
    expected_plot = os.path.join(cfg['out_dir'], cfg['rt_plot_name'])
    args = ['Rscript', plot_r, cfg_file]
    res = subprocess.run(args, check=False, capture_output=True, text=True)
    if not os.path.exists(expected_plot):
        raise ValueError(res.stderr)
    # try:
    #     subprocess.run(args, check=True, capture_output=True, text=True)
    # except subprocess.CalledProcessError as e:
    #     return e.cmd, e.output


def run_goldstein(goldstein_jl: PathLike, cfg_file: PathLike):
    # TODO how many threads - export JULIA_NUM_THREADS
    os.environ['JULIA_NUM_THREADS'] = '8'
    # TODO: remove
    os.environ['PATH'] = f"{os.environ['PATH']}:/home/nick/sfw/julia-1.10.4/bin"
    args = ['julia', goldstein_jl, cfg_file]
    subprocess.run(args, check=False, capture_output=True, text=True)

    # try:
    #     subprocess.run(args, check=True, capture_output=True, text=True)
    # except subprocess.CalledProcessError as e:
    #     return e.cmd, e.output


def run(n_samples: int, n_chains: int, goldstein_jl: PathLike, plot_r: PathLike,
        water_water_r: PathLike):
    now = datetime.datetime.now()
    ts = now.strftime('%Y%m%d_%H%M%S')
    cfg = {
        'ts': ts,
        'sim': 'real',
        'seed': 1,
        'rt_plot_name': f'rt_plot_{ts}.png',
        'n_samples': n_samples,
        'n_chains': n_chains,
        'waste_water_r': water_water_r
    }

    stage_data(cfg)
    cfg_file = write_cfg(cfg)
    run_goldstein(goldstein_jl, cfg_file)
    # TODO store the produced csv files with AERO.
    run_rt_plot(plot_r, cfg, cfg_file)


if __name__ == '__main__':
    n_samples = 10
    n_chains = 2
    goldstein_jl = '/home/nick/Documents/repos/Chicago-WW-Reff/Goldstein/goldstein_dp.jl'
    plot_r = '/home/nick/Documents/repos/Chicago-WW-Reff/Goldstein/plot_rt.R'
    waste_water_r = '/home/nick/Documents/repos/Chicago-WW-Reff/Goldstein/WW_paper-1/src/wastewater_functions.R'

    run(n_samples, n_chains, goldstein_jl, plot_r, waste_water_r)
