"""
VTK 2D Slice Viewer with Two-Color Threshold Visualization
A Dash application for interactive VTK file visualization
"""
import os
import numpy as np
from dash import Dash, html, dcc, Input, Output, State, callback_context
import plotly.graph_objects as go
from utils.vtk_reader import VTKReader


# Initialize Dash app
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "VTK 2D Slice Viewer"

# Global variables to store data
vtk_reader = None
current_data = {}


def initialize_vtk_file(file_path):
    """Initialize VTK file and set default parameters"""
    global vtk_reader, current_data

    vtk_reader = VTKReader(file_path)

    # Get initial slice
    axis = 'y'
    slice_index = None
    if vtk_reader.is_3d:
        slice_index = vtk_reader.dimensions[1] // 2

    x_coords, y_coords, scalars, stats = vtk_reader.get_slice(axis=axis, index=slice_index)

    # Interpolate to grid with high resolution for smooth output
    X_grid, Y_grid, Z_grid = vtk_reader.interpolate_to_grid(x_coords, y_coords, scalars, resolution=500)

    # Calculate initial threshold (midpoint)
    threshold = (stats['min'] + stats['max']) / 2

    # Store current state
    current_data = {
        'X_grid': X_grid,
        'Y_grid': Y_grid,
        'Z_grid': Z_grid,
        'stats': stats,
        'threshold': threshold,
        'colorA': 'blue',
        'colorB': 'red',
        'slice_index': slice_index if vtk_reader.is_3d else 0,
        'axis': axis,
        'clicked_value': None,
        'initial_threshold': threshold,
        'initial_colorA': 'blue',
        'initial_colorB': 'red',
        'current_scalar': vtk_reader.scalar_name,
        'range_min': stats['min'],
        'range_max': stats['max'],
        'click_count': 0,
        'first_click': None
    }

    return current_data


# Initialize with default file
default_file = 'PhaseField_Initial.vts'
if os.path.exists(default_file):
    initialize_vtk_file(default_file)
else:
    # Create placeholder data
    current_data = {
        'X_grid': np.zeros((10, 10)),
        'Y_grid': np.zeros((10, 10)),
        'Z_grid': np.zeros((10, 10)),
        'stats': {'min': 0, 'max': 1, 'mean': 0.5, 'std': 0.1},
        'threshold': 0.5,
        'colorA': 'blue',
        'colorB': 'red',
        'slice_index': 0,
        'axis': 'y',
        'clicked_value': None,
        'initial_threshold': 0.5,
        'initial_colorA': 'blue',
        'initial_colorB': 'red'
    }


# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("VTK 2D Slice Viewer", style={'textAlign': 'center', 'color': '#2c3e50'}),
        html.P(
            "Interactive two-color threshold visualization for VTK files",
            style={'textAlign': 'center', 'color': '#7f8c8d'}
        )
    ], style={'marginBottom': '20px'}),

    # Main container - Controls on LEFT, Figure on RIGHT
    html.Div([
        # LEFT column: Controls
        html.Div([
            html.Div([
                html.H3("Controls", style={'borderBottom': '2px solid #3498db', 'paddingBottom': '10px'}),

                # Scalar field selector
                html.Div([
                    html.Label("Scalar Field:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='scalar-field-dropdown',
                        options=[{'label': name, 'value': name} for name in (vtk_reader.mesh.array_names if vtk_reader else [])],
                        value=current_data.get('current_scalar', 'Interfaces'),
                        style={'marginTop': '5px'},
                        clearable=False
                    )
                ], style={'marginBottom': '20px'}),

                # Hidden inputs for colors and threshold (still needed for callbacks)
                html.Div([
                    dcc.Input(id='color-a-input', type='text', value=current_data['colorA'], style={'display': 'none'}),
                    dcc.Input(id='color-b-input', type='text', value=current_data['colorB'], style={'display': 'none'}),
                    dcc.Input(id='threshold-input', type='number', value=current_data['threshold'], style={'display': 'none'})
                ]),

                # Min and Max value inputs with Rescale button (single row)
                html.Div([
                    html.Label("Range:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                    html.Div([
                        # Min input
                        html.Div([
                            dcc.Input(
                                id='min-input',
                                type='number',
                                value=current_data['range_min'],
                                step=0.001,
                                placeholder='Min',
                                style={'width': '100%', 'padding': '6px', 'fontSize': '12px'}
                            )
                        ], style={'width': '35%', 'display': 'inline-block'}),

                        # Max input
                        html.Div([
                            dcc.Input(
                                id='max-input',
                                type='number',
                                value=current_data['range_max'],
                                step=0.001,
                                placeholder='Max',
                                style={'width': '100%', 'padding': '6px', 'fontSize': '12px'}
                            )
                        ], style={'width': '35%', 'display': 'inline-block', 'marginLeft': '5px'}),

                        # Select Range button
                        html.Div([
                            html.Button(
                                'Select Range on Figure',
                                id='rescale-button',
                                n_clicks=0,
                                style={
                                    'width': '100%',
                                    'padding': '6px',
                                    'backgroundColor': '#3498db',
                                    'color': 'white',
                                    'border': 'none',
                                    'borderRadius': '3px',
                                    'cursor': 'pointer',
                                    'fontSize': '12px',
                                    'fontWeight': 'bold'
                                }
                            )
                        ], style={'width': '25%', 'display': 'inline-block', 'marginLeft': '5px'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], style={'marginBottom': '20px'}),

                # Slice selector (only for 3D data)
                html.Div([
                    html.Label("Slice Index (Y-axis):", style={'fontWeight': 'bold'}),
                    dcc.Slider(
                        id='slice-slider',
                        min=0,
                        max=(vtk_reader.dimensions[1] - 1) if vtk_reader and vtk_reader.is_3d else 0,
                        value=current_data['slice_index'],
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        disabled=not (vtk_reader and vtk_reader.is_3d)
                    )
                ], style={'marginBottom': '20px'}, id='slice-container'),

                # Reset button
                html.Div([
                    html.Button(
                        'Reset to Initial',
                        id='reset-button',
                        n_clicks=0,
                        style={
                            'width': '100%',
                            'padding': '12px',
                            'backgroundColor': '#e74c3c',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '16px',
                            'fontWeight': 'bold'
                        }
                    )
                ], style={'marginBottom': '20px'}),

                # Statistics display
                html.Div([
                    html.H4("Statistics", style={'borderBottom': '1px solid #bdc3c7', 'paddingBottom': '5px'}),
                    html.Div(id='stats-display')
                ])

            ], className='control-panel')
        ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'}),

        # RIGHT column: Heatmap
        html.Div([
            dcc.Graph(
                id='heatmap',
                style={'height': '80vh'},
                config={'displayModeBar': True, 'displaylogo': False}
            ),
            html.Div(id='click-info', style={
                'marginTop': '10px',
                'padding': '10px',
                'borderRadius': '5px',
                'textAlign': 'center',
                'fontWeight': 'bold'
            })
        ], style={'width': '73%', 'display': 'inline-block', 'padding': '20px'})

    ], style={'display': 'flex', 'flexWrap': 'nowrap', 'alignItems': 'flex-start'}),

    # Hidden div to store click data
    dcc.Store(id='click-data-store')

], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1800px', 'margin': '0 auto', 'padding': '20px'})


@app.callback(
    [Output('heatmap', 'figure'),
     Output('stats-display', 'children'),
     Output('click-info', 'children'),
     Output('threshold-input', 'value'),
     Output('color-a-input', 'value'),
     Output('color-b-input', 'value'),
     Output('slice-slider', 'value'),
     Output('min-input', 'value'),
     Output('max-input', 'value')],
    [Input('scalar-field-dropdown', 'value'),
     Input('color-a-input', 'value'),
     Input('color-b-input', 'value'),
     Input('threshold-input', 'value'),
     Input('min-input', 'value'),
     Input('max-input', 'value'),
     Input('slice-slider', 'value'),
     Input('reset-button', 'n_clicks'),
     Input('rescale-button', 'n_clicks'),
     Input('heatmap', 'clickData')],
    [State('threshold-input', 'value'),
     State('color-a-input', 'value'),
     State('color-b-input', 'value')]
)
def update_visualization(scalar_field, colorA, colorB, threshold_manual, min_val, max_val, slice_idx, reset_clicks, rescale_clicks, click_data,
                        current_threshold, current_colorA, current_colorB):
    """Update visualization based on user interactions"""
    global current_data, vtk_reader

    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Handle reset
    if triggered_id == 'reset-button':
        current_data['threshold'] = current_data['initial_threshold']
        current_data['colorA'] = current_data['initial_colorA']
        current_data['colorB'] = current_data['initial_colorB']
        current_data['range_min'] = current_data['stats']['min']
        current_data['range_max'] = current_data['stats']['max']
        current_data['clicked_value'] = None
        current_data['click_count'] = 0
        current_data['first_click'] = None
        threshold_manual = current_data['threshold']
        colorA = current_data['colorA']
        colorB = current_data['colorB']
        min_val = current_data['range_min']
        max_val = current_data['range_max']

    # Handle scalar field change
    if triggered_id == 'scalar-field-dropdown' and scalar_field:
        if scalar_field != current_data.get('current_scalar'):
            x_coords, y_coords, scalars, stats = vtk_reader.get_slice(
                axis=current_data['axis'],
                index=current_data['slice_index'],
                scalar_name=scalar_field
            )
            X_grid, Y_grid, Z_grid = vtk_reader.interpolate_to_grid(
                x_coords, y_coords, scalars, resolution=500
            )
            current_data['X_grid'] = X_grid
            current_data['Y_grid'] = Y_grid
            current_data['Z_grid'] = Z_grid
            current_data['stats'] = stats
            current_data['current_scalar'] = scalar_field
            current_data['clicked_value'] = None
            # Reset range to full data range
            current_data['range_min'] = stats['min']
            current_data['range_max'] = stats['max']
            # Reset threshold to new midpoint
            threshold_manual = (stats['min'] + stats['max']) / 2
            current_data['threshold'] = threshold_manual
            current_data['initial_threshold'] = threshold_manual
            # Reset click counter
            current_data['click_count'] = 0
            current_data['first_click'] = None

    # Handle slice change
    if triggered_id == 'slice-slider' and vtk_reader and vtk_reader.is_3d:
        if slice_idx != current_data['slice_index']:
            x_coords, y_coords, scalars, stats = vtk_reader.get_slice(
                axis=current_data['axis'],
                index=slice_idx,
                scalar_name=current_data.get('current_scalar')
            )
            X_grid, Y_grid, Z_grid = vtk_reader.interpolate_to_grid(
                x_coords, y_coords, scalars, resolution=500
            )
            current_data['X_grid'] = X_grid
            current_data['Y_grid'] = Y_grid
            current_data['Z_grid'] = Z_grid
            current_data['stats'] = stats
            current_data['slice_index'] = slice_idx
            current_data['clicked_value'] = None

    # Handle Select Range button - activate selection mode
    if triggered_id == 'rescale-button':
        # Activate selection mode - reset click counter
        current_data['click_count'] = 0
        current_data['first_click'] = None
        current_data['selection_mode'] = True
        current_data['clicked_value'] = "Selection mode active - click on image twice to select range"

    # Handle click on heatmap - only if selection mode is active
    if triggered_id == 'heatmap' and click_data and current_data.get('selection_mode', False):
        try:
            point_data = click_data['points'][0]
            clicked_z = point_data['z']

            if current_data['click_count'] == 0:
                # First click - store value
                current_data['first_click'] = clicked_z
                current_data['click_count'] = 1
                current_data['clicked_value'] = f"First click: {clicked_z:.4f} (click again to set range)"
            else:
                # Second click - set min and max
                val1 = current_data['first_click']
                val2 = clicked_z
                current_data['range_min'] = min(val1, val2)
                current_data['range_max'] = max(val1, val2)
                current_data['click_count'] = 0
                current_data['first_click'] = None
                current_data['selection_mode'] = False  # Deactivate selection mode
                current_data['clicked_value'] = f"Range selected from image: [{current_data['range_min']:.4f}, {current_data['range_max']:.4f}]"
                # Update threshold to midpoint of new range
                threshold_manual = (current_data['range_min'] + current_data['range_max']) / 2
                current_data['threshold'] = threshold_manual
        except (KeyError, IndexError):
            pass

    # Handle manual min/max input changes - auto-apply
    if triggered_id in ['min-input', 'max-input']:
        if min_val is not None and max_val is not None:
            current_data['range_min'] = min(min_val, max_val)
            current_data['range_max'] = max(min_val, max_val)
            # Update threshold to midpoint
            threshold_manual = (current_data['range_min'] + current_data['range_max']) / 2
            current_data['threshold'] = threshold_manual
            current_data['clicked_value'] = f"Manual range applied: [{current_data['range_min']:.4f}, {current_data['range_max']:.4f}]"
            current_data['selection_mode'] = False  # Deactivate selection mode if active

    # Update colors
    current_data['colorA'] = colorA
    current_data['colorB'] = colorB
    current_data['threshold'] = threshold_manual

    # Create gradient colorscale with white in the middle
    colorscale = [
        [0.0, colorA],
        [0.5, 'white'],
        [1.0, colorB]
    ]

    # Get current scalar field name for colorbar title
    current_scalar_name = current_data.get('current_scalar', 'Scalar Value')

    # Create heatmap figure with optimized settings and custom range
    fig = go.Figure(data=go.Heatmap(
        x=current_data['X_grid'][0, :],
        y=current_data['Y_grid'][:, 0],
        z=current_data['Z_grid'],
        colorscale=colorscale,
        zmid=threshold_manual,
        zmin=current_data.get('range_min', current_data['stats']['min']),
        zmax=current_data.get('range_max', current_data['stats']['max']),
        zsmooth='best',  # Enable smoothing for high-quality rendering
        colorbar=dict(
            title=dict(
                text=current_scalar_name,
                side="right",
                font=dict(size=25, family="Arial Black")  # Bold font for title
            ),
            len=0.6,  # Reduced height of colorbar (60% of plot height)
            tickmode="linear",
            tick0=current_data.get('range_min', current_data['stats']['min']),
            dtick=(current_data.get('range_max', current_data['stats']['max']) -
                   current_data.get('range_min', current_data['stats']['min'])) / 5,
            tickfont=dict(size=18)  # Larger font size for tick values
        ),
        hovertemplate='Value: %{z:.4f}<extra></extra>'
    ))

    fig.update_layout(
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            title=None,
            scaleanchor="y",  # Lock aspect ratio to y-axis
            scaleratio=1       # 1:1 aspect ratio
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            title=None,
            constrain='domain'  # Keep within domain
        ),
        template="plotly_white",
        height=700,
        width=700,  # Make square
        hovermode='closest',
        margin=dict(t=20, b=20, l=20, r=100)  # Reduced top margin, added right margin for colorbar
    )

    # Statistics panel
    stats = current_data['stats']
    stats_children = [
        html.P([html.Strong("Min: "), f"{stats['min']:.4f}"]),
        html.P([html.Strong("Max: "), f"{stats['max']:.4f}"]),
        html.P([html.Strong("Mean: "), f"{stats['mean']:.4f}"]),
        html.P([html.Strong("Std Dev: "), f"{stats['std']:.4f}"]),
        html.P([html.Strong("Threshold: "), f"{threshold_manual:.4f}"],
               style={'color': '#e74c3c', 'fontWeight': 'bold'})
    ]

    # Click info with indicator
    if current_data.get('selection_mode', False) and current_data.get('click_count', 0) == 1:
        click_info_element = html.Div([
            html.Span("Waiting for 2nd click | First value: ", style={'color': '#856404'}),
            html.Span(f"{current_data['first_click']:.4f}", style={'color': '#856404', 'fontWeight': 'bold'})
        ], style={'backgroundColor': '#fff3cd', 'padding': '10px', 'borderRadius': '5px'})
    elif current_data['clicked_value'] is not None:
        click_info_element = html.Div(
            str(current_data['clicked_value']),
            style={'backgroundColor': '#d4edda', 'color': '#155724', 'padding': '10px', 'borderRadius': '5px', 'fontWeight': 'bold'}
        )
    else:
        click_info_element = html.Div([
            html.Span("Type Min/Max to apply instantly, or click ", style={'color': '#2c3e50'}),
            html.Span("\"Select Range\"", style={'color': '#3498db', 'fontWeight': 'bold'}),
            html.Span(" then click image twice", style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#ecf0f1', 'padding': '10px', 'borderRadius': '5px'})

    return (
        fig,
        stats_children,
        click_info_element,
        threshold_manual,
        colorA,
        colorB,
        current_data['slice_index'],
        current_data['range_min'],
        current_data['range_max']
    )


if __name__ == '__main__':
    # Check if sample data exists, if not, generate it
    if not os.path.exists('sample_data/sample_3d.vti'):
        print("Sample data not found. Generating sample VTI files...")
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from sample_data.generate_sample_vti import generate_3d_vti, generate_2d_vti
        os.makedirs('sample_data', exist_ok=True)
        generate_3d_vti('sample_data/sample_3d.vti')
        generate_2d_vti('sample_data/sample_2d.vti')
        print("Sample files generated. Restarting initialization...")
        initialize_vtk_file('sample_data/sample_3d.vti')

    print("\n" + "="*60)
    print("VTK 2D SLICE VIEWER")
    print("="*60)
    print(f"Loaded file: {default_file if os.path.exists(default_file) else 'No file loaded'}")
    if vtk_reader:
        print(f"Dimensions: {vtk_reader.dimensions}")
        print(f"Is 3D: {vtk_reader.is_3d}")
        print(f"Scalar field: {vtk_reader.scalar_name}")
    print("\nStarting Dash server...")
    print("Open your browser and navigate to: http://127.0.0.1:8050")
    print("="*60 + "\n")

    app.run(debug=True, host='127.0.0.1', port=8050)
