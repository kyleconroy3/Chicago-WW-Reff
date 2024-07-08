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
    cfg['ww_data'] = f'{cfg["root_path"]}/Goldstein/WW_paper-1/data/Obriendata.csv'


def store_output(cfg: Dict):
    gen_quants = os.path.join(cfg['out_dir'], cfg["gen_quants_filename"])
    post_preds = os.path.join(cfg['out_dir'], cfg["post_pred_filename"])
    posterior_df = os.path.join(cfg['out_dir'], cfg["posterior_df_filename"])
    # TODO: write these to data store with AERO


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
    args = ['julia', goldstein_jl, cfg_file]
    # subprocess.run(args, check=True, capture_output=True, text=True)

    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(e.cmd, e.stderr)
        raise ValueError()


def run(n_samples: int, n_chains: int, root_path: PathLike, n_threads: int):
    os.environ['JULIA_NUM_THREADS'] = str(n_threads)
    goldstein_jl = f'{root_path}/Goldstein/goldstein_dp.jl'
    plot_r = f'{root_path}/Goldstein/plot_rt.R'
    waste_water_r = f'{root_path}/Goldstein/WW_paper-1/src/wastewater_functions.R'

    now = datetime.datetime.now()
    ts = now.strftime('%Y%m%d_%H%M%S')
    cfg = {
        'ts': ts,
        'root_path': root_path,
        'sim': 'real',
        'seed': 1,
        'rt_plot_name': f'rt_plot_{ts}.png',
        'n_samples': n_samples,
        'n_chains': n_chains,
        'n_reps': 10,
        'waste_water_r': waste_water_r,
        'gen_quants_filename': f'generated_quantities_{ts}.csv',
        'post_pred_filename': f'posterior_predictive_{ts}.csv',
        'posterior_df_filename': f'posterior_df_{ts}.csv'
    }

    stage_data(cfg)
    cfg_file = write_cfg(cfg)
    run_goldstein(goldstein_jl, cfg_file)
    store_output(cfg)
    run_rt_plot(plot_r, cfg, cfg_file)


if __name__ == '__main__':
    n_samples = 10
    n_chains = 2

    root_path = '/home/nick/Documents/repos/Chicago-WW-Reff'
    run(n_samples, n_chains, root_path, 8)
