import pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import LabelEncoder

# Load the dataset
data = pd.read_csv('C:/Users/crokh/OneDrive/Documents/Wealth/clean_alls.csv')

# Clean and transform the demographic and financial variables
data['age'] = data['age'].fillna(data['age'].mean())
data['gender'] = (data['gender'] == "Woman").astype(int)
data['french_survey'] = (data['language'] == "French").astype(int)
data['married'] = data['marital_status'].isin(["Married", "Living common-law"]).astype(int)
data['has_children'] = (data['children'] == "yes").astype(int)
data['work_experience'] = data['work_experience'].fillna(data['work_experience'].mean())
data['income_impute'] = data['income_impute'].fillna(data['income_impute'].mean())
data['education_highschool'] = data['educ'].isin([
    "Less than high school diploma or its equivalent",
    "High school diploma or a high school equivalency certificate",
    "Trade certificate or diploma"]).astype(int)
data['education_college'] = data['educ'].isin([
    "College, CEGEP or other non-university certificate or diploma (other than trades certificates or diplomas)",
    "University certificate or diploma below the bachelor's level"]).astype(int)
data['education_bachelor'] = data['educ'].isin([
    "Bachelor's degree (e.g. B.A., B.Sc., LL.B.)",
    "University certificate, diploma, degree above the bachelor's level"]).astype(int)

# Handle the debt variable
data['debt'] = data['debt_impute'].fillna(data['debt_impute'].mean())

# Prepare the scenario variables: MTR and APR
data['MTR_50'] = (data['scn1b_mtr'] == '50%').astype(int)
data['APR_5'] = (data['scn1b_apr'] == '5%').astype(int)
data['APR_7_5'] = (data['scn1b_apr'] == '7.5%').astype(int)

# Prepare independent variables with debt included
X_filtered = data[['MTR_50', 'APR_5', 'APR_7_5', 'age', 'gender', 'french_survey', 'married', 'has_children', 
                   'work_experience', 'income_impute', 'education_highschool', 'education_college', 
                   'education_bachelor', 'debt']]

# Prepare the dependent variable (scn1b_answer or scn1a_answer)
label_encoder = LabelEncoder()
y_filtered = label_encoder.fit_transform(data['scn1b_answer'])  # Adjust based on the scenario

# Print the class mapping (so you can interpret results later)
class_mapping = dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))
print("Class Mapping:", class_mapping)

# Run the multinomial logit model (with robust standard errors)
model_mlogit = sm.MNLogit(y_filtered, X_filtered)
result_mlogit = model_mlogit.fit(cov_type='HC0', maxiter=1000)  # Use sandwich estimator for robust standard errors

# Calculate and print marginal effects (average partial effects)
marginal_effects = result_mlogit.get_margeff()
print(marginal_effects.summary())
