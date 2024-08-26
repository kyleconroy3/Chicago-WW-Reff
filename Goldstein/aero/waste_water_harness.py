import yaml
import os
import datetime
from typing import Dict, Union
from pathlib import Path
import subprocess
from dsaas_client.api import save_output
from dsaas_client.api import get_file


PathLike = Union[str, bytes, os.PathLike]


def write_cfg(cfg: Dict):
    out_dir = cfg['out_dir']
    cfg_file = os.path.join(out_dir, f"cfg_{cfg['ts']}.yaml")
    with open(cfg_file, 'w') as f_out:
        yaml.safe_dump(cfg, f_out)
    return cfg_file


def stage_data(cfg: Dict):
    cfg['ww_data'] = f'{cfg["root_path"]}/Goldstein/WW_paper-1/data/Obriendata.csv'
    # AERO file retrieval
    # data = get_file(cfg['ww_data_source_id'])
    # data.to_csv(cfg['ww_data'], index=False)


def store_output(fname: PathLike, description: str, sources: Dict):
    name = os.path.basename(fname)
    with open(fname, 'rb') as fin:
        data = fin.read()
    collection = "https://g-c952d0.1305de.36fe.data.globus.org/"
    save_output(data=data, collection_url=collection, name=name,
                description=description, sources=sources)


def store_outputs(cfg: Dict):
    sources = {}  # [cfg['ww_data_id']]
    # csv files
    gen_quants = os.path.join(cfg['out_dir'], cfg["gen_quants_filename"])
    store_output(gen_quants, 'Waster water generated quantities', sources)
    post_preds = os.path.join(cfg['out_dir'], cfg["post_pred_filename"])
    store_output(post_preds, 'Waster water posterior predictive', sources)
    posterior_df = os.path.join(cfg['out_dir'], cfg["posterior_df_filename"])
    store_output(posterior_df, 'Waster water posterior samples', sources)


def run_rt_plot(plot_r: PathLike, cfg: Dict, cfg_file: PathLike):
    # Rscript doesn't return error code or raise exception error,
    # so check that the plot is created as expected
    expected_plot = os.path.join(cfg['out_dir'], cfg['rt_plot_name'])
    args = ['Rscript', plot_r, cfg_file]
    res = subprocess.run(args, check=False, capture_output=True, text=True)
    if not os.path.exists(expected_plot):
        raise ValueError(res.stderr)

    # TODO: Uncomment when AERO is working - add source ids for the other outputs??
    sources = {}  # cfg['ww_data_id']
    store_output(expected_plot, 'waster png plot', sources)


def run_goldstein(goldstein_jl: PathLike, cfg_file: PathLike):
    args = ['julia', goldstein_jl, cfg_file]
    # subprocess.run(args, check=True, capture_output=True, text=True)

    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(e.cmd, e.stdout, e.stderr)
        raise ValueError(f'{e.cmd}\n{e.stdout}\n{e.stderr}')


def run(n_samples: int, n_chains: int, n_reps: int, root_path: PathLike, n_threads: int):
    os.environ['JULIA_NUM_THREADS'] = str(n_threads)
    goldstein_jl = str(Path(root_path, 'Goldstein', 'aero', 'goldstein_dp.jl'))
    plot_r = str(Path(root_path, 'Goldstein', 'aero', 'plot_rt.R'))
    waste_water_r = str(Path(root_path, 'Goldstein', 'WW_paper-1', 'src', 'wastewater_functions.R'))

    out_path = Path(root_path, 'Goldstein', 'aero', 'output')
    out_path.mkdir(exist_ok=True)

    now = datetime.datetime.now()
    ts = now.strftime('%Y%m%d_%H%M%S')
    cfg = {
        'ts': ts,
        'root_path': root_path,
        'out_dir': str(out_path),
        'sim': 'real',
        'seed': 1,
        'rt_plot_name': f'rt_plot_{ts}.png',
        'n_samples': n_samples,
        'n_chains': n_chains,
        'n_reps': n_reps,
        'waste_water_r': waste_water_r,
        'gen_quants_filename': f'generated_quantities_{ts}.csv',
        'post_pred_filename': f'posterior_predictive_{ts}.csv',
        'posterior_df_filename': f'posterior_df_{ts}.csv'
    }

    stage_data(cfg)
    cfg_file = write_cfg(cfg)
    run_goldstein(goldstein_jl, cfg_file)
    # TODO: uncomment when AERO is working
    store_outputs(cfg)
    run_rt_plot(plot_r, cfg, cfg_file)
    return cfg


if __name__ == '__main__':
    n_samples = 10
    n_chains = 2

    root_path = '/lcrc/project/EMEWS/bebop-2.0/ncollier/repos/Chicago-WW-Reff'
    run(n_samples, n_chains, 10, root_path, 10)
