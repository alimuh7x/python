"""Dash layout helpers for viewer tabs."""
from dash import dcc, html


def build_controls(viewer_id: str, scalar_options, state, slider_disabled, slider_max, axis_label, palette_options):
    """Return control panel stacked above the graph."""

    return html.Div([
        # Row 1: Scalar Field and Color Map
        html.Div([
            html.Label([
                html.Span("S", className="label-icon"),
                "Scalar Field:",
            ], className='field-label grid-label'),
            html.Div([
                dcc.Dropdown(
                    id=component_id(viewer_id, 'scalar'),
                    options=scalar_options,
                    value=state.scalar_key,
                    clearable=False,
                    searchable=False,
                )
            ], className='dropdown-wrapper'),
            html.Label([
                html.Img(src='/assets/color-scale.png', className="label-img"),
                "Color Map:",
            ], className='field-label grid-label'),
            html.Div([
                dcc.Dropdown(
                    id=component_id(viewer_id, 'palette'),
                    options=palette_options,
                    value=state.palette,
                    clearable=False,
                    searchable=False,
                )
            ], className='dropdown-wrapper')
        ], className='controls-grid-row'),

        # Row 2: Range inputs
        html.Div([
            html.Label([
                html.Img(src='/assets/bar-chart.png', className="label-img"),
                "Range:",
            ], className='field-label grid-label'),
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
                ["⟳", " Reset"],
                id=component_id(viewer_id, 'reset'),
                className='btn btn-danger reset-btn'
            )
        ], className='controls-grid-row range-row-extended'),

        # Row 2b: Slice controls (when visible)
        html.Div([
            html.Label(axis_label, className='field-label grid-label'),
            dcc.Slider(
                id=component_id(viewer_id, 'slice'),
                min=0,
                max=slider_max,
                value=state.slice_index,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
                disabled=slider_disabled,
                className='slice-slider'
            ),
            dcc.Input(
                id=component_id(viewer_id, 'sliceInput'),
                type='number',
                value=state.slice_index,
                min=0,
                max=slider_max,
                step=1,
                placeholder='Slice',
                disabled=slider_disabled,
                className='slice-input'
            )
        ], className='controls-grid-row slice-row-extended', style={'display': 'none' if slider_disabled else 'grid'}, id=component_id(viewer_id, 'sliceContainer')),

        # Row 3: Range slider
        html.Div([
            dcc.RangeSlider(
                id=component_id(viewer_id, 'rangeSlider'),
                min=state.range_min,
                max=state.range_max,
                value=[state.range_min, state.range_max],
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
                className='range-slider-dual',
                allowCross=False
            ),
            # Hidden display elements for callback compatibility
            html.Div([
                html.Span(id=component_id(viewer_id, 'rangeMinDisplay'), style={'display': 'none'}),
                html.Span(id=component_id(viewer_id, 'rangeMaxDisplay'), style={'display': 'none'}),
            ], style={'display': 'none'})
        ], className='range-slider-row'),
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
