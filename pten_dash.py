import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
import sys
from datetime import datetime

path = sys.argv[1]
sheet_name = sys.argv[2]

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

app = dash.Dash(__name__)


app.layout = html.Div(
    style={
        "backgroundColor": "grey",
    },
    children=[
        html.H1(
            children="PhenoMap",
            style={"textAlign": "center", "color": "white"},
        ),
        html.Div(
            children="A clinical data exploration tool for PHTS",
            style={"textAlign": "center", "color": "white"},
        ),
        html.Div(
            children=[
                html.Button("Add Chart", id="add-chart", n_clicks=0),
            ]
        ),
        html.Div(id="container", children=[]),
    ],
)


@app.callback(
    Output("container", "children"),
    [Input("add-chart", "n_clicks")],
    [State("container", "children")],
)
def display_graphs(n_clicks, div_children):
    new_child = html.Div(
        style={
            "width": "45%",
            "display": "inline-block",
            "outline": "thin lightgrey solid",
            "padding": 10,
        },
        children=[
            dcc.Graph(id={"type": "dynamic-graph", "index": n_clicks}, figure={}),
            dcc.Dropdown(
                id={"type": "patient-id", "index": n_clicks},
                options=[
                    {"label": x, "value": x} for x in np.sort(df["patientID"].unique())
                ],
                multi=False,
                value=None,
                placeholder="Patient ID",
                style=dict(verticalAlign="top"),
            ),
            dcc.Dropdown(
                id={"type": "feature-col", "index": n_clicks},
                options=[{"label": x, "value": x} for x in list(df.columns)],
                placeholder="Feature",
                value="goiter",
                clearable=True,
                style=dict(verticalAlign="bottom"),
            ),
        ],
    )
    div_children.append(new_child)
    return div_children


@app.callback(
    Output({"type": "dynamic-graph", "index": MATCH}, "figure"),
    [
        Input(
            component_id={"type": "patient-id", "index": MATCH},
            component_property="value",
        ),
        Input(
            component_id={"type": "feature-col", "index": MATCH},
            component_property="value",
        ),
    ],
)
def update_graph(patient_id, feature_col):

    fig = {}

    if feature_col is not None:

        dff = df.set_index("patientID")

        dff = dff.dropna(subset=list([feature_col]))

        labels = list(dff[feature_col].unique())

        remove_list = list()

        if len(labels) > 1:

            data = list()

            for label in labels:

                dfff = dff[dff[feature_col].isin(list([label]))]

                val_list = list(dfff["yearsToPrimary"].to_list())

                if len(val_list) < 2:

                    remove_list.append(label)

                else:
                    data.append(val_list)

            for remove in remove_list:
                labels.remove(remove)

            fig = ff.create_distplot(data, labels, show_hist=False)
            text = f"yearsToPrimary vs. {feature_col}"

            if patient_id is not None:

                age = dff.at[patient_id, "age"]
                fig.add_vline(x=age)
                text += f"(Patient ID: {patient_id} | Age: {age} | Feature: {dff.at[patient_id, feature_col]})"

            fig.update_layout(
                title={
                    "text": text,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                xaxis_title="yearsToPrimary",
                yaxis_title="density",
                legend_title=feature_col,
            )
        else:
            print("No Groups to Compare.")

    return fig


if __name__ == "__main__":

    app.run_server(debug=True)