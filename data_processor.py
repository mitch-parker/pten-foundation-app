import pandas as pd
from datetime import datetime

def fetch_data(path, sheet_name):

    df = pd.read_excel(path, sheet_name=sheet_name)

    num_list = [1, 2]

    df = df.dropna(subset=["dateOfBirth"])

    df["dateOfBirth"] = pd.to_datetime(df["dateOfBirth"], format="%Y")

    for num in num_list:
        col = f"cancer{num}Year"
        df[col] = pd.to_datetime(df[col], format="%Y")
        df = df.dropna(subset=[col])

    index_list = list()

    for index in list(df.index.values):

        for num in num_list:

            if index not in index_list:

                canc = df.at[index, f"cancer{num}"]

                if canc == "Thyroid":

                    dob = df.at[index, "dateOfBirth"]
                    doc = df.at[index, f"cancer{num}Year"]
                    delta_canc = doc - dob

                    delta_age = datetime.now() - dob

                    df.at[index, "yearsToPrimary"] = int(delta_canc.days / 365)
                    df.at[index, "age"] = int(delta_age.days / 365)

                    index_list.append(index)

    df = df.loc[index_list, :]

    df = df.reset_index(drop=True)

    df["patientID"] = df.index

    return df