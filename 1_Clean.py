import sys
import pandas as pd
import numpy as np
import rename                                       

#**********************
# Environment verifier 
#**********************

print(f"    --------------------\n    Environment verifier \n    --------------------")
print("Current Python version:", sys.version)
print(f"Min. required Python version: 3.11.7")

def print_version_comparison(library, version_current, version_req):
    print(f"{'Library':<15}{'Current':<15}{'Min. Required':<15}")
    print(f"{library:<15}{version_current:<15}{version_req:<15}")
if __name__ == "__main__":
    library = "Pandas"
    version_current = pd.__version__
    version_req = "2.1.4"
    print_version_comparison(library, version_current, version_req)


#************************************
#*      PART 1 : Data Cleaning      *      
#************************************


#*************************************************
# Import the data and merge FP and IQPF together * 
#*************************************************

fp_df = pd.read_excel("DataRaw/C_HEC-21-2697 OECE 081121 FP.xlsx", sheet_name="Sheet1", header=0) # Import the raw FP data (804x198)
fp_df['sample'] = 0     # Generate variable to identify FP Canada observations
iqpf_df = pd.read_excel("DataRaw/C_HEC-21-2697 OECE 081121 IQPF.xlsx", sheet_name="Sheet1", header=0)    # Import the raw IQPF data (240x198)
iqpf_df['sample'] = 1 
df_raw = pd.concat([iqpf_df, fp_df], ignore_index=True)     # The Appended data (1044x199)
df = df_raw.copy()

#**********************
#* Creating raw_all *
#**********************
df.to_csv("DataClean/raw_all.csv", index=False)


#****************************************************
#* Use the appended data and rename/label variables *
#****************************************************

# (1) Renaming values to yesnodk    (Easier if we use the initial questionnaire variable names)

to_yesnodk = [
    ('QD_', 1, 3),
    ('Q13_', 1, 3), ('Q13_', 7777777, 7777777), ('Q13_', 8888888, 8888888),
    ('Q14_', 1, 12),
    ('Q15_', 1, 7),
    ('hQ18_', 1, 6),
    ('Q25_', 1, 18),
    ('Q26_', 1, 8),
    ('Q28_', 1, 8),
    ('Q30x1_', 1, 5) ]
for prefix, start, end in to_yesnodk:
    for x in range(start, end + 1):
        column_name = prefix + str(x)
        df[column_name] = df[column_name].astype('category').replace(rename.yesnodk)


to_yesnodk2 = ['Q3', 'Q24a', 'Q24b', 'Q24c', 'Q24d', 'Q29', 'Q31a', 'Q31b', 'Q39']
for var in to_yesnodk2:
    df[var] = df[var].astype('category').replace(rename.yesnodk2)


agreements = [  (('Q22_', 1, 10), rename.agreement),
                (('Q23_', 1, 7), rename.agreement5),
                (('Q30x3_', 1, 5), rename.share), ]
for agreement_set, agreement_type in agreements:
    prefix, start, end = agreement_set
    for x in range(start, end + 1):
        column_name = prefix + str(x)
        df[column_name] = df[column_name].astype('category').replace(agreement_type)


# (2) Renaming variables

for old_name, new_name in rename.rename_list:
    if old_name in df.columns:  # Checks if the column exists in the DataFrame
        df.rename(columns={old_name: new_name}, inplace=True)


# (3) Renaming values (other than yesnodk)
    
for col, labels in rename.value_labels.items():
    if col in df.columns:                   # Check if the variable exists in the DataFrame
        df[col] = df[col].map(labels).astype('category') # or df[col] = df[col].astype('category').cat.rename_categories(labels)


suffixes = ['a', 'b']
var_prefixes = ['name', 'apr', 'mtr', 'solicit', 'answer', 
                'bequest', 'rate', 'health', 'payout', 'comp', 
                'borrow', 
                'mutfees', 'segfees']
for suffix in suffixes:
    for scenario in range(1, 5):
        for var_prefix in var_prefixes:
            var = f"scn{scenario}{suffix}_{var_prefix}"
            value_label_name = f"{var_prefix}{scenario}" 
            if value_label_name in rename.value_labels_scn:  # Check if value_label_name exists
                df[var] = df[var].map(rename.value_labels_scn[value_label_name]).astype('category')
            #print(var)    


####### Bring imputed values from STATA imputation #############################
df_stata = pd.read_stata("DataRaw/clean_all.dta")
df = df.merge(df_stata[['respid', 'income_impute', 'debt_impute']], on='respid', how='left')
#################################################################################

#(4)  Labeling variables

for column, label in rename.variable_labels.items():
    if column in df.columns:  # Check if the column exists in the DataFrame
        df[column].name = label


#***********************
#* Additional varibles *
#***********************

df['time'] = df['timestamp'].str[4:10]
dates_to_remind = ["Oct 29", "Oct 30", "Oct 31", "Nov 1 ", "Nov 2 ", "Nov 3 ", "Nov 4 ", "Nov 5 ", "Nov 6 ", "Nov 8 "]
df['reminder'] = df['time'].isin(dates_to_remind).astype(int)

#**********************
#* Creating clean_all *
#**********************
df.to_csv("DataClean/clean_all.csv", index=False)


#*****************************************
#*      PART 2 : Wide to long format     *      
#*****************************************

#*****************************************************
#* Switch from wide to long data for easier analysis *
#*****************************************************

variables = ['name', 'solicit', 'answer', 'apr', 'mtr', 'bequest', 'rate', 
             'health', 'payout', 'comp', 'borrow', 'mutfees', 'segfees']
dfms = {}      # Dictionary to store the dataframes

# (1) Let's create a df for each melted variable and store them in a dictionary(dfms)
for variable in variables:
    scn_cols = [f'scn1a_{variable}', f'scn1b_{variable}', 
                f'scn2a_{variable}', f'scn2b_{variable}',
                f'scn3a_{variable}', f'scn3b_{variable}', 
                f'scn4a_{variable}', f'scn4b_{variable}']
    scn_cols = [col for col in scn_cols if col in df.columns]  # Check if the current variable exists in any of the scn columns
    dfm = df.melt(id_vars    =  ['respid'], 
                  value_vars =  scn_cols, 
                  var_name   =  'scn', 
                  value_name =  variable)
    dfm['scn'] = dfm['scn'].replace({f'scn1a_{variable}' : '1', f'scn1b_{variable}' : '2',
                                     f'scn2a_{variable}' : '3', f'scn2b_{variable}' : '4',
                                     f'scn3a_{variable}' : '5', f'scn3b_{variable}' : '6',
                                     f'scn4a_{variable}' : '7', f'scn4b_{variable}' : '8' })
    dfms[f'dfm_{variable}'] = dfm   # Assign the dataframe to the dictionary with appropriate key
# print (dfms['dfm_comp'])

# (2) Merge all dataframes stored in dfms
merged_df = None
for key, dfm in dfms.items():
    if merged_df is None:
        merged_df = dfm
    else:
        merged_df = pd.merge(merged_df, dfm, on=['respid', 'scn'], how='outer')
#print(merged_df)

# (3) Merge df with merged_df (8352 obs)
long_df = pd.merge(merged_df, df, on='respid', how='left')
long_df = long_df.sort_values(by=['respid', 'scn'])
#print(long_df)

#****************************
#* Creating clean_all_longv *
#****************************
long_df.to_csv("DataClean/clean_all_longv.csv", index=False)

