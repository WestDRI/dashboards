import plotly.express as px
import numpy as np
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.CERULEAN]
app = Dash(__name__, external_stylesheets=external_stylesheets)
npoints = 100
xpos = np.random.rand(npoints)
ypos = np.random.rand(npoints)
fig1 = px.scatter(x=xpos, y=ypos, range_x=[0, 1], range_y=[0, 1], width=600, height=600)
fig1.update_traces(marker=dict(size=30, opacity=0.8))
fig1.update_layout(dragmode="lasso")
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.Div(
                    "Lasso selection with connected outputs",
                    className="text-primary text-center fs-3",
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col([dcc.Graph(figure=fig1, id="g1")], width="auto"),
                dbc.Col(
                    [
                        dcc.Graph(figure={}, id="g2"),
                        dcc.Graph(figure={}, id="g3"),
                    ],
                    width="auto",
                ),
            ],
            justify="center",
        ),  # centre both columns in the row
    ],
    fluid=True,
)


@callback(
    Output(component_id="g2", component_property="figure"),
    Output(component_id="g3", component_property="figure"),
    Input("g1", "selectedData"),
)
def update_graph(selectedPoints):
    print("running the callback function for", selectedPoints)
    if selectedPoints is None:
        xsel, ysel = [], []
        xtitle = "Select points to see details"
        ytitle = xtitle
    else:
        xsel = [p["x"] for p in selectedPoints["points"]]  # x of selected points
        ysel = [p["y"] for p in selectedPoints["points"]]  # y of selected points
        xtitle, ytitle = "x-distribution", "y-distribution"
    fig2 = px.histogram(x=xsel, nbins=10, width=400, height=280)
    fig2.update_traces(xbins=dict(start=0, end=1, size=0.1))  # fixed number of bins
    fig2.update_xaxes(title_text=xtitle, range=[0, 1])  # fixed x-limits
    fig3 = px.histogram(x=ysel, nbins=10, width=400, height=280)
    fig3.update_traces(xbins=dict(start=0, end=1, size=0.1))  # fixed number of bins
    fig3.update_xaxes(title_text=ytitle, range=[0, 1])  # fixed x-limits
    return fig2, fig3


app.run(debug=True)
