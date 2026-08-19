library('nlme')

rawdata <- read.csv('/home/hereinlies/Documents/GlobusSharing/gmm_data.csv')

model <-lme(sum_entropy_child~study+sum_entropy_parent*age_months_t2*age_diff, 
        random = ~ 1  | name, 
        data = rawdata)
summary(model)

