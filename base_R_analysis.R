library('nlme')

rawdata <- read.csv('/home/hereinlies/Documents/GlobusSharing/gmm_data.csv')

model <-lme(sum_entropy_child~sum_entropy_parent*age_months_t1*age_diff, 
        random = ~ 1  | study/name, 
        data = rawdata)
summary(model)
