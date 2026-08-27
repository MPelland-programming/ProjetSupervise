library('nlme')

rawdata <- read.csv('/home/hereinlies/Documents/GlobusSharing/new_model.csv')

rawdata$study <- factor(rawdata$study)
rawdata$sex_child <- factor(rawdata$sex_child, levels = c('male','female'))

model <-lme(sum_entropy_child~study+sum_entropy_parent+ntokens_parent+ntokens_child
            +age_months_t2+age_diff+sex_child+age_months_t2:sex_child+sum_entropy_parent:age_diff
            +sum_entropy_parent:ntokens_parent+ntokens_parent:age_diff
            +sum_entropy_parent:ntokens_parent:age_diff,  
        random = ~ 1  | name, 
        data = rawdata, na.action = na.omit)
summary(model)

