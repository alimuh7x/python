"""Multi-field VTK viewer with reusable tab panels."""
import base64
import os
import re
import warnings
from glob import glob
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import ALL, MATCH, Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate
from flask import render_template_string
import markdown
from scipy import stats
import dash_mantine_components as dmc

from utils.vtk_reader import VTKReader
from viewer import ViewerPanel


APP_TITLE = "OPView"
TENSOR_COMPONENTS = ['xx', 'yy', 'zz', 'xy', 'yz', 'zx']
BASE_DIR = Path(__file__).resolve().parent


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
                "file_glob": "VTK/PhaseField_*.vts",
                "scalars": [
                    {'label': 'Phase Field', 'array': 'PhaseFields'},
                    {'label': 'Interfaces', 'array': 'Interfaces'},
                    {'label': 'Phase Fraction', 'array': 'PhaseFraction_0'},
                ]
            }
        ],
    },
    {
        "id": "composition",
        "label": "Composition",
        "datasets": [
            {
                "id": "composition",
                "label": "Composition",
                "file_glob": "VTK/Composition_*.vts",
                "scalars": [
                    {'label': 'Weight Fraction FE (Total)', 'array': 'WeightFractionsTotal_FE'},
                    {'label': 'Mole Fraction FE (Total)', 'array': 'MoleFractionsTotal_FE'},
                    {'label': 'Mole Fraction FE (Phase 0)', 'array': 'MoleFractionsPhase_FE(0)'},
                    {'label': 'Mole Fraction FE (Phase 1)', 'array': 'MoleFractionsPhase_FE(1)'},
                    {'label': 'Weight Fraction SOLVENT (Total)', 'array': 'WeightFractionsTotal_SOLVENT'},
                    {'label': 'Mole Fraction SOLVENT (Total)', 'array': 'MoleFractionsTotal_SOLVENT'},
                    {'label': 'Mole Fraction SOLVENT (Phase 0)', 'array': 'MoleFractionsPhase_SOLVENT(0)'},
                    {'label': 'Mole Fraction SOLVENT (Phase 1)', 'array': 'MoleFractionsPhase_SOLVENT(1)'},
                    {'label': 'Weight Fraction CL (Total)', 'array': 'WeightFractionsTotal_CL'},
                    {'label': 'Mole Fraction CL (Total)', 'array': 'MoleFractionsTotal_CL'},
                    {'label': 'Mole Fraction CL (Phase 0)', 'array': 'MoleFractionsPhase_CL(0)'},
                    {'label': 'Mole Fraction CL (Phase 1)', 'array': 'MoleFractionsPhase_CL(1)'},
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
                # Store elastic strains in percent for all components
                "units": "%",
                "scale": 100.0,
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
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "VTK/CRSS_00001000.vts",
                "scalars": [
                    {'label': f"CRSS {i}", 'array': f"CRSS_0_{i}"}
                    for i in range(12)
                ],
            },
            {
                "id": "plastic-strain",
                "label": "Plastic Strain",
                "file_glob": "VTK/PlasticStrain_*.vts",
                # Store plastic strains in percent for all components
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('PlasticStrain', 'εᵖ'),
            },
        ],
    },
]

reader_cache = {}

# Grid cache for comparison panel optimizations: key = (file_name, scalar, slice_index) → (figure, colorbar_figure)
comparison_grid_cache = {}
comparison_grid_cache_data = {}  # key = (file_name, scalar, slice_index) → (X_grid, Y_grid, Z_grid, stats, state_dict)

# Cache for rendered heatmap rows to avoid rebuilding on tab switches
comparison_heatmap_rows_cache = {
    'settings_key': None,  # Hash of current settings
    'files_key': None,     # Hash of current files
    'rows': None           # Cached rendered rows
}


def vtk_data_dir():
    """Return the VTK data directory preferring the caller's CWD/VTK, else repo VTK."""
    cwd_vtk = Path.cwd() / "VTK"
    if cwd_vtk.exists():
        return cwd_vtk
    fallback = BASE_DIR / "VTK"
    return fallback if fallback.exists() else Path.cwd()


DEFAULT_VTK_FOLDER_LABEL = vtk_data_dir().name or "VTK"
COMPARISON_FOLDER_NAME = "Comparison"
ALLOWED_VTK_EXTENSIONS = ('.vtk', '.vti', '.vtp', '.vtr', '.vts')


def comparison_data_dir() -> Path:
    """
    Return the comparison folder path, preferring the user's working directory.
    The directory is created inside the repository when no working-copy folder exists.
    """
    cwd_dir = Path.cwd() / COMPARISON_FOLDER_NAME
    repo_dir = BASE_DIR / COMPARISON_FOLDER_NAME
    if cwd_dir.exists():
        return cwd_dir
    if repo_dir.exists():
        return repo_dir
    repo_dir.mkdir(parents=True, exist_ok=True)
    return repo_dir


def list_comparison_files():
    """Return sorted filenames in the comparison folder filtered by allowed extensions."""
    directory = comparison_data_dir()
    files = [
        child.name
        for child in sorted(directory.iterdir())
        if child.is_file() and child.suffix.lower() in ALLOWED_VTK_EXTENSIONS
    ]
    return files

def resolve_vtk_path(pattern: str) -> Path:
    """Resolve a file or glob pattern into the VTK data dir."""
    p = Path(pattern)
    if p.is_absolute():
        return p
    parts = p.parts
    if parts and parts[0].lower() == "vtk":
        p = Path(*parts[1:])
    return vtk_data_dir() / p


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
SIZE_DETAILS_FILE   = TEXTDATA_DIR / "SizeDetails.dat"
SIZE_AVERAGE_FILE   = TEXTDATA_DIR / "SizeAveInfo.dat"
STRESS_STRAIN_FILE  = TEXTDATA_DIR / "StressStrainFile.txt"
CRSS_FILE           = TEXTDATA_DIR / "CRSSFile.txt"
PLASTIC_STRAIN_FILE = TEXTDATA_DIR / "PlasticStrainFile.txt"
SIZE_AVERAGE_FILE   = TEXTDATA_DIR / "SizeAveInfo.dat"


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

    strain_components = {
        name: columns[name]
        for name in columns
        if name.lower().startswith('epsilon')
    }
    strain = strain_components.get('Epsilon_xx') or strain_components.get('EpsilonXX')
    if strain is None and strain_components:
        strain = next(iter(strain_components.values()))
    time = col('Time', 'TimeStep')
    sigma_xx = col('Sigma_xx', 'SigmaXX')
    sigma_yy = col('Sigma_yy', 'SigmaYY')
    sigma_zz = col('Sigma_zz', 'SigmaZZ')
    mises = col('Mises', 'VonMises')

    stress_components = {
        key: value for key, value in {
            "Sigma_xx": sigma_xx,
            "Sigma_yy": sigma_yy,
            "Sigma_zz": sigma_zz,
            "Mises": mises,
        }.items() if value is not None
    }

    if not strain or not stress_components:
        return None

    return {
        "strain": strain,
        "time": time,
        "components": stress_components,
        "strain_components": strain_components
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


DOCUMENTATION_FILE = Path("assets/Documentation.md")


@app.server.route('/docs')
def render_docs():
    if not DOCUMENTATION_FILE.exists():
        return render_template_string(
            "<h1>Documentation</h1><p>Documentation file not found.</p>"
        )
    content = DOCUMENTATION_FILE.read_text(encoding='utf-8')
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc'])
    html_body = md.convert(content)
    toc_html = md.toc
    template = """
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>OpenPhase Documentation</title>
        <link rel="stylesheet" href="/assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { background: var(--bg-gradient); }
            .doc-article {
                background: var(--surface);
                border-radius: 18px;
                padding: 32px 40px;
                box-shadow: var(--shadow-lg);
                line-height: 1.7;
                color: var(--text-main);
                word-wrap: break-word;
            }
            .doc-article h1, .doc-article h2, .doc-article h3 {
                color: #183568;
            }
            .doc-article pre {
                background: #0d2244;
                color: #fff;
                padding: 12px;
                border-radius: 8px;
                overflow-x: auto;
            }
            .doc-article code {
                color: #c50623;
            }
            .doc-sidebar .sidebar-tabs {
                overflow: visible;
            }
            .doc-sidebar .toc {
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .doc-sidebar .toc ul {
                list-style: none;
                padding-left: 16px;
                margin-top: 6px;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .doc-sidebar .toc a {
                color: rgba(255,255,255,0.75);
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                display: block;
                padding: 8px 12px;
                border-radius: 12px;
                transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
            }
            .doc-sidebar .toc a:hover {
                color: #fff;
                background: rgba(255,255,255,0.1);
            }
            .doc-sidebar .toc a.active {
                color: #fff;
                background: rgba(255,255,255,0.15);
                box-shadow: inset 3px 0 0 #c50623;
            }
            .doc-main {
                max-width: 1080px;
                width: 100%;
                margin: 0 auto;
            }
            /* Ensure doc header logo matches main app sizing */
            .app-logo {
                width: 42px;
                height: 42px;
                object-fit: contain;
            }
        </style>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </head>
    <body>
        <div id="app-container">
            <div class="app-header">
                <div class="top-bar">
                    <div class="top-left">
                        <img src="/assets/OP_Logo_main.png" class="app-logo" alt="OP logo">
                        <h1 class="app-title">OPV<span class="app-title-sub">iew</span></h1>
                    </div>
                    <div class="top-right">
                        <a class="doc-link" href="/">Back to App</a>
                    </div>
                </div>
            </div>
            <div class="layout-shell">
                <div class="sidebar doc-sidebar" style="position: sticky; top: 0; max-height: 100vh; overflow-y: auto; width: 280px;">
                    <span class="sidebar-title">Contents</span>
                    <div class="sidebar-tabs">
                        {{ toc|safe }}
                    </div>
                </div>
                <div class="main-panel">
                    <div class="doc-main">
                        <article class="doc-article">
                            {{ body|safe }}
                        </article>
                    </div>
                </div>
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const tocLinks = Array.from(document.querySelectorAll('.doc-sidebar .toc a'));
                if (!tocLinks.length) {
                    return;
                }
                const headingMap = tocLinks.map(link => {
                    const hash = decodeURIComponent(link.hash || '').replace('#', '');
                    const target = document.getElementById(hash);
                    return { link, target };
                }).filter(item => item.target);

                function setActive(link) {
                    tocLinks.forEach(l => l.classList.remove('active'));
                    if (link) {
                        link.classList.add('active');
                    }
                }

                tocLinks.forEach(link => {
                    link.addEventListener('click', () => setActive(link));
                });

                const observer = new IntersectionObserver((entries) => {
                    const visible = entries
                        .filter(entry => entry.isIntersecting)
                        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
                    if (visible.length > 0) {
                        const match = headingMap.find(item => item.target === visible[0].target);
                        if (match) {
                            setActive(match.link);
                        }
                    }
                }, {
                    rootMargin: '-150px 0px -60% 0px',
                    threshold: [0.2, 0.4, 0.6]
                });

                headingMap.forEach(item => observer.observe(item.target));

                // highlight first item initially
                setActive(tocLinks[0]);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(template, body=html_body, toc=toc_html)


def compute_average_series(series_dict):
    """Return element-wise average across provided series."""
    arrays = []
    lengths = []
    for values in series_dict.values():
        if values is None:
            continue
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            continue
        arrays.append(arr)
        lengths.append(arr.size)
    if not arrays:
        return None
    min_len = min(lengths)
    stacked = np.vstack([arr[:min_len] for arr in arrays])
    return np.mean(stacked, axis=0)


def build_histogram_figure(values, x_label, bins=None, fit=False):
    if values is None:
        return go.Figure(), "No data available"
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return go.Figure(), "No data available"
    if bins is None:
        nbins = max(10, min(60, int(np.sqrt(arr.size) * 3)))
    else:
        nbins = max(5, min(100, int(bins)))
    hist = go.Histogram(
        x=arr,
        nbinsx=nbins,
        marker_color='#183568',
        name='Histogram'
    )

    x_min, x_max = arr.min(), arr.max()
    if np.isclose(x_min, x_max):
        x_min -= 1
        x_max += 1
    x_vals = np.linspace(x_min, x_max, 400)
    summary = "_Enable **Best-fit PDF** to evaluate distributions._"
    traces = [hist]

    if fit:
        best_fit = fit_best_distribution(arr)
        if best_fit:
            pdf_vals = best_fit['dist'].pdf(x_vals, *best_fit['params'])
            counts, edges = np.histogram(arr, bins=nbins)
            bin_width = edges[1] - edges[0]
            pdf_scaled = pdf_vals * arr.size * bin_width
            pdf_line = go.Scatter(
                x=x_vals,
                y=pdf_scaled,
                mode='lines',
                line=dict(color='#0d2244', width=2),
                name=f"{best_fit['name']} PDF"
            )
            traces.append(pdf_line)
            summary = format_fit_summary(best_fit)
        else:
            summary = "_No valid fit available._"

    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=50, r=20, t=30, b=50),
        height=320,
        template='plotly_white',
        bargap=0.05
    )
    fig.update_xaxes(
        title=x_label,
        title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
        tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="Frequency",
        title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
        tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
    )
    fig.update_traces(showlegend=False, selector=lambda t: isinstance(t, go.Histogram))
    return fig, summary


def crss_series_values(component):
    data = CRSS_DATA
    if not data:
        return None
    if component == 'Average':
        return np.asarray(data['averages']) / 1e6
    values = (data.get('series') or {}).get(component)
    return np.asarray(values) / 1e6 if values is not None else None


def stress_series_values(component):
    data = STRESS_STRAIN_DATA
    if not data:
        return None
    comps = data.get('components') or {}
    if component == 'Average':
        avg = compute_average_series(comps)
        return avg / 1e6 if avg is not None else None
    values = comps.get(component)
    return np.asarray(values) / 1e6 if values is not None else None


def strain_series_values(component):
    data = STRESS_STRAIN_DATA
    if not data:
        return None
    comps = data.get('strain_components') or {}
    if component == 'Average':
        avg = compute_average_series(comps)
        return avg * 100.0 if avg is not None else None
    values = comps.get(component)
    return np.asarray(values) * 100.0 if values is not None else None


def build_grain_histogram(time_value, bins, fit=False):
    data = SIZE_DETAILS_DATA
    if not data:
        return go.Figure(), "_No data available._"
    times = data['times']
    values = data['values']
    if not times or not values:
        return go.Figure(), "_No data available._"
    try:
        time_value = float(time_value)
    except (TypeError, ValueError):
        time_value = times[0]
    row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
    row_values = values[row_index]
    if not row_values:
        return go.Figure(), "_No data available._"
    fig, summary = build_histogram_figure(row_values, "Grain Size", bins, fit=fit)
    summary = f"**Time:** {times[row_index]:.3f}\n\n" + summary
    return fig, summary


def fit_best_distribution(data):
    """Fit candidate distributions and select best via BIC."""
    if data is None:
        return None
    arr = np.asarray(data, dtype=float)
    if arr.size < 3 or np.allclose(arr.std(), 0):
        return None
    candidates = {
        "Normal": stats.norm,
        "Lognormal": stats.lognorm,
        "Weibull": stats.weibull_min,
        "Gamma": stats.gamma
    }
    best = None
    n = arr.size
    for name, dist in candidates.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                params = dist.fit(arr)
        except Exception:
            continue
        try:
            loglik = np.sum(dist.logpdf(arr, *params))
        except Exception:
            continue
        k = len(params)
        aic = 2 * k - 2 * loglik
        bic = np.log(n) * k - 2 * loglik
        if not best or bic < best['bic']:
            best = {
                "name": name,
                "dist": dist,
                "params": params,
                "aic": aic,
                "bic": bic
            }
    return best


def format_fit_summary(best_fit):
    if not best_fit:
        return "_No valid fit available._"
    label_map = {
        "Normal": ["\\mu", "\\sigma"],
        "Lognormal": ["s", "\\mu", "\\sigma"],
        "Weibull": ["k", "\\lambda", "\\theta"],
        "Gamma": ["k", "\\theta", "\\lambda"]
    }
    labels = label_map.get(best_fit["name"]) or [f"\\theta_{i+1}" for i in range(len(best_fit["params"]))]
    param_lines = []
    for label, value in zip(labels, best_fit["params"]):
        param_lines.append(f"{label} &= {value:.3g}")
    params_block = " \\\\ ".join(param_lines)
    return (
        f"**Best Fit:** $\\text{{{best_fit['name']}}}$\n\n"
        f"$$\\begin{{aligned}}{params_block}\\end{{aligned}}$$\n\n"
        f"$$\\mathrm{{AIC}} = {best_fit['aic']:.2f}\\quad "
        f"\\mathrm{{BIC}} = {best_fit['bic']:.2f}$$"
    )


tab_datasets = {}
for tab in TAB_CONFIGS:
    datasets = []
    for dataset in tab.get("datasets", []):
        # Collect all available files for this dataset (time steps)
        files = []
        if dataset.get("file_glob"):
            glob_pattern = resolve_vtk_path(dataset["file_glob"])
            files = sorted(glob(str(glob_pattern)))
        elif dataset.get("file"):
            files = [str(resolve_vtk_path(dataset["file"]))]
        if not files:
            continue
        # Default to latest file for initial view
        file_path = files[-1]
        dataset_config = {
            "id": f"{tab['id']}-{dataset['id']}",
            "label": dataset["label"],
            "scalars": dataset.get("scalars"),
            "colorA": dataset.get("colorA"),
            "colorB": dataset.get("colorB"),
            "file": file_path,
            "files": files,
            "scale": dataset.get("scale"),
            "units": dataset.get("units"),
            "overrides": dataset.get("overrides"),
            "enable_line_scan": tab['id'] != 'phase-field',  # Enable for all tabs except phase-field
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


comparison_panels = {}


def _comparison_panel_id(group: str) -> str:
    safe = re.sub(r'[^a-z0-9]+', '-', group.lower()).strip('-')
    suffix = safe or 'group'
    return f"comparison-{suffix}"


def _comparison_group_name(file_name: str) -> str:
    return file_name.split('_', 1)[0] or file_name


def _group_comparison_files(file_names):
    grouped = {}
    for file_name in sorted(set(file_names or [])):
        group = _comparison_group_name(file_name)
        grouped.setdefault(group, []).append(file_name)
    return grouped


def _comparison_scalar_options(panels):
    """Return unique scalar dropdown options aggregated from all panels."""
    seen = set()
    options = []
    for panel_entry in panels.values():
        if not panel_entry:
            continue
        _, panel = panel_entry
        for opt in panel.scalar_options:
            value = opt['value']
            if value in seen:
                continue
            seen.add(value)
            options.append(opt)
    return options


def _comparison_palette_options(panels):
    """Return palette dropdown options for comparison controls."""
    if not panels:
        return [{'label': key.replace('-', ' ').title(), 'value': key} for key in ViewerPanel.PALETTES.keys()]
    _, panel = next(iter(panels.values()))
    return panel.palette_options


def _parse_float(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_range(min_val, max_val):
    if min_val is None or max_val is None:
        return min_val, max_val
    lo, hi = sorted([min_val, max_val])
    return lo, hi


def _comparison_range_defaults(panels, scalar_key):
    """Return range defaults for the requested scalar from the first suitable panel."""
    for file_name, panel_entry in panels.items():
        if not panel_entry:
            continue
        _, panel = panel_entry
        descriptor = panel.scalar_map.get(scalar_key)
        if not descriptor:
            continue
        file_path = str(comparison_data_dir() / file_name)
        try:
            reader = panel.reader_factory(file_path)
        except FileNotFoundError:
            continue
        state, _, _ = panel._build_state(reader, file_path, descriptor['value'], return_slice=True)
        return state.range_min, state.range_max
    return None, None


def _comparison_settings(panels, scalar_value=None, range_min=None, range_max=None,
                         palette_value=None, full_scale=False, slider_range=None):
    """Normalize comparison control inputs into a settings dict plus dropdown options."""
    scalar_options = _comparison_scalar_options(panels)
    palette_options = _comparison_palette_options(panels)
    scalar_values = {opt['value'] for opt in scalar_options}
    palette_values = {opt['value'] for opt in palette_options}
    default_scalar = next((opt['value'] for opt in scalar_options), None)
    default_palette = next((opt['value'] for opt in palette_options), 'aqua-fire')

    selected_scalar = scalar_value if scalar_value in scalar_values else default_scalar
    selected_palette = palette_value if palette_value in palette_values else default_palette

    parsed_min = _parse_float(range_min)
    parsed_max = _parse_float(range_max)
    slider_min = None
    slider_max = None
    if slider_range and isinstance(slider_range, (list, tuple)) and len(slider_range) == 2:
        try:
            slider_min = float(slider_range[0])
            slider_max = float(slider_range[1])
        except (TypeError, ValueError):
            slider_min = None
            slider_max = None
    if slider_min is not None and slider_max is not None:
        parsed_min = slider_min
        parsed_max = slider_max
    if selected_scalar and (parsed_min is None or parsed_max is None):
        fallback_min, fallback_max = _comparison_range_defaults(panels, selected_scalar)
        if parsed_min is None:
            parsed_min = fallback_min
        if parsed_max is None:
            parsed_max = fallback_max

    clamped_min, clamped_max = _clamp_range(parsed_min, parsed_max)

    settings = {
        'scalar': selected_scalar,
        'range_min': clamped_min,
        'range_max': clamped_max,
        'palette': selected_palette,
        'full_scale': bool(full_scale),
    }
    return settings, scalar_options, palette_options


def _comparison_dataset_config(file_name: str):
    path = comparison_data_dir() / file_name
    if not path.exists():
        return None
    config = {
        "id": _comparison_panel_id(file_name),
        "label": file_name,
        "file": str(path),
        "files": [str(path)],
        "scalars": None,
        "enable_line_scan": True,
        "axis": 'y',
    }
    return config


def get_comparison_panels(file_names):
    panels = {}
    for file_name in sorted(set(file_names or [])):
        config = _comparison_dataset_config(file_name)
        if not config:
            continue
        entry = comparison_panels.get(file_name)
        panel = entry['panel'] if entry and entry['axis'] == config["axis"] else None
        if panel is None:
            try:
                panel = ViewerPanel(app, get_reader, config)
            except (FileNotFoundError, ValueError):
                continue
            comparison_panels[file_name] = {'axis': config["axis"], 'panel': panel}
        panels[file_name] = (config["label"], panel)

    for cached_file in list(comparison_panels.keys()):
        if cached_file not in panels:
            comparison_panels.pop(cached_file, None)
    return panels


def build_tab_children(tab_id):
    panels = tab_datasets[tab_id]["panels"]
    if not panels:
        return [html.Div("No datasets available for this tab.", className='dataset-empty')]
    cards = []

    # Add main viewer cards
    for label, panel in panels:
        # Main viewer card
        cards.append(html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(label, className='dataset-title')
            ], className='dataset-header'),
            html.Div(panel.build_layout(), className='dataset-body')
        ], className='dataset-block'))

        # Line scan and histogram cards - for all tabs EXCEPT Phase Field
        if tab_id != 'phase-field':
            cards.append(panel.build_line_scan_card())
            # build_histogram_card() returns None (deprecated - now combined with line scan)
            histogram_card = panel.build_histogram_card()
            if histogram_card:
                cards.append(histogram_card)

    if tab_id == 'phase-field':
        # Phase-field tab: show size-details and grain distribution cards.
        for builder in (build_size_details_card, build_grain_distribution_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'mechanics':
        for builder in (build_stress_strain_card, build_stress_hist_card, build_strain_hist_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'plasticity':
        for builder in (build_crss_card, build_plastic_strain_card):
            card = builder()
            if card:
                cards.append(card)
    return [html.Div(cards, className='dataset-grid')]


def _comparison_graph_id(file_name: str):
    safe = re.sub(r'[^a-z0-9]+', '-', file_name.lower()).strip('-')
    return {'type': 'comparison-graph', 'file': safe or 'file'}


def _comparison_heatmap_data(panel, file_name: str, settings):
    """Build comparison heatmap with grid caching for performance."""
    file_path = str(comparison_data_dir() / file_name)
    scalar_value = settings.get('scalar')
    descriptor = panel.scalar_map.get(scalar_value) or panel.scalar_defs[0]

    # Create cache key for grid data (independent of range/palette/full_scale)
    slice_index = settings.get('slice_index')
    if slice_index is None:
        slice_index = 0
    else:
        try:
            slice_index = int(slice_index)
        except (TypeError, ValueError):
            slice_index = 0

    grid_cache_key = (file_name, scalar_value, slice_index)

    # Check if we have cached grid data
    if grid_cache_key in comparison_grid_cache_data:
        X_grid, Y_grid, Z_grid, stats, state_dict = comparison_grid_cache_data[grid_cache_key]
        # Reconstruct state from cached data and apply current settings
        try:
            reader = panel.reader_factory(file_path)
        except FileNotFoundError:
            return None

        from viewer.state import ViewerState
        state = ViewerState(**state_dict)
    else:
        # First access: build state and cache the grid data
        try:
            reader = panel.reader_factory(file_path)
        except FileNotFoundError:
            return None
        try:
            state, slice_data, _ = panel._build_state(
                reader, file_path, descriptor['value'], return_slice=True
            )
        except Exception:
            return None

        # Cache the grid data
        if 'slice_data' in locals() and slice_data:
            # slice_data is a tuple: (X_grid, Y_grid, Z_grid, stats)
            X_grid, Y_grid, Z_grid, stats = slice_data

            # Store state as dict for serialization
            state_dict = {
                'scalar_key': state.scalar_key,
                'scalar_label': state.scalar_label,
                'axis': state.axis,
                'slice_index': state.slice_index,
                'colorA': state.colorA,
                'colorB': state.colorB,
                'palette': state.palette,
                'threshold': state.threshold,
                'range_min': state.range_min,
                'range_max': state.range_max,
                'file_path': state.file_path,
                'scale': state.scale,
                'units': state.units,
                'colorscale_mode': state.colorscale_mode,
            }
            comparison_grid_cache_data[grid_cache_key] = (X_grid, Y_grid, Z_grid, stats, state_dict)

    # Apply current settings to state
    range_min = settings.get('range_min')
    range_max = settings.get('range_max')
    if range_min is not None:
        state.range_min = range_min
    if range_max is not None:
        state.range_max = range_max
    if state.range_min is not None and state.range_max is not None and state.range_min > state.range_max:
        state.range_min, state.range_max = sorted([state.range_min, state.range_max])
    if state.range_min is not None and state.range_max is not None:
        state.threshold = (state.range_min + state.range_max) / 2
    state.palette = settings.get('palette') or state.palette
    state.colorscale_mode = 'dynamic' if settings.get('full_scale') else 'normal'
    state.slice_index = max(0, slice_index)

    return panel._build_heatmap_figures(reader, state, file_path, slice_data=None)


def build_comparison_heatmap_rows(panels, grouped, settings):
    """Return header + heatmap rows for each comparison group."""
    rows = []
    graph_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'responsive': False,
        'toImageButtonOptions': {'scale': 4}
    }
    for group, file_names in grouped.items():
        ordered = [(name, panels.get(name)) for name in file_names if name in panels]
        if not ordered:
            continue
        heatmap_children = [
            html.Div(
                html.Img(src='/assets/OP_Logo.png', className='heatmap-logo', alt='OP logo'),
                className='heatmap-logo-card comparison-heatmap-logo-card'
            )
        ]
        colorbar_fig = None
        for file_name, panel_entry in ordered:
            if not panel_entry:
                continue
            _, panel = panel_entry
            heatmap_data = _comparison_heatmap_data(panel, file_name, settings)
            if not heatmap_data:
                continue
            if colorbar_fig is None:
                colorbar_fig = heatmap_data['colorbar']
            heatmap_children.append(html.Div(
                dcc.Graph(
                    id=_comparison_graph_id(file_name),
                    className='heatmap-main-graph comparison-heatmap-graph',
                    figure=heatmap_data['figure'],
                    config=graph_config
                ),
                className='heatmap-main-card comparison-heatmap-main-card'
            ))

        if colorbar_fig:
            heatmap_children.append(html.Div(
                dcc.Graph(
                    className='heatmap-colorbar-graph comparison-heatmap-colorbar-graph',
                    figure=colorbar_fig,
                    config={'displayModeBar': False, 'displaylogo': False, 'responsive': False}
                ),
                className='heatmap-colorbar-card comparison-heatmap-colorbar-card',
                style={'width': '120px', 'height': '380px'}
            ))

        rows.append(html.Div(
            html.Div(heatmap_children, className='comparison-heatmap-row heatmap-row'),
            className='comparison-group-block'
        ))
    return rows


# ===== SECTION 4: Build Comparison Content with Persistent Values =====
def build_comparison_content(files, comparison_controls=None):
    """Render the comparison tab body showing uploaded files.

    Args:
        files: List of comparison file names
        comparison_controls: Dict with persisted control values {scalar, range_min, range_max, palette, full_scale, slider_range}
    """
    panels = get_comparison_panels(files)
    if not panels:
        return [html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3('Comparison Files', className='dataset-title')
            ], className='dataset-header'),
            html.Div(
                "No comparison files uploaded yet. Switch to Comparison tab and use \"Add VTK File\".",
                className='comparison-empty'
            )
        ], className='dataset-block comparison-card')]

    grouped = _group_comparison_files(files)

    # Use stored control values if available, otherwise use defaults
    stored_scalar = comparison_controls.get('scalar') if comparison_controls else None
    stored_range_min = comparison_controls.get('range_min') if comparison_controls else None
    stored_range_max = comparison_controls.get('range_max') if comparison_controls else None
    stored_palette = comparison_controls.get('palette') if comparison_controls else None
    stored_full_scale = comparison_controls.get('full_scale') if comparison_controls else False
    stored_slider_range = comparison_controls.get('slider_range') if comparison_controls else None

    # Get default settings first
    settings, scalar_options, palette_options = _comparison_settings(panels)

    # Override with stored values if available
    if stored_scalar:
        settings, scalar_options, palette_options = _comparison_settings(
            panels,
            scalar_value=stored_scalar,
            range_min=stored_range_min,
            range_max=stored_range_max,
            palette_value=stored_palette,
            full_scale=stored_full_scale,
            slider_range=stored_slider_range
        )

    slider_min_default, slider_max_default = _comparison_range_defaults(panels, settings['scalar'])
    if slider_min_default is None or slider_max_default is None:
        slider_min_default, slider_max_default = 0.0, 1.0
    slider_value_min = settings['range_min'] if settings['range_min'] is not None else slider_min_default
    slider_value_max = settings['range_max'] if settings['range_max'] is not None else slider_max_default

    controls_layout = html.Div([
        html.Div([
            html.Label([
                html.Span("S", className="label-icon"),
                "Field"
            ], className='field-label grid-label'),
            dcc.Dropdown(
                id='comparison-heatmap-field',
                options=scalar_options,
                value=settings['scalar'],
                clearable=False,
                searchable=True,
                className='dropdown-wrapper'
            ),
            html.Label([
                html.Img(src='/assets/color-scale.png', className="label-img"),
                "Palette"
            ], className='field-label grid-label'),
            dcc.Dropdown(
                id='comparison-heatmap-palette',
                options=palette_options,
                value=settings['palette'],
                clearable=False,
                searchable=True,
                className='dropdown-wrapper'
            )
        ], className='comparison-control-row comparison-palette-group'),


        html.Div([
            html.Label([
                html.Img(src='/assets/bar-chart.png', className="label-img"),
                "Range"
            ], className='field-label grid-label'),
            html.Div([
                dcc.Input(
                    id='comparison-heatmap-range-min',
                    type='number',
                    value=settings['range_min'],
                    step='any',
                    placeholder='Min',
                    className='comparison-range-input'
                ),
                dcc.Input(
                    id='comparison-heatmap-range-max',
                    type='number',
                    value=settings['range_max'],
                    step='any',
                    placeholder='Max',
                    className='comparison-range-input'
                ),
                html.Button(
                    html.Img(src='/assets/Reset.png', alt='Reset range', className='btn-icon'),
                    id='comparison-heatmap-reset',
                    n_clicks=0,
                    className='btn btn-danger reset-btn',
                    title='Reset range'
                )
            ], className='comparison-range-row'),

                html.Div([
                    dcc.RangeSlider(
                        id='comparison-heatmap-range-slider',
                        min=slider_min_default,
                        max=slider_max_default,
                        value=[slider_value_min, slider_value_max],
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className='comparison-range-slider'
                    )
                ], className='comparison-range-slider-row'),
            dmc.Switch(
                id='comparison-heatmap-full-scale',
                label="Full Scale",
                checked=settings['full_scale'],
                labelPosition="right",
                size="xs",
                radius="xs",
                color="#c50623",
                withThumbIndicator=True,
            )

        ], className='comparison-control-row comparison-range-group'),
    ], className='comparison-controls-grid')

    range_selector_store = dcc.Store(
        id='comparison-range-selection',
        data={'click_count': 0, 'first_click': None},
    )

    heatmap_sections = build_comparison_heatmap_rows(panels, grouped, settings)
    comparison_block = html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Composition', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            controls_layout,
            range_selector_store,
            html.Div(heatmap_sections, id='comparison-heatmap-rows', className='comparison-heatmap-area-inner')
        ], className='comparison-heatmap-area')
    ], className='dataset-block comparison-card comparison-heatmap-panel')

    cards = [comparison_block]

    for group, file_names in grouped.items():
        for file_name in file_names:
            panel_entry = panels.get(file_name)
            if not panel_entry:
                continue
            _, panel = panel_entry
            line_scan_card = panel.build_line_scan_card()
            if line_scan_card:
                cards.append(line_scan_card)
            histogram_card = panel.build_histogram_card()
            if histogram_card:
                cards.append(histogram_card)

    for panel_entry in panels.values():
        if not panel_entry:
            continue
        _, panel = panel_entry
        cards.append(html.Div(panel.build_layout(), className='comparison-hidden-layout'))

    return [html.Div(cards, className='comparison-root')]
# ===== END SECTION 4 =====


def _make_comparison_cache_key(files, field, range_min, range_max, palette, full_scale, slider_range):
    """Create a hashable cache key from comparison settings."""
    files_tuple = tuple(sorted(files)) if files else ()
    slider_tuple = tuple(slider_range) if slider_range else ()
    return (files_tuple, field, range_min, range_max, palette, full_scale, slider_tuple)


@app.callback(
    Output('comparison-heatmap-rows', 'children'),
    Input('comparison-files-store', 'data'),
    Input('comparison-heatmap-field', 'value'),
    Input('comparison-heatmap-range-min', 'value'),
    Input('comparison-heatmap-range-max', 'value'),
    Input('comparison-heatmap-palette', 'value'),
    Input('comparison-heatmap-full-scale', 'checked'),
    Input('comparison-heatmap-range-slider', 'value'),
)
def _update_comparison_heatmaps(files, field, range_min, range_max, palette, full_scale, slider_range):
    """Update comparison heatmap rows with optimizations.

    Uses grid caching to avoid re-interpolation when only range/palette changes.
    Only rebuilds heatmaps if settings actually changed (avoids rebuild on tab switches).
    """
    panels = get_comparison_panels(files or [])
    if not panels:
        return []

    # Create cache key from current settings
    cache_key = _make_comparison_cache_key(files, field, range_min, range_max, palette, full_scale, slider_range)

    # Check if settings haven't changed - return cached rows
    if comparison_heatmap_rows_cache['settings_key'] == cache_key and comparison_heatmap_rows_cache['rows'] is not None:
        return comparison_heatmap_rows_cache['rows']

    # Settings changed, need to rebuild
    grouped = _group_comparison_files(files or [])

    # For palette-only or range-only changes, the grid data is cached
    # so we'll get instant updates from _comparison_heatmap_data
    settings, _, _ = _comparison_settings(
        panels, field, range_min, range_max, palette, full_scale, slider_range=slider_range
    )
    rows = build_comparison_heatmap_rows(panels, grouped, settings)

    # Cache the rendered rows and settings key for next call
    comparison_heatmap_rows_cache['settings_key'] = cache_key
    comparison_heatmap_rows_cache['rows'] = rows

    return rows


@app.callback(
    Output('comparison-heatmap-range-min', 'value'),
    Output('comparison-heatmap-range-max', 'value'),
    Output('comparison-range-selection', 'data'),
    Output('comparison-heatmap-range-slider', 'value'),
    Input('comparison-heatmap-reset', 'n_clicks'),
    Input({'type': 'comparison-graph', 'file': ALL}, 'clickData'),
    Input('comparison-heatmap-range-slider', 'value'),
    State('comparison-heatmap-field', 'value'),
    State('comparison-files-store', 'data'),
    State('comparison-range-selection', 'data'),
    State('comparison-heatmap-range-min', 'value'),
    State('comparison-heatmap-range-max', 'value'),
    prevent_initial_call=True
)
def _update_comparison_range(reset_clicks, clicks, slider_values, field, files, store_data, current_min, current_max):
    triggered = ctx.triggered_id
    if triggered == 'comparison-heatmap-reset':
        if not files:
            raise PreventUpdate
        panels = get_comparison_panels(files)
        if not panels:
            raise PreventUpdate
        min_val, max_val = _comparison_range_defaults(panels, field)
        if min_val is None or max_val is None:
            raise PreventUpdate
        return min_val, max_val, {'click_count': 0, 'first_click': None}, [min_val, max_val]
    if isinstance(triggered, dict):
        triggered_value = ctx.triggered[0]['value']
        if not triggered_value or 'points' not in triggered_value or not triggered_value['points']:
            raise PreventUpdate
        try:
            point = triggered_value['points'][0]
        except (IndexError, KeyError):
            raise PreventUpdate
        z_val = point.get('z')
        if z_val is None:
            raise PreventUpdate
        try:
            z_val = float(z_val)
        except (TypeError, ValueError):
            raise PreventUpdate
        store = store_data or {'click_count': 0, 'first_click': None}
        click_count = store.get('click_count', 0)
        first_click = store.get('first_click')
        if click_count == 0 or first_click is None:
            return current_min, current_max, {'click_count': 1, 'first_click': z_val}, [current_min, current_max]
        lo, hi = sorted([first_click, z_val])
        return lo, hi, {'click_count': 0, 'first_click': None}, [lo, hi]
    if triggered == 'comparison-heatmap-range-slider':
        if not slider_values or len(slider_values) != 2:
            raise PreventUpdate
        try:
            lo = float(slider_values[0])
            hi = float(slider_values[1])
        except (TypeError, ValueError):
            raise PreventUpdate
        lo, hi = sorted([lo, hi])
        return lo, hi, {'click_count': 0, 'first_click': None}, [lo, hi]
    raise PreventUpdate
    raise PreventUpdate


@app.callback(
    Output({'type': 'comparison-graph', 'file': MATCH}, 'figure'),
    Input('comparison-heatmap-palette', 'value'),
    Input('comparison-heatmap-range-min', 'value'),
    Input('comparison-heatmap-range-max', 'value'),
    Input('comparison-heatmap-full-scale', 'checked'),
    Input('comparison-heatmap-range-slider', 'value'),
    State({'type': 'comparison-graph', 'file': MATCH}, 'id'),
    State('comparison-heatmap-field', 'value'),
    State('comparison-files-store', 'data'),
    prevent_initial_call=True
)
def _update_single_comparison_graph(palette, range_min, range_max, full_scale, slider_range,
                                     graph_id, field, files):
    """Update individual comparison graph figure without rebuilding DOM.

    This pattern-matching callback updates only the figure property of individual graphs,
    avoiding expensive DOM regeneration and leveraging grid cache for fast palette/range updates.
    """
    if not graph_id or not files:
        raise PreventUpdate

    file_name = graph_id.get('file')
    if not file_name:
        raise PreventUpdate

    # Reconstruct file_name from the safe version
    # Find the actual file name from the files list that matches
    actual_file_name = None
    safe_file_name = file_name
    for f in files:
        safe = re.sub(r'[^a-z0-9]+', '-', f.lower()).strip('-') or 'file'
        if safe == safe_file_name:
            actual_file_name = f
            break

    if not actual_file_name:
        raise PreventUpdate

    panels = get_comparison_panels(files or [])
    if actual_file_name not in panels:
        raise PreventUpdate

    _, panel = panels[actual_file_name]

    # Build settings from current state
    settings, _, _ = _comparison_settings(
        panels, field, range_min, range_max, palette, full_scale, slider_range=slider_range
    )

    # Get heatmap data (uses cache, so it's fast)
    heatmap_data = _comparison_heatmap_data(panel, actual_file_name, settings)
    if heatmap_data:
        return heatmap_data['figure']

    raise PreventUpdate


# ===== SECTION 2: Update Persistent Control Values Store =====
@app.callback(
    Output('comparison-controls-store', 'data'),
    Input('comparison-heatmap-field', 'value'),
    Input('comparison-heatmap-range-min', 'value'),
    Input('comparison-heatmap-range-max', 'value'),
    Input('comparison-heatmap-palette', 'value'),
    Input('comparison-heatmap-full-scale', 'checked'),
    Input('comparison-heatmap-range-slider', 'value'),
    prevent_initial_call=True
)
def update_comparison_controls_store(field, range_min, range_max, palette, full_scale, slider_range):
    """Save user control values to persistent store whenever they change.

    This ensures that when switching tabs, the control values are preserved
    and not reset to defaults on tab switch.
    """
    return {
        'scalar': field,
        'range_min': range_min,
        'range_max': range_max,
        'palette': palette,
        'full_scale': full_scale,
        'slider_range': slider_range
    }
# ===== END SECTION 2 =====


TAB_ORDER = [tab['id'] for tab in TAB_CONFIGS]


def get_default_active_tab():
    for tab_id in TAB_ORDER:
        if tab_datasets.get(tab_id, {}).get("panels"):
            return tab_id
    return TAB_ORDER[0] if TAB_ORDER else None


def build_tab_bar():
    icons = {
        "phase-field": "⛶",
        "composition": "⚛",
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
    default_time_val = float(default_time)
    default_bins = 15
    default_fig, default_summary = build_grain_histogram(default_time_val, default_bins)
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Distribution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
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
                        value=default_bins,
                        marks={10: '10', 25: '25', 40: '40'},
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Analysis', className='textdata-label'),
                    dcc.Checklist(
                        id='grain-dist-fit',
                        options=[{'label': 'Show Best-fit PDF', 'value': 'fit'}],
                        value=[],
                        className='hist-toggle'
                    )
                ], className='textdata-control')
            ], className='textdata-controls'),
            dcc.Graph(id='grain-dist-fig', figure=default_fig, className='textdata-plot')
        ], className='textdata-graphs'),
        dcc.Markdown(default_summary, id='grain-dist-summary', className='hist-summary', mathjax=True)
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
            dcc.Graph(id='stress-strain-fig', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_stress_hist_card():
    """Legacy PDF-based stress histogram card – hidden from UI."""
    return None


def build_strain_hist_card():
    """Legacy PDF-based strain histogram card – hidden from UI."""
    return None


def build_crss_card():
    data = CRSS_DATA
    if not data:
        return None
    series = data.get('series') or {}

    def sort_key(name):
        digits = ''.join(ch for ch in name if ch.isdigit())
        return int(digits) if digits else name

    options = [{'label': 'Average', 'value': 'Average'}]
    for name in sorted(series.keys(), key=sort_key):
        options.append({'label': name.replace('ss_', 'SS ').upper(), 'value': name})
    fig = build_crss_figure()
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('CRSS Evolution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='crss-component-select',
                    options=options,
                    value=['Average'],
                    className='crss-checklist'
                )
            ], className='textdata-control crss-control')
        ], className='textdata-controls'),
            dcc.Graph(id='crss-avg-fig', figure=fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_crss_hist_card():
    data = CRSS_DATA
    if not data:
        return None
    series = data.get('series') or {}


def build_crss_figure(selected=None):
    data = CRSS_DATA
    if not data:
        return go.Figure()
    times = data['times']
    series = data.get('series') or {}
    available = {'Average'}
    available.update({name for name, values in series.items() if values})
    if not selected:
        selected = ['Average']
    filtered = [key for key in selected if key in available]
    if not filtered:
        filtered = ['Average'] if 'Average' in available else list(available)
    selected = filtered
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
        margin=dict(l=50, r=30, t=70, b=60),
        height=320,
        template='plotly_white',
        legend=dict(
            orientation='h',
            x=0,
            xanchor='left',
            y=1.18,
            yanchor='bottom',
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
        margin=dict(l=50, r=30, t=40, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    rate_fig = go.Figure(data=rate_traces)
    rate_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=60),
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


app.layout = dmc.MantineProvider(
    html.Div(
        id='app-container',
        children=[
            dcc.Store(id='active-tab', data=INITIAL_ACTIVE_TAB),
            dcc.Store(id='comparison-files-store', data=list_comparison_files()),
            # ===== SECTION 1: Persistent Control Values Storage =====
            # This store persists user's control values across tab switches
            dcc.Store(
                id='comparison-controls-store',
                data={
                    'scalar': None,
                    'range_min': None,
                    'range_max': None,
                    'palette': None,
                    'full_scale': False,
                    'slider_range': None
                }
            ),
            # ===== END SECTION 1 =====
            html.Div([
                html.Div([
                    html.Div([
                        html.Img(src='/assets/OP_Logo_main.png', className='app-logo', alt='OP logo'),
                        html.H1([
                            "OPV",
                            html.Span("iew", className='app-title-sub'),
                        ], className='app-title')
                    ], className='top-left'),
                    html.Div([
                        html.A("Documentation", href='/docs', target='_blank', className='doc-link')
                    ], className='top-right')
            ], className='top-bar')
        ], className='app-header'),
        html.Div([
        html.Div([
            html.Div([
                html.Span(DEFAULT_VTK_FOLDER_LABEL, className='vtk-folder-badge'),
                html.Span("Folders", className='vtk-folder-heading-text')
            ], className='vtk-folder-heading'),
        dcc.Tabs(
            id='vtk-folder-tabs',
            value='current',
            className='vtk-tabs',
            children=[
            dcc.Tab(
                label=DEFAULT_VTK_FOLDER_LABEL,
                value='current',
                className='vtk-tab',
                selected_className='vtk-tab--selected'
            ),
            dcc.Tab(
                label='Comparison',
                value='comparison',
                className='vtk-tab',
                selected_className='vtk-tab--selected'
            )
            ]
        ),
        html.Div(id='vtk-folder-actions', className='vtk-folder-actions'),
        html.Div(id='vtk-upload-feedback', className='vtk-upload-feedback')
], className='vtk-folder-row')
        ], className='vtk-folder-section'),
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
)


@app.callback(
    Output('vtk-upload-feedback', 'children'),
    Output('comparison-files-store', 'data'),
    Input('vtk-file-upload', 'contents'),
    State('vtk-file-upload', 'filename'),
    State('comparison-files-store', 'data'),
    State('vtk-folder-tabs', 'value'),
    prevent_initial_call=True
)
def handle_vtk_upload(contents, filename, stored_files, active_folder):
    """Save an uploaded VTK file into the comparison directory."""
    if active_folder != 'comparison':
        raise PreventUpdate
    if not contents or not filename:
        raise PreventUpdate
    if not filename.lower().endswith(ALLOWED_VTK_EXTENSIONS):
        return (
            html.Div(
                "Only VTK files (.vtk/.vti/.vtp/.vtr/.vts) are supported.",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    try:
        _, encoded = contents.split(',', 1)
    except ValueError:
        return (
            html.Div(
                "Unable to parse the uploaded file.",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    try:
        payload = base64.b64decode(encoded)
    except Exception:
        return (
            html.Div(
                "Uploaded data could not be decoded.",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    target_dir = comparison_data_dir()
    target_path = target_dir / Path(filename).name
    reader_cache.pop(str(target_path), None)
    try:
        target_path.write_bytes(payload)
    except OSError as exc:
        return (
            html.Div(
                f"Failed to save {target_path.name}: {exc}",
                className='vtk-upload-feedback vtk-upload-feedback--error'
            ),
            stored_files or []
        )
    return (
        html.Div(
            f"Saved {target_path.name} to {target_dir}",
            className='vtk-upload-feedback vtk-upload-feedback--success'
        ),
        list_comparison_files()
    )


def _comparison_upload():
    """Return the upload button for the Comparison tab."""
    return dcc.Upload(
        id='vtk-file-upload',
        accept='.vtk,.vti,.vtp,.vtr,.vts',
        multiple=False,
        className='vtk-file-upload',
        children=html.Span("Add VTK File", className='vtk-file-upload__text')
    )


@app.callback(
    Output('vtk-folder-actions', 'children'),
    Input('vtk-folder-tabs', 'value')
)
def update_folder_actions(active_tab):
    if active_tab == 'comparison':
        return _comparison_upload()
    return None

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


# ===== SECTION 3: Render Tab with Persistent Control Values =====
@app.callback(
    Output('tab-content', 'children'),
    Output({'type': 'tab-button', 'tab': ALL}, 'className'),
    Input('active-tab', 'data'),
    Input('comparison-files-store', 'data'),
    Input('vtk-folder-tabs', 'value'),
    Input('comparison-controls-store', 'data'),
)
def render_active_tab(active_tab, comparison_files, active_folder, comparison_controls):
    if active_tab is None and active_folder != 'comparison':
        return html.Div("No tabs available", className='dataset-empty'), ['custom-tab'] * len(TAB_ORDER)
    classes = [
        'custom-tab active-tab' if tab_id == active_tab else 'custom-tab'
        for tab_id in TAB_ORDER
    ]
    if active_folder == 'comparison':
        # Pass stored control values to build_comparison_content
        return build_comparison_content(comparison_files or [], comparison_controls), classes
    children = build_tab_children(active_tab)
    return children, classes
# ===== END SECTION 3 =====


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
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
            template='plotly_white'
        )
        axis_title_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f')
        tick_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
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
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
            template='plotly_white'
        )
        line_fig.update_xaxes(title="Time Step", title_font=axis_title_font, tickfont=tick_font)
        line_fig.update_yaxes(title="Average Grain Size", title_font=axis_title_font, tickfont=tick_font)

        return main_fig, line_fig

    @app.callback(
        Output('grain-dist-fig', 'figure'),
        Output('grain-dist-summary', 'children'),
        Input('grain-dist-time', 'value'),
        Input('grain-dist-bins', 'value'),
        Input('grain-dist-fit', 'value')
    )
    def update_grain_distribution(selected_time, bins, fit_value):
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        fig, summary = build_grain_histogram(selected_time, bins, fit=fit_enabled)
        return fig, summary


if STRESS_STRAIN_DATA:

    @app.callback(
        Output('stress-strain-fig', 'figure'),
        Input('stress-components', 'value')
    )
    def update_stress_strain(components):
        data = STRESS_STRAIN_DATA
        # Convert engineering strain to percent for display
        strain = np.array(data['strain']) * 100.0
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
            margin=dict(l=50, r=30, t=90, b=60),
            height=320,
            template='plotly_white',
            legend=dict(
                orientation='h',
                x=0,
                xanchor='left',
                y=1.18,
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(24,53,104,0.15)',
                borderwidth=1
            )
        )
        fig.update_xaxes(
            title="ε_xx (%)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title="Stress (MPa)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        return fig

    @app.callback(
        Output('stress-hist-fig', 'figure'),
        Output('stress-hist-summary', 'children'),
        Input('stress-hist-component', 'value'),
        Input('stress-hist-bins', 'value'),
        Input('stress-hist-fit', 'value')
    )
    def update_stress_hist(selected_component, bins, fit_value):
        values = stress_series_values(selected_component)
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        fig, summary = build_histogram_figure(values, "Stress (MPa)", bins, fit=fit_enabled)
        return fig, summary

    @app.callback(
        Output('strain-hist-fig', 'figure'),
        Output('strain-hist-summary', 'children'),
        Input('strain-hist-component', 'value'),
        Input('strain-hist-bins', 'value'),
        Input('strain-hist-fit', 'value')
    )
    def update_strain_hist(selected_component, bins, fit_value):
        values = strain_series_values(selected_component)
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        fig, summary = build_histogram_figure(values, "Strain (%)", bins, fit=fit_enabled)
        return fig, summary


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
