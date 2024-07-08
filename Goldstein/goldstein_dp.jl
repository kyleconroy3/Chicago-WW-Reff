this_d = dirname(@__FILE__)

using Pkg
Pkg.activate(this_d * "/WW_paper-1/")
Pkg.update()
Pkg.resolve()


using Revise
using JLD2
using FileIO
using CSV
using DataFrames
using Turing
using DifferentialEquations
using LogExpFunctions
using Random
using ForwardDiff
using Optim
using LineSearches
using ww_paper
using Logging
using PreallocationTools

function init_includes(src_dir, seed)
    include(string(src_dir, "/prior_constants_eirr_closed_LAdata", "_seed", seed, ".jl")) ##Using the same constants as used in the paper
    include(string(src_dir, "/newnew_closed_soln_eirr_withincid.jl"))
    ## Load Model
    include(string(src_dir, "/new_bayes_eirrc_closed.jl"))
end


function run(cfg)
    # if sim == "real"
    dat = CSV.read(cfg["ww_data"], DataFrame)
    dat = filter(:year_day => year_day -> year_day < 423, dat)
    ## Define Priors
    
    
    subset_dat = dat[:, [:new_time, :log_gene_copies]]
    long_dat = DataFrames.stack(subset_dat, [:log_gene_copies])
    long_dat = filter(:value => value -> value > 0, long_dat)
    data_log_copies = long_dat[:, :value]
    grid_size = 1.0
     # end 

    obstimes = long_dat[:, :new_time]
    obstimes = convert(Vector{Float64}, obstimes)

    # pick the change times 
    if maximum(obstimes) % 7 == 0
    param_change_max = maximum(obstimes) - 7
    else 
    param_change_max = maximum(obstimes)
    end 
    param_change_times = collect(7:7.0:param_change_max)
    full_time_series = collect(minimum(obstimes):grid_size:maximum(obstimes))
    outs_tmp = dualcache(zeros(6,length(full_time_series)), 10)

    index = zeros(length(obstimes))
    for i in 1:length(index)
        time = obstimes[i]
        index[i] = indexin(round(Int64,time), full_time_series)[1]
    end 

    my_model = new_bayes_eirrc_closed!(
        outs_tmp, 
        data_log_copies,
        obstimes, 
        param_change_times,
        grid_size,
        index)
    
    seed = cfg["seed"]
    Random.seed!(seed)
    # TODO 10 as default arg, use n_reps in cfg.
    n_reps = cfg["n_reps"]
    MAP_init = optimize_many_MAP(my_model, n_reps, 1, true)[1]

    n_chains = cfg["n_chains"]
    Random.seed!(seed)
    MAP_noise = vcat(randn(length(MAP_init) - 1, n_chains), transpose(zeros(n_chains)))
    MAP_noise = [MAP_noise[:,i] for i in 1:size(MAP_noise,2)]

    init = repeat([MAP_init], n_chains) .+ 0.05 * MAP_noise

    Random.seed!(seed)
    n_samples = cfg["n_samples"]
    posterior_samples = sample(my_model, NUTS(), MCMCThreads(), n_samples, n_chains, discard_initial = n_samples,
                               init_params = init)
                               missing_log_copies = repeat([missing], length(data_log_copies))
  
    my_model_forecast_missing = new_bayes_eirrc_closed!(
        outs_tmp, 
        missing_log_copies,
        obstimes,
        param_change_times,
        grid_size,
        index)
                               
    # sometimes there are NAs in the final posterior, this removes those samples
    indices_to_keep = .!isnothing.(generated_quantities(my_model, posterior_samples));
    posterior_samples_randn = ChainsCustomIndex(posterior_samples, indices_to_keep);
    
    # posterior predictive output
    Random.seed!(seed)
    predictive_randn = predict(my_model_forecast_missing, posterior_samples_randn)
    
    # properly scaled posterior output
    Random.seed!(seed)
    gq_randn = get_gq_chains(my_model, posterior_samples_randn);

    out_dir = cfg["out_dir"]

    CSV.write(string(out_dir, "/", cfg["gen_quants_filename"]), DataFrame(gq_randn))
    CSV.write(string(out_dir, "/", cfg["post_pred_filename"]), DataFrame(predictive_randn))
    CSV.write(string(out_dir, "/", cfg["posterior_df_filename"]), DataFrame(posterior_samples))
end

Pkg.add("YAML")
using YAML

cfg_file = ARGS[1]
cfg = YAML.load_file(cfg_file)


init_includes(string(this_d, "/WW_paper-1/src"), cfg["seed"])
run(cfg)



