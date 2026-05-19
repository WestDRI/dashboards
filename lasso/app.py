import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.callbacks import Points
from shiny import App, reactive, ui
from shinywidgets import output_widget, render_widget

BOOTSWATCH_CERULEAN = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.8/dist/cerulean/bootstrap.min.css"

npoints = 100
xpos = np.random.rand(npoints)
ypos = np.random.rand(npoints)


def make_scatter_widget(on_selection):
    fig = px.scatter(
        x=xpos,
        y=ypos,
        range_x=[0, 1],
        range_y=[0, 1],
        width=600,
        height=600,
    )
    fig.update_traces(marker=dict(size=30, opacity=0.8))
    fig.update_layout(dragmode="lasso")

    widget = go.FigureWidget(fig)
    widget.data[0].on_selection(on_selection)
    return widget


def make_histogram(values, title):
    fig = px.histogram(x=values, nbins=10, width=400, height=280)
    fig.update_traces(xbins=dict(start=0, end=1, size=0.1))
    fig.update_xaxes(title_text=title, range=[0, 1])
    return fig


app_ui = ui.page_fluid(
    ui.tags.h2(
        "Lasso selection with connected outputs",
        class_="text-primary text-center fs-3 my-3",
    ),
    ui.div(
        ui.div(output_widget("g1"), class_="col-auto"),
        ui.div(
            output_widget("g2"),
            output_widget("g3"),
            class_="col-auto",
        ),
        class_="row justify-content-center g-3",
    ),
    title="Lasso selection",
    theme=BOOTSWATCH_CERULEAN,
)


def server(input, output, session):
    selection = reactive.value(None)

    def on_point_selection(trace, points: Points, state):
        selection.set(points)

    @render_widget
    def g1():
        return make_scatter_widget(on_point_selection)

    @render_widget
    def g2():
        selected = selection.get()
        if selected is None or not selected.point_inds:
            values = []
            title = "Select points to see details"
        else:
            values = list(selected.xs)
            title = "x-distribution"
        return make_histogram(values, title)

    @render_widget
    def g3():
        selected = selection.get()
        if selected is None or not selected.point_inds:
            values = []
            title = "Select points to see details"
        else:
            values = list(selected.ys)
            title = "y-distribution"
        return make_histogram(values, title)


app = App(app_ui, server)
