"""Multi-field VTK viewer with reusable tab panels."""
import os
from glob import glob
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html

from utils.vtk_reader import VTKReader
from viewer import ViewerPanel


APP_TITLE = "OP Viewer"
TENSOR_COMPONENTS = ['xx', 'yy', 'zz', 'xy', 'yz', 'zx']


def tensor_scalars(array_name: str, prefix: str):
    return [
        {'label': f"{prefix}_{comp}", 'array': array_name, 'component': idx}
        for idx, comp in enumerate(TENSOR_COMPONENTS)
    ]

TAB_CONFIGS = [
    {
        "id": "phase-field",
        "label": "Phase Field",
        "datasets": [
            {
                "id": "phase",
                "label": "Phase Field",
                "file_glob": "VTK/PhaseField_00000000.vts",
                "scalars": [
                    {'label': 'Phase Field', 'array': 'PhaseFields'},
                    {'label': 'Interfaces', 'array': 'Interfaces'},
                    {'label': 'Phase Fraction', 'array': 'PhaseFraction_0'},
                ]
            }
        ],
    },
    {
        "id": "mechanics",
        "label": "Mechanics",
        "datasets": [
            {
                "id": "stresses",
                "label": "Stress Tensor",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "VTK/Stresses_*.vts",
                "scalars": [
                    {'label': 'Pressure', 'array': 'Pressure'},
                    {'label': 'von Mises', 'array': 'von Mises'},
                    *tensor_scalars('Stresses', 'σ')
                ],
            },
            {
                "id": "elastic",
                "label": "Elastic Strains",
                "file_glob": "VTK/ElasticStrains_*.vts",
                "scalars": tensor_scalars('ElasticStrains', 'ε'),
            },
        ],
    },
    {
        "id": "plasticity",
        "label": "Plasticity",
        "datasets": [
            {
                "id": "crss",
                "label": "CRSS",
                "file_glob": "VTK/CRSS_00001000.vts",
                "scalars": [
                    {'label': f"CRSS {i}", 'array': f"CRSS_0_{i}"}
                    for i in range(12)
                ],
            }
        ],
    },
]

reader_cache = {}


def get_reader(file_path):
    """Return cached VTKReader for a given file path."""
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"VTK file not found: {file_path}")
    if file_path not in reader_cache:
        reader_cache[file_path] = VTKReader(file_path)
    return reader_cache[file_path]


def latest_file(pattern: str):
    """Return the most recent file matching the glob pattern."""
    matches = sorted(glob(pattern))
    return matches[-1] if matches else None


app = Dash(__name__, suppress_callback_exceptions=True)
app.title = APP_TITLE

TEXTDATA_DIR = Path("TextData")
SIZE_DETAILS_FILE = TEXTDATA_DIR / "SizeDetails.dat"
SIZE_AVERAGE_FILE = TEXTDATA_DIR / "SizeAveInfo.dat"
STRESS_STRAIN_FILE = TEXTDATA_DIR / "StressStrainFile.txt"
CRSS_FILE = TEXTDATA_DIR / "CRSSFile.txt"
PLASTIC_STRAIN_FILE = TEXTDATA_DIR / "PlasticStrainFile.txt"
SIZE_AVERAGE_FILE = TEXTDATA_DIR / "SizeAveInfo.dat"


def load_size_details():
    if not SIZE_DETAILS_FILE.exists():
        return None
    rows = []
    try:
        with SIZE_DETAILS_FILE.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                try:
                    rows.append([float(p) for p in parts])
                except ValueError:
                    continue
    except OSError:
        return None
    if not rows:
        return None
    # Determine columns: first is time, second often count, rest are values
    has_count = len(rows[0]) > 2
    values_offset = 2 if has_count else 1
    labels = [str(idx + 1) for idx in range(len(rows[0]) - values_offset)]
    data_matrix = [row[values_offset:] for row in rows]
    times = [row[0] for row in rows]
    counts = [row[1] for row in rows] if has_count else None
    return {
        "times": times,
        "counts": counts,
        "labels": labels,
        "values": data_matrix,
    }


def load_size_averages():
    if not SIZE_AVERAGE_FILE.exists():
        return None
    times = []
    averages = []
    try:
        with SIZE_AVERAGE_FILE.open() as fh:
            for line in fh:
                parts = line.strip().split()
                if len(parts) < 3:
                    continue
                try:
                    times.append(float(parts[0]))
                    averages.append(float(parts[2]))
                except ValueError:
                    continue
    except OSError:
        return None
    if not times:
        return None
    return {"times": times, "averages": averages}


SIZE_DETAILS_DATA = load_size_details()
SIZE_AVERAGE_DATA = load_size_averages()


def load_stress_strain():
    if not STRESS_STRAIN_FILE.exists():
        return None
    try:
        with STRESS_STRAIN_FILE.open() as fh:
            lines = [line.strip() for line in fh if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    header = [token.strip() for token in lines[0].replace(',', ' ').split()]
    rows = []
    for line in lines[1:]:
        parts = [token.strip() for token in line.replace(',', ' ').split()]
        if len(parts) != len(header):
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue
    if not rows:
        return None

    columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}

    def col(*names):
        for name in names:
            if name in columns:
                return columns[name]
        return None

    strain = col('Epsilon_xx', 'EpsilonXX')
    time = col('Time', 'TimeStep')
    sigma_xx = col('Sigma_xx', 'SigmaXX')
    sigma_yy = col('Sigma_yy', 'SigmaYY')
    sigma_zz = col('Sigma_zz', 'SigmaZZ')
    mises = col('Mises', 'VonMises')

    if not strain or not sigma_xx:
        return None

    return {
        "strain": strain,
        "time": time,
        "components": {
            "Sigma_xx": sigma_xx,
            "Sigma_yy": sigma_yy,
            "Sigma_zz": sigma_zz,
            "Mises": mises,
        }
    }


def load_crss():
    if not CRSS_FILE.exists():
        return None
    try:
        with CRSS_FILE.open() as fh:
            lines = [line.strip() for line in fh if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    header = [h.strip() for h in lines[0].split(',')]
    if 'Time' not in header:
        return None
    times = []
    averages = []
    time_idx = header.index('Time')
    avg_idx = header.index('Average') if 'Average' in header else None
    slip_columns = [
        (idx, name)
        for idx, name in enumerate(header)
        if name.lower().startswith('ss_')
    ]
    series = {name: [] for _, name in slip_columns}
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) <= time_idx:
            continue
        try:
            time_val = float(parts[time_idx])
        except ValueError:
            continue
        if avg_idx is not None and len(parts) > avg_idx:
            try:
                avg_val = float(parts[avg_idx])
            except ValueError:
                avg_val = None
        else:
            avg_val = None
        row_series = {}
        for idx, name in slip_columns:
            if idx >= len(parts):
                row_series = {}
                break
            try:
                row_series[name] = float(parts[idx])
            except ValueError:
                row_series = {}
                break
        if not row_series:
            continue
        if avg_val is None:
            avg_val = float(np.mean(list(row_series.values())))
        times.append(time_val)
        averages.append(avg_val)
        for name in series:
            series[name].append(row_series[name])
    if not times:
        return None
    return {"times": times, "averages": averages, "series": series}


STRESS_STRAIN_DATA = load_stress_strain()
CRSS_DATA = load_crss()
PLASTIC_STRAIN_DATA = None


def load_plastic_strain():
    if not PLASTIC_STRAIN_FILE.exists():
        return None
    try:
        with PLASTIC_STRAIN_FILE.open() as fh:
            lines = [line.strip() for line in fh if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    header = [token.strip() for token in lines[0].replace(',', ' ').split()]
    rows = []
    for line in lines[1:]:
        parts = [token.strip() for token in line.replace(',', ' ').split()]
        if len(parts) != len(header):
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue
    if not rows:
        return None
    columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}

    def collect(prefix):
        return {
            name: columns[name]
            for name in columns
            if name.lower().startswith(prefix)
        }

    times = columns.get('time') or columns.get('Time')
    if not times:
        return None
    epsilons = collect('epsilon')
    if 'PEEQ' in columns:
        epsilons['PEEQ'] = columns['PEEQ']
    rates = collect('rate')
    return {
        "times": times,
        "epsilons": epsilons,
        "rates": rates
    }


PLASTIC_STRAIN_DATA = load_plastic_strain()

tab_datasets = {}
for tab in TAB_CONFIGS:
    datasets = []
    for dataset in tab.get("datasets", []):
        file_path = dataset.get("file")
        if dataset.get("file_glob"):
            file_path = latest_file(dataset["file_glob"])
        if not file_path:
            continue
        dataset_config = {
            "id": f"{tab['id']}-{dataset['id']}",
            "label": dataset["label"],
            "scalars": dataset.get("scalars"),
            "colorA": dataset.get("colorA"),
            "colorB": dataset.get("colorB"),
            "file": file_path,
            "scale": dataset.get("scale"),
            "units": dataset.get("units"),
            "overrides": dataset.get("overrides"),
        }
        try:
            panel = ViewerPanel(app, get_reader, dataset_config)
        except (FileNotFoundError, ValueError):
            continue
        datasets.append((dataset["label"], panel))
    tab_datasets[tab["id"]] = {
        "label": tab["label"],
        "panels": datasets
    }


def build_tab_children(tab_id):
    panels = tab_datasets[tab_id]["panels"]
    if not panels:
        return [html.Div("No datasets available for this tab.", className='dataset-empty')]
    cards = [
        html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(label, className='dataset-title')
            ], className='dataset-header'),
            html.Div(panel.build_layout(), className='dataset-body')
        ], className='dataset-block')
        for label, panel in panels
    ]
    if tab_id == 'phase-field':
        for builder in (build_size_details_card, build_grain_distribution_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'mechanics':
        stress_card = build_stress_strain_card()
        if stress_card:
            cards.append(stress_card)
    elif tab_id == 'plasticity':
        for builder in (build_crss_card, build_plastic_strain_card):
            card = builder()
            if card:
                cards.append(card)
    return [html.Div(cards, className='dataset-grid')]


TAB_ORDER = [tab['id'] for tab in TAB_CONFIGS]


def get_default_active_tab():
    for tab_id in TAB_ORDER:
        if tab_datasets.get(tab_id, {}).get("panels"):
            return tab_id
    return TAB_ORDER[0] if TAB_ORDER else None


def build_tab_bar():
    icons = {
        "phase-field": "⛶",
        "mechanics": "⚙",
        "plasticity": "🧪",
    }
    return [
        html.Button(
            [
                html.Span(icons.get(tab_id, "•"), className="tab-icon"),
                html.Span(
                    tab_datasets.get(tab_id, {}).get("label", tab_id.title()),
                    className="tab-label"
                ),
            ],
            id={'type': 'tab-button', 'tab': tab_id},
            n_clicks=0,
            className='custom-tab'
        )
        for tab_id in TAB_ORDER
    ]


INITIAL_ACTIVE_TAB = get_default_active_tab()


def build_size_details_card():
    data = SIZE_DETAILS_DATA
    if not data:
        return None
    time_options = []
    for t in data['times']:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})
    value_labels = data['labels']
    if not value_labels:
        return None
    default_time = time_options[0]['value'] if time_options else None
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Details', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Label('Time Step', className='textdata-label'),
                dcc.Dropdown(
                    id='size-card-time',
                    options=time_options,
                    value=default_time,
                    clearable=False,
                    className='textdata-input'
                )
            ], className='textdata-control'),
            html.Div([
                html.Label('Chart Style', className='textdata-label'),
                dcc.RadioItems(
                    id='size-card-mode',
                    options=[
                        {'label': 'Bar', 'value': 'bar'},
                        {'label': 'Line', 'value': 'line'}
                    ],
                    value='bar',
                    inline=True,
                    className='textdata-radio',
                    labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                    inputStyle={'marginRight': '4px'}
                )
            ], className='textdata-control'),
        ], className='textdata-controls'),
        html.Div([
            dcc.Graph(id='size-card-main', className='textdata-plot'),
            dcc.Graph(id='size-card-line', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_grain_distribution_card():
    data = SIZE_DETAILS_DATA
    if not data:
        return None
    times = data['times']
    if not times:
        return None
    time_options = []
    for t in times:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})
    default_time = time_options[0]['value']
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Distribution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Label('Time Step', className='textdata-label'),
                dcc.Dropdown(
                    id='grain-dist-time',
                    options=time_options,
                    value=default_time,
                    clearable=False,
                    className='textdata-input'
                )
            ], className='textdata-control'),
            html.Div([
                html.Label('Number of Bins', className='textdata-label'),
                dcc.Slider(
                    id='grain-dist-bins',
                    min=5,
                    max=50,
                    step=5,
                    value=15,
                    marks={10: '10', 25: '25', 40: '40'},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], className='textdata-control')
        ], className='textdata-controls'),
        html.Div([
            dcc.Graph(id='grain-dist-fig', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_stress_strain_card():
    data = STRESS_STRAIN_DATA
    if not data:
        return None
    options = [
        {'label': 'σ_xx', 'value': 'Sigma_xx'},
        {'label': 'σ_yy', 'value': 'Sigma_yy'},
        {'label': 'σ_zz', 'value': 'Sigma_zz'},
        {'label': 'von Mises', 'value': 'Mises'},
    ]
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Stress–Strain Curves', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='stress-components',
                    options=options,
                    value=['Sigma_xx', 'Mises'],
                    className='textdata-radio',
                    labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                    inputStyle={'marginRight': '4px'}
                )
            ], className='textdata-control')
        ], className='textdata-controls'),
        html.Div([
            dcc.Graph(id='stress-strain-fig', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_crss_card():
    data = CRSS_DATA
    if not data:
        return None
    series = data.get('series') or {}
    options = [{'label': 'Average', 'value': 'Average'}]
    for name in sorted(series.keys()):
        options.append({'label': name.replace('ss_', 'SS ').upper(), 'value': name})
    fig = build_crss_figure()
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('CRSS Evolution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='crss-component-select',
                    options=options,
                    value=['Average'],
                    className='textdata-radio',
                    labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                    inputStyle={'marginRight': '4px'}
                )
            ], className='textdata-control')
        ], className='textdata-controls'),
        html.Div([
            dcc.Graph(id='crss-avg-fig', figure=fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_crss_figure(selected=None):
    data = CRSS_DATA
    if not data:
        return go.Figure()
    times = data['times']
    series = data.get('series') or {}
    if not selected:
        selected = ['Average']
    traces = []
    for key in selected:
        if key == 'Average':
            values = data['averages']
            label = 'Average'
        else:
            values = series.get(key)
            label = key.replace('ss_', 'SS ').upper()
        if not values:
            continue
        traces.append(go.Scatter(
            x=times,
            y=np.array(values) / 1e6,
            mode='lines',
            line=dict(width=2),
            name=label
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(
            text="CRSS vs Time",
            x=0.5,
            xanchor='center',
            font=dict(size=20, family='Inter, sans-serif', color='#12294f')
        ),
        margin=dict(l=50, r=150, t=60, b=60),
        height=320,
        template='plotly_white',
        legend=dict(
            orientation='v',
            x=1.02,
            xanchor='left',
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(24,53,104,0.15)',
            borderwidth=1
        )
    )
    fig.update_xaxes(
        title="Time",
        title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="CRSS (MPa)",
        title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
    )
    return fig


def build_plastic_strain_card():
    data = PLASTIC_STRAIN_DATA
    if not data:
        return None
    strain_fig, rate_fig = build_plastic_strain_figures()
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Plastic Strain Insights', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            dcc.Graph(id='plastic-strain-eps', figure=strain_fig, className='textdata-plot'),
            dcc.Graph(id='plastic-strain-rate', figure=rate_fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_plastic_strain_figures():
    data = PLASTIC_STRAIN_DATA
    times = data['times']
    eps = data['epsilons']
    rates = data['rates']
    strain_traces = []
    for name, values in sorted(eps.items()):
        display = name.replace('_', ' ').title()
        strain_traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(width=2),
            name=display
        ))
    rate_traces = []
    for name, values in sorted(rates.items()):
        display = name.replace('_', ' ').title()
        rate_traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(width=2),
            name=display
        ))
    strain_fig = go.Figure(data=strain_traces)
    strain_fig.update_layout(
        title=dict(
            text="Plastic Strain Components",
            x=0.5,
            font=dict(size=20, family='Inter, sans-serif', color='#12294f')
        ),
        margin=dict(l=50, r=30, t=60, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    rate_fig = go.Figure(data=rate_traces)
    rate_fig.update_layout(
        title=dict(
            text="Plastic Strain Rates",
            x=0.5,
            font=dict(size=20, family='Inter, sans-serif', color='#12294f')
        ),
        margin=dict(l=50, r=30, t=60, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    for fig, y_title in ((strain_fig, "Strain"), (rate_fig, "Strain Rate")):
        fig.update_xaxes(
            title="Time",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title=y_title,
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
    return strain_fig, rate_fig


app.layout = html.Div(
    id='app-container',
    children=[
        dcc.Store(id='active-tab', data=INITIAL_ACTIVE_TAB),
        html.Div([
            html.Div([
                html.Div([
                    html.Img(src='/assets/OP_Logo.png', className='app-logo', alt='OP logo'),
                    html.H1(APP_TITLE, className='app-title')
                ], className='top-left'),
            ], className='top-bar')
        ], className='app-header'),
        html.Div([
            html.Div([
                html.Span("Modules", className='sidebar-title'),
                html.Div(build_tab_bar(), className='sidebar-tabs')
            ], className='sidebar'),
            html.Div([
                html.Div(
                    id='tab-content',
                    children=build_tab_children(INITIAL_ACTIVE_TAB) if INITIAL_ACTIVE_TAB else []
                )
            ], className='main-panel')
        ], className='layout-shell')
    ]
)


@app.callback(
    Output('active-tab', 'data'),
    Input({'type': 'tab-button', 'tab': ALL}, 'n_clicks'),
    State('active-tab', 'data'),
    prevent_initial_call=True
)
def set_active_tab(n_clicks, current_tab):
    trigger = ctx.triggered_id
    if isinstance(trigger, dict) and trigger.get('tab'):
        return trigger['tab']
    return current_tab


@app.callback(
    Output('tab-content', 'children'),
    Output({'type': 'tab-button', 'tab': ALL}, 'className'),
    Input('active-tab', 'data')
)
def render_active_tab(active_tab):
    if active_tab is None:
        return html.Div("No tabs available", className='dataset-empty'), ['custom-tab'] * len(TAB_ORDER)
    children = build_tab_children(active_tab)
    classes = [
        'custom-tab active-tab' if tab_id == active_tab else 'custom-tab'
        for tab_id in TAB_ORDER
    ]
    return children, classes


if SIZE_DETAILS_DATA:

    @app.callback(
        Output('size-card-main', 'figure'),
        Output('size-card-line', 'figure'),
        Input('size-card-time', 'value'),
        Input('size-card-mode', 'value')
    )
    def update_size_details(selected_time, chart_mode):
        data = SIZE_DETAILS_DATA
        times = data['times']
        labels = data['labels']
        values = data['values']
        if not times or not labels:
            return go.Figure(), go.Figure()
        try:
            time_value = float(selected_time)
        except (TypeError, ValueError):
            time_value = times[0]
        row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
        row_values = values[row_index]

        if chart_mode not in {'line', 'bar'}:
            chart_mode = 'bar'

        main_fig = go.Figure()
        if chart_mode == 'bar':
            main_fig.add_bar(x=labels, y=row_values, marker_color='#183568')
        else:
            main_fig.add_scatter(x=labels, y=row_values, mode='lines+markers', line=dict(color='#183568'))
        main_fig.update_layout(
            title=dict(
                text=f"Grain Sizes — Time {times[row_index]:.3f}",
                x=0.5,
                xanchor='center',
                font=dict(size=20, family='Inter, sans-serif', color='#12294f')
            ),
            margin=dict(l=50, r=30, t=60, b=60),
            height=320,
            template='plotly_white'
        )
        axis_title_font = dict(size=16, family='Inter, sans-serif', color='#12294f')
        tick_font = dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        main_fig.update_xaxes(title="Grain Number", title_font=axis_title_font, tickfont=tick_font)
        main_fig.update_yaxes(title="Grain Size", title_font=axis_title_font, tickfont=tick_font)

        if SIZE_AVERAGE_DATA:
            avg_times = SIZE_AVERAGE_DATA['times']
            avg_values = SIZE_AVERAGE_DATA['averages']
        else:
            avg_times = times
            avg_values = [
                sum(row) / len(row) if row else 0
                for row in values
            ]
        line_fig = go.Figure(
            data=[go.Scatter(x=avg_times, y=avg_values, mode='lines+markers', line=dict(color='#c50623'))]
        )
        line_fig.update_layout(
            title=dict(
                text="Average Grain Size Over Time",
                x=0.5,
                xanchor='center',
                font=dict(size=20, family='Inter, sans-serif', color='#12294f')
            ),
            margin=dict(l=50, r=30, t=60, b=60),
            height=320,
            template='plotly_white'
        )
        line_fig.update_xaxes(title="Time Step", title_font=axis_title_font, tickfont=tick_font)
        line_fig.update_yaxes(title="Average Grain Size", title_font=axis_title_font, tickfont=tick_font)

        return main_fig, line_fig

    @app.callback(
        Output('grain-dist-fig', 'figure'),
        Input('grain-dist-time', 'value'),
        Input('grain-dist-bins', 'value')
    )
    def update_grain_distribution(selected_time, bins):
        data = SIZE_DETAILS_DATA
        times = data['times']
        values = data['values']
        if not times or not values:
            return go.Figure()
        try:
            time_value = float(selected_time)
        except (TypeError, ValueError):
            time_value = times[0]
        row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
        row_values = values[row_index]
        if not row_values:
            return go.Figure()
        bin_count = int(bins) if bins else 15
        hist, edges = np.histogram(row_values, bins=bin_count)
        centers = (edges[:-1] + edges[1:]) / 2
        fig = go.Figure(
            data=[
                go.Bar(x=centers, y=hist, marker_color='#183568')
            ]
        )
        fig.update_layout(
            title=dict(
                text=f"Grain Size Distribution — Time {times[row_index]:.3f}",
                x=0.5,
                font=dict(size=20, family='Inter, sans-serif', color='#12294f')
            ),
            margin=dict(l=50, r=30, t=60, b=60),
            height=320,
            template='plotly_white'
        )
        fig.update_xaxes(
            title="Grain Size",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title="Frequency",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        return fig


if STRESS_STRAIN_DATA:

    @app.callback(
        Output('stress-strain-fig', 'figure'),
        Input('stress-components', 'value')
    )
    def update_stress_strain(components):
        data = STRESS_STRAIN_DATA
        strain = np.array(data['strain'])
        comp_map = data['components']
        labels = {
            "Sigma_xx": "σ_xx",
            "Sigma_yy": "σ_yy",
            "Sigma_zz": "σ_zz",
            "Mises": "von Mises",
        }
        default_components = ['Sigma_xx', 'Mises']
        selected = components or default_components
        traces = []
        for comp in selected:
            values = comp_map.get(comp)
            if values is None:
                continue
            traces.append(go.Scatter(
                x=strain,
                y=np.array(values) / 1e6,
                mode='lines',
                line=dict(width=2),
                name=labels.get(comp, comp)
            ))
        fig = go.Figure(data=traces)
        fig.update_layout(
            title=dict(
                text="Stress–Strain Response",
                x=0.5,
                font=dict(size=20, family='Inter, sans-serif', color='#12294f')
            ),
            margin=dict(l=50, r=150, t=60, b=60),
            height=320,
            template='plotly_white',
            legend=dict(
                orientation='v',
                x=1.02,
                xanchor='left',
                y=1,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(24,53,104,0.15)',
                borderwidth=1
            )
        )
        fig.update_xaxes(
            title="ε_xx",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title="Stress (MPa)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        return fig


if CRSS_DATA:

    @app.callback(
        Output('crss-avg-fig', 'figure'),
        Input('crss-component-select', 'value')
    )
    def update_crss_plot(selected_components):
        return build_crss_figure(selected_components)




if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(APP_TITLE.upper())
    print("=" * 60)
    for tab_id, info in tab_datasets.items():
        print(f"[{info['label']}]")
        if not info['panels']:
            print("  - No datasets found.")
            continue
        for dataset_label, panel in info['panels']:
            print(f"  - {dataset_label}: {panel.file_path}")
    print("\nStarting Dash server on http://127.0.0.1:8050\n")

    app.run(debug=True, host='127.0.0.1', port=8050)
