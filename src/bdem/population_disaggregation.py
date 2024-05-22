


#define bbox

#define countries list
cnt = ["FR", "NL", "PL", "IT", "LU"]

#load 100m budem cells in bbox
#load 1000m population cells in bbox

#index 100m cells

#for each 1000m population cell with non-null population

    #get 100m cells
    #compute total bu_res
    #for each 100m cell
        #assign 100m population as pop*bu_res/tot_bu_res

