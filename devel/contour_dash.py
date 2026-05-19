from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from skimage import measure
from netCDF4 import Dataset
from pathlib import Path

filename = "sineEnvelope.nc"
rootgrp = Dataset(filename, "r", format="NETCDF4")
rho = rootgrp.variables["density"][:]
rootgrp.close()

external_stylesheets = [dbc.themes.CERULEAN]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = dbc.Container(
    [
        dbc.Row(
            [html.Div("Isosurface", className="text-primary text-center fs-3")]
        ),  # colour+centring+size
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Slider(
                            id="slider1",
                            min=0.05,
                            max=1.95,
                            step=0.05,
                            value=0.5,
                            vertical=True,
                            marks={i / 10: str(i / 10) for i in range(0, 21, 2)},
                            tooltip={"placement": "left", "always_visible": True},
                        ),
                    ],
                    width=1,
                    align="center",
                    className="ms-4",
                ),  # ms-4 is a left margin of size 4
                dbc.Col([dcc.Graph(figure={}, id="g1")], width="auto"),
            ],
            justify="center",
        ),  # centre both columns in the row
    ],
    fluid=True,
)  # use full screen width, min margin padding


@callback(
    Output(component_id="g1", component_property="figure"),
    Input(component_id="slider1", component_property="value"),
)
def update_graph(selected):
    print("running the callback function for", selected)
    # generate marching cubes
    vertices, triangles, normals, values = measure.marching_cubes(
        rho, selected
    )  # create an isosurface
    print(
        format(vertices.shape[0], ","),
        "vertices and",
        format(triangles.shape[0], ","),
        "triangles",
    )
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=triangles[:, 0],
                j=triangles[:, 1],
                k=triangles[:, 2],
                intensity=vertices[:, 2],  # color by z-height
                colorscale="Viridis",
                showscale=True,
            )
        ]
    )
    fig.update_layout(width=900, height=800, scene=dict(aspectmode="data"))
    return fig


app.run(debug=True)
