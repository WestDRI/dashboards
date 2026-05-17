from pathlib import Path
from functools import lru_cache

from netCDF4 import Dataset
import plotly.graph_objects as go
from shiny import App, reactive, ui
from shinywidgets import output_widget, render_widget
from skimage import measure

SLIDER_MIN = 0.05
SLIDER_MAX = 1.95
SLIDER_STEP = 0.05
DEFAULT_LEVEL = 0.5


def load_density() -> object:
    data_path = Path(__file__).with_name("sineEnvelope.nc")
    with Dataset(data_path, "r", format="NETCDF4") as root_group:
        return root_group.variables["density"][:]


RHO = load_density()


def level_key(level: float) -> int:
    return int(round(level / SLIDER_STEP))


@lru_cache(maxsize=16)
def make_figure_for_level(level_value: float) -> go.Figure:
    vertices, triangles, _, _ = measure.marching_cubes(RHO, level_value)
    return go.Figure(
        data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=triangles[:, 0],
                j=triangles[:, 1],
                k=triangles[:, 2],
                intensity=vertices[:, 2],
                colorscale="Viridis",
                showscale=True,
            )
        ],
        layout=dict(
            height=800,
            uirevision="keep-camera",
            scene=dict(aspectmode="data", uirevision="keep-camera"),
            margin=dict(l=0, r=0, t=0, b=0),
        ),
    )


def make_figure(level: float) -> go.Figure:
    level_value = level_key(level) * SLIDER_STEP
    level_value = min(max(level_value, SLIDER_MIN), SLIDER_MAX)
    fig = make_figure_for_level(level_value)
    return go.Figure(fig)


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider(
            "level",
            "Isovalue",
            min=SLIDER_MIN,
            max=SLIDER_MAX,
            value=DEFAULT_LEVEL,
            step=SLIDER_STEP,
            ticks=True,
            width="100%",
        ),
        width=220,
        title="Controls",
    ),
    ui.tags.style(
        """
        .bslib-sidebar-layout {
            height: 100vh;
        }
        """
    ),
    ui.div(
        ui.div("Isosurface", class_="text-primary text-center fs-3 mb-2"),
        output_widget("g1"),
        class_="p-2 h-100",
    ),
    fillable=True,
    title="Isosurface",
    window_title="Isosurface",
)


def server(input, output, session):
    fig = go.FigureWidget(make_figure(DEFAULT_LEVEL))

    @render_widget
    def g1():
        return fig

    @reactive.effect
    def _update_figure():
        source = make_figure(input.level())
        mesh = source.data[0]

        with fig.batch_update():
            fig.data[0].x = mesh.x
            fig.data[0].y = mesh.y
            fig.data[0].z = mesh.z
            fig.data[0].i = mesh.i
            fig.data[0].j = mesh.j
            fig.data[0].k = mesh.k
            fig.data[0].intensity = mesh.intensity


app = App(app_ui, server)
