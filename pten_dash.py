import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH
import plotly.express as px
import pandas as pd
import numpy as np
import sys


path = sys.argv[1]
sheet_name = sys.argv[2]

df = pd.read_excel(path, sheet_name=sheet_name)

num_list = [1, 2]

df["dateOfBirth"] = pd.to_datetime(df["dateOfBirth"], format="%Y")

for num in num_list:
    df[f"cancer{num}Year"] = pd.to_datetime(df[f"cancer{num}Year"], format="%Y")

for i in list(df.index.values):

    for num in num_list:

        canc = df.at[i, f"cancer{num}"]

        if canc == "Thyroid":

            dob = df.at[i, "dateOfBirth"]
            doc = df.at[i, f"cancer{num}Year"]
            delta = doc - dob

            df.at[i, "yearsToPrimary"] = int(delta.days / 365)

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            children=[
                html.Button("Add Chart", id="add-chart", n_clicks=0),
            ]
        ),
        html.Div(id="container", children=[]),
    ]
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
                    {"label": x, "value": x} for x in np.sort(df["userID"].unique())
                ],
                multi=False,
                value=58,
                placeholder="Patient ID",
            ),
            dcc.Dropdown(
                id={"type": "feature-col", "index": n_clicks},
                options=[{"label": x, "value": x} for x in list(df.columns)],
                placeholder="Feature",
                value="gender",
                clearable=True,
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

    dff = df.set_index("userID")

    dff[feature_col] = dff[feature_col].fillna("NS")

    dff.at[patient_id, "yearsToPrimary"]

    fig = px.histogram(
        dff,
        x="yearsToPrimary",
        color=feature_col,
        marginal="rug",
    )

    fig.add_vline(x=dff.at[patient_id, "yearsToPrimary"])

    fig.update_layout(
        title={
            "text": f"yearsToPrimary vs. {feature_col} (Patient ID: {patient_id})",
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    return fig


if __name__ == "__main__":

    app.run_server(debug=True)