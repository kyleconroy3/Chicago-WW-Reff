#| output: false
library(tidyverse)
library(tidybayes)
library(posterior)
library(fs)
library(GGally)
library(gridExtra)
library(cowplot)
library(scales)
library(dplyr)
library(yaml)


run <- function(cfg) {
  source(cfg$waste_water_r)
  sim = cfg$sim
  seed = cfg$seed
  
  # a hack for dealing with re-using scenario 1 data
  repeat_scenario1s = c(3,4,5,6,7,8,9,10, 12, "frw")
  repeat_scenario41s = c(411, 4111)
  
  if (sim %in% repeat_scenario1s) {
    scenario_sim = 1
  } else if (sim %in% repeat_scenario41s) {
    scenario_sim = 41
  } else {
    scenario_sim = sim
  }
  
  ## load posterior samples, calculate mcmc diagnostics
  gq_file<- paste0(cfg$out_dir, "/", cfg$gen_quants_filename)
  posterior_samples <- read_csv(gq_file) %>%
    rename(.iteration = iteration,
           .chain = chain) %>%
    as_draws()
  subset_samples <- subset_draws(posterior_samples)
  mcmc_summary <- summarise_draws(subset_samples)
  
  # This code creates two dataframes: one with the mcmc samples for 
  # non-time-varying parameters, the other quantiles of the time-varying parameters.

  posterior_gq_samples_all <- subset_samples  %>%
    pivot_longer(-c(.iteration, .chain)) %>%
    dplyr::select(name, value)
  posterior_fixed_samples <- make_fixed_posterior_samples(posterior_gq_samples_all)
  posterior_timevarying_quantiles <- make_timevarying_posterior_quantiles(posterior_gq_samples_all)
  
  #  Create quantiles for the posterior predictive for each day there was observed data
  post_pred_file <-  paste0(cfg$out_dir, "/", cfg$post_pred_filename)
  eirr_post_pred <- read_csv(post_pred_file)
  
  real_data <- read_csv(cfg$ww_data)
  
  if (sim == 3) {
    ten_sim_val = TRUE
  } else {
    ten_sim_val = FALSE
  }
  
  if (sim == 4) {
    three_mean_val = TRUE
  } else {
    three_mean_val = FALSE
  }
  
  eirr_post_pred_intervals <- make_post_pred_intervals(eirr_post_pred, real_data, ten_sim = ten_sim_val, three_mean = three_mean_val)
  
  # Once the time-varying quantiles have been created, we can visualize them. In this vignette,
  # we visualize the quantiles of Rt
  # generate crosswalk between model time and actual date
  
  real_data$epi_week[real_data$year == 2023] <- real_data$epi_week[real_data$year == 2023] + 52
  real_data$epi_week[real_data$year == 2024] <- real_data$epi_week[real_data$year == 2024] + 104
  date_week_crosswalk <- real_data %>% 
    dplyr::select(date, epi_week, new_time) %>%
    mutate(time = epi_week - 7)
  
  # then we filter the time-varying quantiles dataframe for the Rt quantiles and visualize
  rt_quantiles_eirr <- posterior_timevarying_quantiles %>%
    filter(name == "rt_t_values") %>%
    left_join(date_week_crosswalk, by = "time") %>%
    dplyr::select(time, date, epi_week, value, .lower, .upper, .width,.point, .interval) 
  
  my_theme <- list(
    scale_fill_brewer(name = "Credible Interval Width",
                      labels = ~percent(as.numeric(.))),
    guides(fill = guide_legend(reverse = TRUE)),
    theme_bw(),
    theme(legend.position = "bottom"))
  
  
  eirrc_realdata_rt_plot_seed1 <- rt_quantiles_eirr %>%
    ggplot(aes(date, value, ymin = .lower, ymax = .upper)) +
    geom_lineribbon() +
    scale_y_continuous("Rt", label = comma, breaks = seq(0.6, 1.4, by = 0.2), limits = c(0.6,1.4)) +
    scale_x_date(name = "Date", date_breaks = "month") +
    ggtitle("EIRR-ww Posterior Rt") +
    my_theme + 
    geom_hline(yintercept = 1, linetype = "solid", color = "black", lwd=1) +  # Add horizontal line 
    theme(axis.text.x = element_text(angle = 90),
          legend.position = c(0.1, 0.2),
          text = element_text(size = 10),
          legend.background = element_blank())
  
  
  eirrc_realdata_rt_plot_seed1
  png_file = paste0(cfg$out_dir, "/", cfg$rt_plot_name)
  ggsave(png_file, plot = eirrc_realdata_rt_plot_seed1, width = 15, height = 6)
}



args <- commandArgs(trailingOnly = TRUE)
cfg_file <- args[1]
cfg <- yaml.load_file(cfg_file)

run(cfg)
