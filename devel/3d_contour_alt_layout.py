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
                colorbar=dict(thickness=14),
            )
        ],
        layout=dict(
            height=600,
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
        ui.div(
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
            class_="slider-shell",
        ),
        width=350,
        open="always",
        resizable=False,
        padding="0.2rem 0.5rem 0 0.5rem",
        gap="0",
    ),
    ui.tags.style(
        """
        .bslib-sidebar-layout {
            height: 100vh;
            margin-bottom: 0;
            border: 0 !important;
            box-shadow: none !important;
        }
        .bslib-sidebar-layout > .main,
        .bslib-sidebar-layout > .sidebar,
        .bslib-sidebar-layout .sidebar-content,
        .bslib-page-main {
            border: 0 !important;
            box-shadow: none !important;
        }
        .bslib-sidebar-layout > .collapse-toggle {
            display: none !important;
        }
        .bslib-page-main {
            gap: 0 !important;
            padding: 0.2rem 0.75rem 0.75rem !important;
        }
        .sidebar-content {
            display: flex;
            flex-direction: column;
            height: 100%;
            justify-content: flex-start;
        }
        .slider-shell {
            width: 100%;
            margin-top: auto;
            padding-bottom: 0.5rem;
        }
        .slider-shell .form-group.shiny-input-container {
            width: 100% !important;
            margin: 0;
        }
        .slider-shell .control-label {
            display: block !important;
            margin-bottom: 0.35rem;
            padding-left: 0.2rem;
            text-align: left;
        }
        .slider-shell .irs {
            margin-top: 0;
        }
        .app-title {
            margin-bottom: 0;
            line-height: 1;
            transform: translateY(0.12rem);
        }
        .main-shell {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .figure-shell {
            flex: 1;
            min-height: 0;
            margin-top: 0;
        }
        """
    ),
    ui.div(
        ui.div("Isosurface", class_="app-title text-primary text-center fs-3"),
        ui.div(output_widget("g1"), class_="figure-shell"),
        class_="main-shell",
    ),
    fillable=True,
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
