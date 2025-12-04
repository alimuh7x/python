"""Dash layout helpers for viewer tabs."""
from dash import dcc, html


def build_controls(viewer_id: str, scalar_options, state, slider_disabled, slider_max, axis_label, palette_options):
    """Return control panel stacked above the graph."""
    return html.Div([
        html.Div([
            html.Div([
                html.Label([
                    html.Span("S", className="label-icon"),
                    "Scalar Field:",
                    html.Span("?", className="tooltip-icon", title="Choose the scalar to display")
                ], className='field-label'),
                dcc.Dropdown(
                    id=component_id(viewer_id, 'scalar'),
                    options=scalar_options,
                    value=state.scalar_key,
                    clearable=False,
                    className='full-width'
                )
            ], className='field-block half-width'),
            html.Div([
                html.Label([
                    html.Img(src='/assets/color-scale.png', className="label-img"),
                    "Color Map:",
                    html.Span("?", className="tooltip-icon", title="Pick a color palette")
                ], className='field-label'),
                dcc.Dropdown(
                    id=component_id(viewer_id, 'palette'),
                    options=palette_options,
                    value=state.palette,
                    clearable=False,
                    className='full-width'
                )
            ], className='field-block half-width')
        ], className='row-inline'),
        html.Div([
            html.Label([
                html.Img(src='/assets/bar-chart.png', className="label-img"),
                "Range:",
                html.Span("?", className="tooltip-icon", title="Adjust min/max or click the heatmap to set a range")
            ], className='field-label'),
            html.Div([
                dcc.Input(
                    id=component_id(viewer_id, 'rangeMin'),
                    type='number',
                    value=state.range_min,
                    step=0.001,
                    placeholder='Min'
                ),
                dcc.Input(
                    id=component_id(viewer_id, 'rangeMax'),
                    type='number',
                    value=state.range_max,
                    step=0.001,
                    placeholder='Max'
                ),
                html.Button(
                    ["⟳", " Reset Range"],
                    id=component_id(viewer_id, 'reset'),
                    className='btn btn-danger reset-btn'
                )
            ], className='range-row with-reset')
        ], className='field-block'),
        slice_controls(viewer_id, axis_label, slider_disabled, slider_max, state.slice_index),
    ], className='control-panel panel-card')


def build_graph_section(viewer_id: str):
    """Graph container."""
    return html.Div([
        html.Div([
            html.Div(id=component_id(viewer_id, 'mapTitle'), className='map-title'),
            html.Div([
                html.Button("⤓", title="Download image", className="icon-btn"),
                html.Button("⤢", title="Fit view", className="icon-btn"),
                html.Button("⟲", title="Reset view", className="icon-btn"),
            ], className="graph-actions")
        ], className="graph-topbar"),
        dcc.Graph(
            id=component_id(viewer_id, 'graph'),
            className='heatmap-graph',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'responsive': False,
                'toImageButtonOptions': {'scale': 4}
            }
        ),
        html.Div(id=component_id(viewer_id, 'clickInfo'), className='toast-anchor')
    ], className='graph-card')


def build_tab_layout(viewer_id: str, scalar_options, state, slider_disabled, slider_max, axis_label, palette_options):
    """Return the full layout for a viewer tab."""
    return html.Div([
        html.Div([
            build_controls(viewer_id, scalar_options, state, slider_disabled, slider_max, axis_label, palette_options),
            build_graph_section(viewer_id)
        ], className='stacked-card'),
        dcc.Store(id=component_id(viewer_id, 'state'), data=state.to_dict())
    ], className='viewer-tab')


def component_id(viewer_id: str, suffix: str) -> str:
    """Generate component ids scoped to the viewer."""
    return f"{viewer_id}-{suffix}"


def slice_controls(viewer_id: str, axis_label: str, slider_disabled: bool, slider_max: int, current_slice: int):
    container_style = {'display': 'none'} if slider_disabled else {}
    return html.Div([
        html.Label(axis_label, className='field-label'),
        dcc.Slider(
            id=component_id(viewer_id, 'slice'),
            min=0,
            max=slider_max,
            value=current_slice,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": True},
            disabled=slider_disabled
        ),
        dcc.Input(
            id=component_id(viewer_id, 'sliceInput'),
            type='number',
            value=current_slice,
            min=0,
            max=slider_max,
            step=1,
            placeholder='Slice number',
            disabled=slider_disabled
        )
    ], style=container_style, id=component_id(viewer_id, 'sliceContainer'), className='field-block')
