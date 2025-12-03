"""Dash layout helpers for viewer tabs."""
from dash import dcc, html


def build_controls(viewer_id: str, scalar_options, state, slider_disabled, slider_max, axis_label, palette_options):
    """Return control panel stacked above the graph."""
    return html.Div([
        html.Div([
            html.Div([
                html.Label("Scalar Field:", className='field-label'),
                dcc.Dropdown(
                    id=component_id(viewer_id, 'scalar'),
                    options=scalar_options,
                    value=state.scalar_key,
                    clearable=False,
                    className='full-width'
                )
            ], className='field-block half-width'),
            html.Div([
                html.Label("Color Map:", className='field-label'),
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
            html.Label("Range:", className='field-label'),
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
                html.Button('Select Range', id=component_id(viewer_id, 'rangeButton'), className='secondary-btn'),
                html.Button(
                    [
                        html.Span("↻", className='reset-icon'),
                        "Reset Range"
                    ],
                    id=component_id(viewer_id, 'reset'),
                    className='primary-btn reset-btn'
                )
            ], className='range-row')
        ], className='field-block'),
        slice_controls(viewer_id, axis_label, slider_disabled, slider_max, state.slice_index),
    ], className='control-panel panel-card')


def build_graph_section(viewer_id: str):
    """Graph container."""
    return html.Div([
        html.Div([
            html.Div(id=component_id(viewer_id, 'mapTitle'), className='map-title'),
            dcc.Graph(
                id=component_id(viewer_id, 'graph'),
                className='heatmap-graph',
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'responsive': False,
                    'toImageButtonOptions': {'scale': 4}
                },
                style={'width': '500px', 'height': '400px'}
            ),
            html.Div(id=component_id(viewer_id, 'clickInfo'), style={'display': 'none'})
        ], className='graph-card')
    ], className='graph-wrapper')


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
