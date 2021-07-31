import pandas as pd
from datetime import datetime

from dateutil.relativedelta import relativedelta

def fetch_data(path, sheet_name):

    df = pd.read_excel(path, sheet_name=sheet_name)
    
    numeric_cols = ['patientWeight', 'patientHeight', 'geneticTestYear', 'diagnosedByDR', "alcohol", "pregnancies", "numberOfCancers", "cancer1Year", "cancer2Year", "cancer3Year", "durationCytomel"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df.dropna(subset=["dateOfBirth"]) # we cannot work with patients whose DOB is unknown

    df = compute_years_to_primary(df)
    has_thyroid_cancer_mask = df.apply(lambda row: any(["thyroid" in row[col].lower() if not pd.isna(row[col]) else False for col in ['cancer1', 'cancer2', 'cancer3']]), axis=1)
    only_thyroid_cancer_patients = df[has_thyroid_cancer_mask]

    return only_thyroid_cancer_patients


def compute_years_to_primary1(df):
    df["dateOfBirth"] = pd.to_datetime(df["dateOfBirth"], format="%Y")

    num_list = [1, 2]

    for num in num_list:
        col = f"cancer{num}Year"
        df[col] = pd.to_datetime(df[col], format="%Y")
        df = df.dropna(subset=[col])

    index_list = list()

    for index in list(df.index.values):

        for num in num_list:

            if index not in index_list:

                canc = df.at[index, f"cancer{num}"]

                if "thyroid" in canc.lower():

                    dob = df.at[index, "dateOfBirth"]
                    doc = df.at[index, f"cancer{num}Year"]
                    delta_canc = doc - dob

                    delta_age = datetime.now() - dob

                    df.at[index, "yearsToPrimary"] = int(delta_canc.days / 365)
                    df.at[index, "age"] = int(delta_age.days / 365)

                    index_list.append(index)

    df = df.loc[index_list, :]

    df = df.reset_index(drop=True)

    # df["patientID"] = df.index
    df = df.rename(columns={"PatientID": "patientID"})
    return df


def compute_years_to_primary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the number of years taken for primary cancer
    """

    df['dob'] = pd.to_datetime(df['dateOfBirth'], errors='coerce')
    df['age'] = df.dob.apply(lambda dob: relativedelta(datetime.now(), dob).years)

    def age_from_years(row, event_year_col, dob_col='dob'):
        age = row[event_year_col] - row[dob_col].year
        if age > 0:
            return age

    df['cancer_one_age'] = df.apply(lambda row: age_from_years(row, 'cancer1Year'), axis=1)
    df['cancer_two_age'] = df.apply(lambda row: age_from_years(row, 'cancer2Year'), axis=1)
    df['cancer_three_age'] = df.apply(lambda row: age_from_years(row, 'cancer3Year'), axis=1)

    df['yearsToPrimary'] = df[['cancer_one_age', 'cancer_two_age', 'cancer_three_age']].min(axis=1)

    return df.drop(columns=['dob'])