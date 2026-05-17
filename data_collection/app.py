from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re

import plotly.graph_objects as go
import polars as pl
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget

DATA_PATH = Path(__file__).with_name("course_interest.parquet")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REQUEST_SCHEMA = {
    "submitted_at": pl.Utf8,
    "email": pl.Utf8,
    "course": pl.Utf8,
}

APP_CSS = """
:root {
    color-scheme: light;
    --page-bg: #f4f7fb;
    --panel-bg: #ffffff;
    --panel-border: #cfd8e3;
    --accent: #1f5a91;
    --accent-soft: #e8f1fb;
    --text: #17324d;
    --muted: #5a7188;
}

body {
    background: var(--page-bg);
    color: var(--text);
    font-family: Inter, Arial, Helvetica, sans-serif;
}

.app-shell {
    max-width: 1280px;
    margin: 0 auto;
    padding: 1.5rem;
}

.header-panel,
.panel {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 14px;
    box-shadow: 0 10px 24px rgba(20, 43, 66, 0.06);
}

.header-panel {
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.25rem;
}

.eyebrow {
    color: var(--accent);
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

.header-title {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
}

.header-copy {
    margin: 0.55rem 0 0;
    max-width: 54rem;
    color: var(--muted);
    line-height: 1.55;
}

.layout-grid {
    display: grid;
    gap: 1.25rem;
    grid-template-columns: minmax(320px, 380px) minmax(0, 1fr);
}

.panel {
    padding: 1.25rem;
}

.panel-title {
    margin: 0 0 0.2rem;
    font-size: 1.2rem;
    font-weight: 700;
}

.panel-subtitle {
    margin: 0 0 1rem;
    color: var(--muted);
    font-size: 0.95rem;
}

.form-group {
    margin-bottom: 1rem;
}

.form-control,
.btn,
.shiny-input-container textarea {
    border-radius: 10px;
}

.btn-primary {
    background: var(--accent);
    border-color: var(--accent);
}

.btn-outline-secondary {
    color: var(--accent);
    border-color: #a7bdd3;
}

.button-row {
    display: grid;
    gap: 0.75rem;
    margin-top: 1rem;
}

.status-box {
    margin-top: 1rem;
    padding: 0.85rem 0.95rem;
    border-radius: 10px;
    background: var(--accent-soft);
    border: 1px solid #d3e1f1;
    font-size: 0.93rem;
    color: var(--text);
}

.analytics-grid {
    display: grid;
    gap: 1rem;
    grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
    align-items: start;
}

.stats-grid {
    display: grid;
    gap: 0.85rem;
}

.metric-card-grid {
    display: grid;
    gap: 0.85rem;
}

.stat-card,
.recent-card {
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    background: #fbfdff;
    padding: 0.95rem;
}

.stat-label {
    display: block;
    color: var(--muted);
    font-size: 0.78rem;
    letter-spacing: 0.05rem;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}

.stat-value {
    font-size: 1.rem;
    font-weight: 700;
}

.recent-list {
    display: grid;
    gap: 0.75rem;
    margin-top: 0.9rem;
}

.recent-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
}

.recent-meta {
    margin-top: 0.3rem;
    color: var(--muted);
    font-size: 0.88rem;
}

.empty-box {
    border: 1px dashed #b9c8d8;
    border-radius: 12px;
    padding: 1rem;
    color: var(--muted);
    background: #fbfdff;
}

@media (max-width: 980px) {
    .layout-grid,
    .analytics-grid {
        grid-template-columns: 1fr;
    }
}
"""


def empty_requests() -> pl.DataFrame:
    return pl.DataFrame(schema=REQUEST_SCHEMA)


def normalize_course_name(course: str) -> str:
    return " ".join(course.split())


def normalize_email(email: str) -> str:
    return email.strip().lower()


def load_requests(path: Path = DATA_PATH) -> pl.DataFrame:
    if not path.exists():
        return empty_requests()
    return pl.read_parquet(path).select(list(REQUEST_SCHEMA))


def write_requests(df: pl.DataFrame, path: Path = DATA_PATH) -> None:
    df.write_parquet(path)


def append_request(email: str, course: str, path: Path = DATA_PATH) -> pl.DataFrame:
    current = load_requests(path)
    submission = pl.DataFrame(
        [
            {
                "submitted_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "email": normalize_email(email),
                "course": normalize_course_name(course),
            }
        ],
        schema=REQUEST_SCHEMA,
    )
    updated = pl.concat([current, submission], how="vertical_relaxed")
    write_requests(updated, path)
    return updated


def validate_submission(email: str, course: str) -> str | None:
    normalized_email = normalize_email(email)
    normalized_course = normalize_course_name(course)
    if not normalized_email:
        return "Please enter an email address."
    if not EMAIL_PATTERN.match(normalized_email):
        return "Please enter a valid email address."
    if not normalized_course:
        return "Please enter the course you would like us to build."
    return None


def summary_metrics(df: pl.DataFrame) -> dict[str, str]:
    if df.height == 0:
        return {
            "total_requests": "0",
            "unique_emails": "0",
            "top_course": "No submissions",
        }

    top_course = (
        df.group_by("course")
        .len()
        .sort(["len", "course"], descending=[True, False])
        .row(0, named=True)["course"]
    )
    unique_emails = df["email"].n_unique()
    return {
        "total_requests": str(df.height),
        "unique_emails": str(unique_emails),
        "top_course": top_course,
    }


def make_course_figure(df: pl.DataFrame) -> go.Figure:
    fig = go.Figure()

    if df.height == 0:
        fig.add_annotation(
            text="No topic requests recorded yet",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#5a7188"),
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        counts = (
            df.group_by("course")
            .len()
            .sort(["len", "course"], descending=[True, False])
            .head(8)
        )
        fig.add_trace(
            go.Bar(
                x=counts["len"].to_list(),
                y=counts["course"].to_list(),
                orientation="h",
                marker=dict(color="#2f6da3", line=dict(color="#214d74", width=1)),
                hovertemplate="%{y}: %{x} request(s)<extra></extra>",
            )
        )
        fig.update_yaxes(
            autorange="reversed",
            automargin=True,
            ticklabelstandoff=14,
        )
        fig.update_xaxes(title="Number of requests", dtick=1, gridcolor="#d8e2ee")

    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=40, r=20, t=40, b=20),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        title_font=dict(size=20, color="#17324d"),
        font=dict(color="#17324d"),
    )
    return fig


app_ui = ui.page_fillable(
    ui.tags.head(ui.tags.style(APP_CSS)),
    ui.div(
        ui.div(
            ui.div("Research computing course planning", class_="eyebrow"),
            ui.h1("Topics requests", class_="header-title"),
            ui.p(
                ui.HTML("""
                   Please make sure to look for courses in <a href="https://explora.alliancecan.ca/" target="_blank">Explora</a> before submitting a request.<br>Note that we can't promise that we will satisfy all requests!
                """),
                class_="header-copy",
            ),
            class_="header-panel",
        ),
        ui.div(
            ui.div(
                ui.h2("Submit request", class_="panel-title"),
                ui.p(
                    "Give us a suggestion of a topic you would like us to cover.",
                    class_="panel-subtitle",
                ),
                ui.input_text(
                    "email",
                    "Canadian academic email address",
                    placeholder="your.name@uni.ca",
                ),
                ui.input_text(
                    "course",
                    "Desired topic",
                    placeholder="Applied time series analysis in Julia",
                ),
                ui.div(
                    ui.input_action_button(
                        "save_request",
                        "Save request",
                        class_="btn btn-primary",
                    ),
                    class_="button-row",
                ),
                class_="panel",
            ),
            ui.div(
                ui.h2("Requested topics", class_="panel-title"),
                ui.div(
                    ui.div(output_widget("course_plot")),
                    ui.div(
                        ui.output_ui("metric_cards"),
                        ui.output_ui("recent_requests"),
                        class_="stats-grid",
                    ),
                    class_="analytics-grid",
                ),
                class_="panel",
            ),
            class_="layout-grid",
        ),
        class_="app-shell",
    ),
    title="Topics requests",
)


def server(input, output, session):
    requests_df = reactive.value(load_requests())

    @reactive.effect
    @reactive.event(input.save_request)
    def _save_request():
        email = input.email()
        course = input.course()
        error = validate_submission(email, course)
        if error is not None:
            ui.notification_show(error, type="warning", duration=4)
            return

        updated = append_request(email=email, course=course)
        requests_df.set(updated)
        ui.update_text("email", value="")
        ui.update_text("course", value="")
        ui.notification_show(
            f"Saved request for {normalize_course_name(course)}.",
            type="message",
            duration=3,
        )

    @render_widget
    def course_plot():
        return make_course_figure(requests_df.get())

    @render.ui
    def metric_cards():
        metrics = summary_metrics(requests_df.get())
        return ui.div(
            ui.div(
                ui.span("Total requests", class_="stat-label"),
                ui.div(metrics["total_requests"], class_="stat-value"),
                class_="stat-card",
            ),
            ui.div(
                ui.span("Unique email addresses", class_="stat-label"),
                ui.div(metrics["unique_emails"], class_="stat-value"),
                class_="stat-card",
            ),
            ui.div(
                ui.span("Most requested topic", class_="stat-label"),
                ui.div(metrics["top_course"], class_="stat-value"),
                class_="stat-card",
            ),
            class_="metric-card-grid",
        )

    @render.ui
    def recent_requests():
        df = requests_df.get()
        if df.height == 0:
            return ui.div(
                "The most recent submission will appear here after the first request is submitted.",
                class_="empty-box",
            )

        row = df.tail(1).row(0, named=True)
        return ui.div(
            ui.div(
                ui.span("Most recent request", class_="stat-label"),
                ui.div(row["course"], class_="stat-value"),
                ui.div(
                    row["submitted_at"],
                    class_="recent-meta",
                ),
                class_="stat-card",
            ),
        )


app = App(app_ui, server)
