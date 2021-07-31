import os

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, MATCH
import plotly.figure_factory as ff
import numpy as np

from data_processor import fetch_data

# path = sys.argv[1] 
# sheet_name = sys.argv[2]

path = "data/PTEN Patients Data.xlsx"
sheet_name = "pos-neg-samples-v4"

df = fetch_data(path, sheet_name)

non_plottable_cols = ["geneticMutationC", "geneticMutationP", "durationCytomel", "geneticTestYear", "alcohol"]
df = df.drop(columns=non_plottable_cols)

# Visualization

# external JavaScript files
external_scripts = [
    {
        'src': 'https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js',
        'integrity': 'sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM',
        'crossorigin': 'anonymous'
    }
]

# external CSS stylesheets
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC',
        'crossorigin': 'anonymous'
    }
]

metas = [
    dict(name="viewport", content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no")
]
app = dash.Dash(__name__, meta_tags=metas, title="PhenoMap - a clinical data explorer for PTEN", external_scripts=external_scripts, external_stylesheets=external_stylesheets)

server = app.server

def create_header():
    return html.Div([
        html.H2("PhenoMap", className="display-2"),
        # TODO: caption looks too small
        html.P('A clinical data explorer for PTEN', className="lead"),
        html.Hr(className="lead col-3 mx-auto")
    ], className="text-center mb-5")

app.layout = html.Div([
    create_header(),

    html.Div(
        children=[
            html.Div([
                html.Label("Patient ID", htmlFor="patient-id", className="col-sm-2 col-form-label"),
                html.Div([
                    dcc.Dropdown(
                        id="patient-id",
                        options=[
                            {"label": x, "value": x} for x in np.sort(df["PatientID"].unique())
                        ],
                        multi=False,
                        value=None,
                        placeholder="Select a patient to see their current disease progression",
                        style=dict(verticalAlign="top"),
                    )
                ], className="col-sm-10")
            ], className="mb-3 row"),
            html.Div(id="patient-card", children=[]),
        ]
    ),
    html.Div(id="container", children=[], className="row"),
    html.Hr(),
    html.Button("Add Chart", id="add-chart", n_clicks=0, className="my-5"),
], className="container", style={"fontSize": "14px"})

@app.callback(
    Output("patient-card", "children"),
    [Input("patient-id", "value")],
    [State("patient-card", "children")],
)
def show_patient_card(patient_id, patient_card_children):
    dff = df.set_index("PatientID")
    patient_card_children = []
    if patient_id is not None:
        patient_card_children = [
            html.Div([
                html.Div([
                    html.Div([
                        html.Img(
                            src="https://t3.ftcdn.net/jpg/01/18/01/98/360_F_118019822_6CKXP6rXmVhDOzbXZlLqEM2ya4HhYzSV.jpg", 
                            className="img-fluid rounded-start", alt=f"{patient_id}'s profile photo")
                    ], className="col-md-4"),
                    html.Div([
                        html.Div([
                            html.H4(f"Patient ID: {patient_id}", className="card-title"),
                            html.Ul([
                                # gender	CountryOFBirth	dateOfBirth	unitOfMeasure	patientHeight	patientWeight
                                html.Li(f"Gender: {dff.at[patient_id, 'gender']}"),
                                html.Li(f"Country of birth: {dff.at[patient_id, 'CountryOFBirth']}"),
                                html.Li(f"Age: {dff.at[patient_id, 'age']}"),
                                html.Li(f"Height: {dff.at[patient_id, 'patientHeight']}"),
                                html.Li(f"Weight: {dff.at[patient_id, 'patientWeight']}")
                            ], className="card-text")
                        ], className="card-body"),
                    ], className="col-md-8"),
                ], className="row g-0")
            ], className="card mb-3 col-lg-6")
        ]
    return patient_card_children

@app.callback(
    Output("container", "children"),
    [Input("add-chart", "n_clicks")],
    [State("container", "children")],
)
def display_graphs(n_clicks, chart_container_children):
    new_chart = html.Div(
        className="col-xl-6 p-4",
        children=[
            dcc.Graph(id={"type": "dynamic-graph", "index": n_clicks}, figure={}),
            dcc.Dropdown(
                id={"type": "feature-col", "index": n_clicks},
                options=[{"label": x, "value": x} for x in sorted(list(df.columns))],
                placeholder="Feature",
                value="goiter",
                clearable=True,
                style=dict(verticalAlign="bottom"),
                className="col-md-6"
            ),
        ],
    )
    chart_container_children.append(new_chart)
    return chart_container_children


@app.callback(
    Output({"type": "dynamic-graph", "index": MATCH}, "figure"),
    [
        Input(
            component_id="patient-id",
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
        dff = df.set_index("PatientID")
        # dff[feature_col] = dff[feature_col].fillna("Not Specified")
        dff = dff.dropna(subset=[feature_col])
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
            text = ""
            if patient_id is not None:
                age = dff.at[patient_id, "age"]
                fig.add_vline(x=age)
                text += f"Patient ID: {patient_id} | {feature_col}: {dff.at[patient_id, feature_col]}"
            
            fig.update_layout(
                title={
                    "text": text,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                },
                xaxis_title="Years to Primary",
                yaxis_title="Fraction of cancer patients",
                legend_title=feature_col,
            )
        
        else:
            print("No Groups to Compare.")
    
    return fig


if __name__ == "__main__":
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    app.run_server(debug=debug_mode)
