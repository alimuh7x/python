"""Viewer panel: layout + callbacks for each tab."""
from __future__ import annotations

from dataclasses import replace

import plotly.graph_objects as go
from dash import Input, Output, State, ctx, html

from .defaults import DEFAULTS
from .layout import build_tab_layout, component_id
from .state import ViewerState, initial_state


class ViewerPanel:
    """Encapsulates layout + callback logic for a single viewer."""

    PALETTES = {
        # From provided presets (white centered)
        "yellow-blue": ["#a5521a", "#fbbc3c", "#fffbe0", "#00afb8", "#00328f"],
        "blue-to-red": ["#a51717", "#fbbc3c", "#fffbe0", "#00afb8", "#00328f"],
        "spectral-lowblue": ["#5e4fa2", "#3f96b7", "#b3e0a3", "#fdd280", "#9e0142"],
        "cool-warm-extended": ["#000059", "#295698", "#fcf5e6", "#f7d5b2", "#590c36"],
        # Existing theme palettes
        "aqua-fire": ["#00328f", "#00afb8", "#fffbdf", "#ffbc3c", "#a51717"],
        "steel": ["#0b2545", "#3e5c76", "#f6f9ff", "#f4c06a", "#b3541e"],
        "ice-sunset": ["#1c3d5a", "#3aa0c8", "#ffffff", "#f9d976", "#f47068"],
    }

    def __init__(self, app, reader_factory, tab_config):
        """
        Args:
            app: Dash application instance
            reader_factory: callable returning VTKReader for a file path
            tab_config (dict): configuration for this tab
        """
        self.app = app
        overrides = tab_config.get("overrides") or {}
        self.config = {**DEFAULTS, **overrides}
        self.tab_config = tab_config
        self.id = tab_config["id"]
        self.label = tab_config["label"]
        self.reader_factory = reader_factory
        self.axis = tab_config.get("axis", self.config["axis"])
        self.axis_label = tab_config.get("axis_label", self.config["slice_axis_label"])
        self.color_defaults = (
            tab_config.get("colorA", self.config["colorA"]),
            tab_config.get("colorB", self.config["colorB"])
        )
        self.file_path = tab_config.get("file")
        self.dataset_units = tab_config.get("units")
        self.dataset_scale = tab_config.get("scale", 1.0)
        self.theme_input_id = None

        self.reader = self.reader_factory(self.file_path)
        self.scalar_defs = self._build_scalar_definitions(tab_config.get("scalars"))
        self.scalar_options = [{'label': d['label'], 'value': d['value']} for d in self.scalar_defs]
        self.scalar_map = {d['value']: d for d in self.scalar_defs}
        self.palette_options = [{'label': name.replace("-", " ").title(), 'value': name} for name in self.PALETTES.keys()]

        if not self.scalar_defs:
            raise ValueError(f"No scalar definitions available for dataset {self.id}")

        initial_scalar = self.scalar_defs[0]['value']
        self.base_state = self._build_state(self.reader, self.file_path, initial_scalar)
        self.initial_slider_max = self._max_slice_index(self.reader)
        self.initial_slider_disabled = not self.reader.is_3d

        self.register_callbacks()

    def cid(self, suffix: str) -> str:
        """Component id helper."""
        return component_id(self.id, suffix)

    def build_layout(self):
        """Return Dash layout for this tab."""
        return build_tab_layout(
            viewer_id=self.id,
            scalar_options=self.scalar_options,
            state=self.base_state,
            slider_disabled=self.initial_slider_disabled,
            slider_max=self.initial_slider_max,
            axis_label=self.axis_label,
            palette_options=self.palette_options
        )

    def register_callbacks(self):
        """Register Dash callbacks for this dataset panel."""

        @self.app.callback(
            Output(self.cid('graph'), 'figure'),
            Output(self.cid('mapTitle'), 'children'),
            Output(self.cid('clickInfo'), 'children'),
            Output(self.cid('state'), 'data'),
            Output(self.cid('scalar'), 'value'),
            Output(self.cid('slice'), 'value'),
            Output(self.cid('rangeMin'), 'value'),
            Output(self.cid('rangeMax'), 'value'),
            Output(self.cid('palette'), 'value'),
            Output(self.cid('sliceInput'), 'value'),
            Output(self.cid('slice'), 'max'),
            Output(self.cid('slice'), 'disabled'),
            Output(self.cid('sliceContainer'), 'style'),
            Output(self.cid('sliceInput'), 'max'),
            Output(self.cid('sliceInput'), 'disabled'),
            Input(self.cid('scalar'), 'value'),
            Input(self.cid('palette'), 'value'),
            Input(self.cid('slice'), 'value'),
            Input(self.cid('sliceInput'), 'value'),
            Input(self.cid('reset'), 'n_clicks'),
            Input(self.cid('rangeButton'), 'n_clicks'),
            Input(self.cid('graph'), 'clickData'),
            State(self.cid('state'), 'data'),
            State(self.cid('rangeMin'), 'value'),
            State(self.cid('rangeMax'), 'value'),
        )
        def _update_viewer(scalar_value, palette_value,
                           slice_value, slice_input_value, reset_clicks, range_clicks, click_data,
                           stored_state, min_val, max_val):
            reader = self.reader
            state_data = stored_state or {}
            default_value = self.scalar_defs[0]['value']
            fallback_value = state_data.get('scalar_key', default_value)
            if fallback_value not in self.scalar_map:
                fallback_value = default_value
            fallback_state = self._build_state(reader, self.file_path, fallback_value)

            state = ViewerState.from_dict(stored_state, fallback_state)
            triggered = ctx.triggered_id
            range_needs_reset = False

            if triggered == self.cid('reset'):
                state = replace(fallback_state)
                min_val = state.range_min
                max_val = state.range_max
                palette_value = fallback_state.palette

            if scalar_value and scalar_value in self.scalar_map and scalar_value != state.scalar_key:
                descriptor = self.scalar_map[scalar_value]
                state.scalar_key = descriptor['value']
                state.scalar_label = descriptor['label']
                state.click_count = 0
                state.first_click = None
                state.clicked_message = None
                range_needs_reset = True

            if triggered in {self.cid('slice'), self.cid('sliceInput')}:
                candidate = slice_value if triggered == self.cid('slice') else slice_input_value
                if candidate is not None:
                    state.slice_index = self._clamp_slice(int(candidate), reader)

            if triggered == self.cid('graph') and click_data:
                state = self._handle_click(state, click_data)

            if triggered == self.cid('rangeButton') and min_val is not None and max_val is not None:
                lo, hi = sorted([min_val, max_val])
                state.range_min = lo
                state.range_max = hi
                state.threshold = (lo + hi) / 2
                state.clicked_message = f"Range selected: [{lo:.4f}, {hi:.4f}]"
                state.click_count = 0
                state.first_click = None
            elif triggered == self.cid('rangeButton'):
                range_needs_reset = True

            state.palette = palette_value or fallback_state.palette

            descriptor = self.scalar_map.get(state.scalar_key, self.scalar_defs[0])
            scale = descriptor.get('scale', 1.0) or 1.0
            units = descriptor.get('units')

            X_grid, Y_grid, Z_grid, stats = reader.get_interpolated_slice(
                axis=state.axis,
                index=state.slice_index,
                scalar_name=descriptor['array'],
                component=descriptor.get('component'),
                resolution=self.config["interpolation_resolution"]
            )
            Z_grid = Z_grid * scale
            scaled_stats = {k: stats[k] * scale for k in stats}
            state.scale = scale
            state.units = units

            if range_needs_reset:
                state.range_min = scaled_stats['min']
                state.range_max = scaled_stats['max']
                state.threshold = (scaled_stats['min'] + scaled_stats['max']) / 2
                state.clicked_message = None

            slice_max = self._max_slice_index(reader)
            slice_disabled = not reader.is_3d
            slice_style = {'marginBottom': '20px'} if reader.is_3d else {'display': 'none'}

            figure = self._build_figure(X_grid, Y_grid, Z_grid, state)
            map_title = self._build_map_title(state)
            click_info = self._build_click_info(state)

            store_data = state.to_dict()
            return (
                figure,
                map_title,
                click_info,
                store_data,
                state.scalar_key,
                state.slice_index,
                state.range_min,
                state.range_max,
                state.palette,
                state.slice_index,
                slice_max,
                slice_disabled,
                slice_style,
                slice_max,
                slice_disabled
            )

    """ NOTE: Construct the heatmap figure based on the provided data and viewer state."""

    def _build_figure(self, X_grid, Y_grid, Z_grid, state: ViewerState):
        colors = self.PALETTES.get(state.palette, self.PALETTES["aqua-fire"])
        colorscale = [
            [0.0, colors[0]],
            [0.25, colors[1]],
            [0.5, colors[2]],
            [0.75, colors[3]],
            [1.0, colors[4]]
        ]

        template = 'plotly_white'
        bg_color = '#ffffff'

        fig = go.Figure(data=go.Heatmap(
            x = X_grid[0, :],
            y = Y_grid[:, 0],
            z = Z_grid,

            colorscale = colorscale,
            zmid       = state.threshold,        # Center the color scale around the threshold
            zmin       = state.range_min, 
            zmax       = state.range_max,
            zsmooth    = self.config["zsmooth"], # 'best' | 'fast' | 'none'
        
            colorbar = dict(
                    title = dict(
                        text = state.scalar_label,
                        side = "right",
                        font = dict(size=24, family="Verdana, Helvetica, Arial", color="black", weight="bold")
                    ),
                    len           = 0.6,             # height of colorbar relative to plot
                    lenmode       = 'fraction',      # 'pixels' | 'fraction'
                    thickness     = 14,              # Colorbar thickness
                    thicknessmode = 'pixels',        # 'pixels' | 'fraction'
                    x             = 0.85,             # x position in plot fraction
                    y             = 0.0,             # y position in plot fraction
                    xpad          = 0,               # Padding in pixels
                    xanchor       = 'left',          # 'left' | 'center' | 'right'
                    yanchor       = 'bottom',        # 'top' | 'middle' | 'bottom'
                    tickmode      = "linear",        # 'auto' | 'linear' | 'array'
                    tick0         = state.range_min, # Starting tick value
                    dtick         = (state.range_max - state.range_min) /
                    5 if state.range_max != state.range_min else 1,
                    tickfont = dict(size=18, family="Verdana, Helvetica, Arial", color='#2c3e50')
                ),
                hovertemplate = 'Value: %{z:.4f}<extra></extra>'))

        fig.update_layout(
            xaxis        = dict(showticklabels=False, showgrid=False, zeroline=False, title=None, scaleanchor="y", scaleratio=1),
            yaxis        = dict(showticklabels=False, showgrid=False, zeroline=False, title=None, constrain='domain'),
            template     = template,
            autosize     = False,
            height       = 400,         # Paper layout
            width        = 600,         # Paper width
            paper_bgcolor= bg_color,
            hovermode    = 'closest',
            margin       = dict(t=45, b=35, l=55, r=55, autoexpand=False), # plot margin
            plot_bgcolor = bg_color
        )

        """ NOTE: Add logo to the figure."""

        fig.add_layout_image(
            dict(
                source  =  "/assets/OP_Logo.png",
                xref    =  "x domain",
                yref    =  "y domain",
                x       =  0,
                y       =  0,
                sizex   =  0.1,
                sizey   =  0.1,
                xanchor =  "left",
                yanchor =  "bottom",
                sizing  =  "contain",
                opacity =  0.95,
                layer   =  "above"
            )
        )
        return fig

    def _build_map_title(self, state: ViewerState):
        base = f"{self.label}: {state.scalar_label}"
        if state.units:
            return f"{base} ({state.units})"
        return base

    def _build_click_info(self, state: ViewerState):
        if state.clicked_message:
            return _click_box(state.clicked_message, color='#155724', background='#d4edda')
        return html.Span()

    def _handle_click(self, state: ViewerState, click_data):
        try:
            clicked_value = click_data['points'][0]['z']
        except (KeyError, IndexError):
            return state

        if state.click_count == 0:
            state.first_click = clicked_value
            state.click_count = 1
            state.clicked_message = f"First click: {clicked_value:.4f} (click again to finish range)"
        else:
            lo, hi = sorted([state.first_click, clicked_value])
            state.range_min = lo
            state.range_max = hi
            state.threshold = (lo + hi) / 2
            state.click_count = 0
            state.first_click = None
            state.clicked_message = f"Range selected: [{lo:.4f}, {hi:.4f}]"
        return state

    def _build_state(self, reader, file_path, scalar_key):
        descriptor = self.scalar_map.get(scalar_key, self.scalar_defs[0])
        slice_index = self._default_slice_index(reader)
        _, _, _, stats = reader.get_interpolated_slice(
            axis=self.axis,
            index=slice_index,
            scalar_name=descriptor['array'],
            component=descriptor.get('component'),
            resolution=self.config["interpolation_resolution"]
        )
        scale = descriptor.get('scale', 1.0) or 1.0
        scaled_stats = {k: stats[k] * scale for k in stats}
        return initial_state(
            scalar_key=descriptor['value'],
            scalar_label=descriptor['label'],
            axis=self.axis,
            slice_index=slice_index,
            stats=scaled_stats,
            colorA=self.color_defaults[0],
            colorB=self.color_defaults[1],
            palette=self.palette_options[0]['value'] if self.palette_options else "aqua-fire",
            file_path=file_path,
            scale=scale,
            units=descriptor.get('units')
        )

    def _default_slice_index(self, reader):
        if not reader.is_3d:
            return 0
        axis_idx = {"x": 0, "y": 1, "z": 2}[self.axis]
        return reader.dimensions[axis_idx] // 2

    def _max_slice_index(self, reader):
        if not reader.is_3d:
            return 0
        axis_idx = {"x": 0, "y": 1, "z": 2}[self.axis]
        return reader.dimensions[axis_idx] - 1

    def _clamp_slice(self, value, reader):
        max_idx = self._max_slice_index(reader)
        return max(0, min(max_idx, value))

    def _build_scalar_definitions(self, scalar_specs):
        available = set(self.reader.scalar_fields)
        definitions = []
        default_scale = self.dataset_scale or 1.0
        default_units = self.dataset_units

        if scalar_specs:
            for spec in scalar_specs:
                array_name = spec.get('array') or spec.get('name') or spec.get('label')
                if not array_name or array_name not in available:
                    continue
                component = spec.get('component')
                label = spec.get('label') or (f"{array_name} [{component}]" if component is not None else array_name)
                value = spec.get('value') or self._make_scalar_value(array_name, component)
                definitions.append({
                    'label': label,
                    'value': value,
                    'array': array_name,
                    'component': component,
                    'scale': spec.get('scale', default_scale),
                    'units': spec.get('units', default_units)
                })

        if not definitions:
            for array_name in available:
                definitions.append({
                    'label': array_name,
                    'value': self._make_scalar_value(array_name, None),
                    'array': array_name,
                    'component': None,
                    'scale': default_scale,
                    'units': default_units
                })

        return definitions

    def _make_scalar_value(self, array_name, component):
        return f"{array_name}__c{component}" if component is not None else array_name


def _click_box(message, color, background):
    return html.Div(
        message,
        style={'backgroundColor': background, 'color': color, 'padding': '10px', 'borderRadius': '5px', 'fontWeight': 'bold'}
    )
