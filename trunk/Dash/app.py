"""Multi-field VTK viewer with reusable tab panels."""
import os
from glob import glob

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
    return [
        html.Div([
            html.H3(label, className='dataset-title'),
            panel.build_layout()
        ], className='dataset-block')
        for label, panel in panels
    ]


TAB_ORDER = [tab['id'] for tab in TAB_CONFIGS]


def get_default_active_tab():
    for tab_id in TAB_ORDER:
        if tab_datasets.get(tab_id, {}).get("panels"):
            return tab_id
    return TAB_ORDER[0] if TAB_ORDER else None


def build_tab_bar():
    return [
        html.Button(
            tab_datasets.get(tab_id, {}).get("label", tab_id.title()),
            id={'type': 'tab-button', 'tab': tab_id},
            n_clicks=0,
            className='custom-tab'
        )
        for tab_id in TAB_ORDER
    ]


INITIAL_ACTIVE_TAB = get_default_active_tab()


app.layout = html.Div(
    id='app-container',
    className='theme-light',
    children=[
        html.Div([
            html.Div([
                html.Img(src='/assets/OP_Logo.png', className='app-logo', alt='OP logo'),
                html.H1(APP_TITLE, className='app-title')
            ], className='top-bar')
        ], className='app-header'),
        dcc.Store(id='active-tab', data=INITIAL_ACTIVE_TAB),
        html.Div(build_tab_bar(), className='tab-container'),
        html.Div(
            id='tab-content',
            children=build_tab_children(INITIAL_ACTIVE_TAB) if INITIAL_ACTIVE_TAB else []
        )
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
