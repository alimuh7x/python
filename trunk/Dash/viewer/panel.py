"""Viewer panel: layout + callbacks for each tab."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, html

from .defaults import DEFAULTS
from .layout import build_tab_layout, component_id
from .state import ViewerState, initial_state


def _formatted_range_value(value):
    if value is None:
        return value
    abs_val = abs(value)
    if abs_val == 0 or 1e-6 <= abs_val < 1e4:
        return float(f"{value:.6f}")
    return float(f"{value:.6e}")


 
def make_dynamic_colorscale(min_val, max_val, blue_cut, red_cut, colors):
    """
    Create a dynamic multi-segment colorscale based on blue and red breakpoints.

    Args:
        min_val (float): Minimum data value
        max_val (float): Maximum data value
        blue_cut (float): Blue breakpoint (user-selected minimum)
        red_cut (float): Red breakpoint (user-selected maximum)
        colors (list): 5-color palette [color0, color1, color2, color3, color4]
                       where color2 is typically white

    Returns:
        list: Plotly-compatible colorscale array with [position, color] pairs

    Logic:
        - Default (blue_cut == min_val, red_cut == max_val):
              Blue → White → Red

        - If blue_cut > min_val:
              Black → White → Blue → White → Red

        - If red_cut < max_val:
              Blue → White → Red → White → Green

        - If both conditions are true:
              Black → White → Blue → White → Red → White → Green
    """
    # Normalize positions to 0-1
    data_range = max_val - min_val
    if data_range == 0:
        # Edge case: all data is the same value
        return [[0.0, colors[2]], [1.0, colors[2]]]  # Just white

    def normalize(val):
        """Convert data value to 0-1 position."""
        normalized = (val - min_val) / data_range
        # Clamp to [0, 1] to avoid floating-point precision errors
        return max(0.0, min(1.0, normalized))

    # Determine which segments are needed
    prepend_black = blue_cut > min_val
    append_green = red_cut < max_val

    # Build colorscale segments
    colorscale = []

    if prepend_black and append_green:
        # Case 4: Black → White → Blue → White → Red → White → Green
        # Positions
        p_min = 0.0
        p_blue = normalize(blue_cut)
        p_red = normalize(red_cut)
        p_max = 1.0

        # Calculate midpoints for smooth transitions
        p_black_white = (p_min + p_blue) / 2
        p_blue_white = (p_blue + p_red) / 2
        p_red_white = (p_red + p_max) / 2

        colorscale = [
            [p_min,         colors[0]],           # Black at minimum
            [p_black_white, colors[2]],   # White midpoint
            [p_blue,        colors[1]],          # Blue at blue_cut
            [p_blue_white,  colors[2]],    # White midpoint
            [p_red,         colors[3]],           # Red at red_cut
            [p_red_white,   colors[2]],     # White midpoint
            [p_max,         colors[4]]            # Green at maximum
        ]

    elif prepend_black:
        # Case 2: Black → White → Blue → White → Red
        p_min = 0.0
        p_blue = normalize(blue_cut)
        p_red = normalize(red_cut)  # Should equal 1.0

        p_black_white = (p_min + p_blue) / 2
        p_blue_white = (p_blue + p_red) / 2

        colorscale = [
            [p_min, colors[0]],           # Black at minimum
            [p_black_white, colors[2]],   # White midpoint
            [p_blue, colors[1]],          # Blue at blue_cut
            [p_blue_white, colors[2]],    # White midpoint
            [p_red, colors[3]]            # Red at red_cut (max)
        ]

    elif append_green:
        # Case 3: Blue → White → Red → White → Green
        p_min = 0.0  # Should equal blue_cut normalized
        p_blue = normalize(blue_cut)
        p_red = normalize(red_cut)
        p_max = 1.0

        p_blue_white = (p_blue + p_red) / 2
        p_red_white = (p_red + p_max) / 2

        colorscale = [
            [p_min, colors[1]],           # Blue at minimum (blue_cut)
            [p_blue_white, colors[2]],    # White midpoint
            [p_red, colors[3]],           # Red at red_cut
            [p_red_white, colors[2]],     # White midpoint
            [p_max, colors[4]]            # Green at maximum
        ]

    else:
        # Case 1: Normal mode - Blue → White → Red
        colorscale = [
            [0.0, colors[1]],             # Blue at minimum
            [0.5, colors[2]],             # White at midpoint
            [1.0, colors[3]]              # Red at maximum
        ]

    return colorscale



class ViewerPanel:
    """Encapsulates layout + callback logic for a single viewer."""

    PALETTES = {
        # From provided presets (white centered)
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

    def build_line_scan_card(self):
        """Return line scan analysis card."""
        from viewer.layout import build_line_scan_card
        return build_line_scan_card(self.id)

    def build_histogram_card(self):
        """Return histogram analysis card."""
        from viewer.layout import build_histogram_card
        return build_histogram_card(self.id)

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
            Output(self.cid('rangeMinDisplay'), 'children'),
            Output(self.cid('rangeMaxDisplay'), 'children'),
            Output(self.cid('rangeSlider'), 'value'),
            Output(self.cid('rangeSlider'), 'min'),
            Output(self.cid('rangeSlider'), 'max'),
            Output(self.cid('colorscaleMode'), 'value'),
            Output(self.cid('lineScanDir'), 'value'),
            Output(self.cid('clickMode'), 'value'),
            Input(self.cid('scalar'), 'value'),
            Input(self.cid('palette'), 'value'),
            Input(self.cid('slice'), 'value'),
            Input(self.cid('sliceInput'), 'value'),
            Input(self.cid('reset'), 'n_clicks'),
            Input(self.cid('graph'), 'clickData'),
            Input(self.cid('rangeMin'), 'value'),
            Input(self.cid('rangeMax'), 'value'),
            Input(self.cid('rangeSlider'), 'value'),
            Input(self.cid('colorscaleMode'), 'value'),
            Input(self.cid('lineScanDir'), 'value'),
            Input(self.cid('clickMode'), 'value'),
            State(self.cid('state'), 'data'),
        )
        def _update_viewer(scalar_value, palette_value,
                           slice_value, slice_input_value, reset_clicks, click_data,
                           min_val, max_val, slider_range, colorscale_mode_value, line_scan_dir, click_mode, stored_state):
            reader = self.reader
            state_data = stored_state or {}
            default_value = self.scalar_defs[0]['value']
            fallback_value = state_data.get('scalar_key', default_value)
            if fallback_value not in self.scalar_map:
                fallback_value = default_value
            fallback_state = self._build_state(reader, self.file_path, fallback_value)

            # Ensure colorscale_mode is in state_data for backward compatibility
            if stored_state and 'colorscale_mode' not in stored_state:
                stored_state['colorscale_mode'] = 'normal'

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
                # Handle click based on current mode
                if state.click_mode == 'range':
                    state = self._handle_click(state, click_data)
                elif state.click_mode == 'linescan':
                    state = self._handle_line_scan_click(state, click_data)

            if triggered in {self.cid('rangeMin'), self.cid('rangeMax')} and min_val is not None and max_val is not None:
                lo, hi = sorted([min_val, max_val])
                state.range_min = lo
                state.range_max = hi
                state.threshold = (lo + hi) / 2
                state.clicked_message = f"Range selected: [{lo:.6f}, {hi:.6f}]"
                state.click_count = 0
                state.first_click = None

            if triggered == self.cid('rangeSlider') and slider_range is not None:
                state.range_min = slider_range[0]
                state.range_max = slider_range[1]
                state.threshold = (slider_range[0] + slider_range[1]) / 2
                state.clicked_message = f"Range selected: [{slider_range[0]:.6f}, {slider_range[1]:.6f}]"
                state.click_count = 0
                state.first_click = None

            state.palette = palette_value or fallback_state.palette
            state.colorscale_mode = colorscale_mode_value or fallback_state.colorscale_mode
            state.line_scan_direction = line_scan_dir or fallback_state.line_scan_direction
            state.click_mode = click_mode or fallback_state.click_mode

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

            # Format display values
            formatted_min = _formatted_range_value(state.range_min)
            formatted_max = _formatted_range_value(state.range_max)
            min_display = f"{formatted_min:.6f}" if formatted_min is not None else ""
            max_display = f"{formatted_max:.6f}" if formatted_max is not None else ""

            return (
                figure,
                map_title,
                click_info,
                store_data,
                state.scalar_key,
                state.slice_index,
                formatted_min,
                formatted_max,
                state.palette,
                state.slice_index,
                slice_max,
                slice_disabled,
                slice_style,
                slice_max,
                slice_disabled,
                min_display,
                max_display,
                [formatted_min, formatted_max],
                _formatted_range_value(scaled_stats['min']),
                _formatted_range_value(scaled_stats['max']),
                state.colorscale_mode,
                state.line_scan_direction,
                state.click_mode
            )

        # Line scan callback
        @self.app.callback(
            Output(self.cid('lineScanPlot'), 'figure'),
            Output(self.cid('lineScanInfo'), 'children'),
            Output(self.cid('state'), 'data', allow_duplicate=True),
            Input(self.cid('graph'), 'clickData'),
            Input(self.cid('lineScanDir'), 'value'),
            Input(self.cid('clickMode'), 'value'),
            State(self.cid('state'), 'data'),
            prevent_initial_call=True
        )
        def _update_line_scan(click_data, scan_direction, click_mode, stored_state):
            state_data = stored_state or {}
            state = ViewerState.from_dict(state_data, self.base_state)

            # Update scan direction
            state.line_scan_direction = scan_direction or 'horizontal'
            state.click_mode = click_mode or 'range'

            # Get click position if available and in linescan mode
            info_msg = ""
            if click_data and 'points' in click_data and len(click_data['points']) > 0 and state.click_mode == 'linescan':
                point = click_data['points'][0]
                if 'x' in point and 'y' in point:
                    if state.line_scan_direction == 'horizontal':
                        state.line_scan_y = point['y']
                        info_msg = f"Horizontal scan at Y = {point['y']:.2f}"
                    else:
                        state.line_scan_x = point['x']
                        info_msg = f"Vertical scan at X = {point['x']:.2f}"
            elif state.click_mode == 'linescan':
                info_msg = "Click heatmap to set line scan position"
            else:
                info_msg = "Switch to 'Line Scan' mode to set position by clicking"

            # Get current data
            descriptor = self.scalar_map.get(state.scalar_key, self.scalar_defs[0])
            X_grid, Y_grid, Z_grid, stats = self.reader.get_interpolated_slice(
                axis=state.axis,
                index=state.slice_index,
                scalar_name=descriptor['array'],
                component=descriptor.get('component'),
                resolution=self.config["interpolation_resolution"]
            )
            Z_grid = Z_grid * state.scale

            # Create line scan plot
            fig = self._build_line_scan_figure(X_grid, Y_grid, Z_grid, state)

            return fig, info_msg, state.to_dict()

        # Histogram callback
        @self.app.callback(
            Output(self.cid('histogramPlot'), 'figure'),
            Output(self.cid('histogramField'), 'options'),
            Output(self.cid('histogramField'), 'value'),
            Input(self.cid('scalar'), 'value'),
            Input(self.cid('histogramField'), 'value'),
            Input(self.cid('histogramBins'), 'value'),
            State(self.cid('state'), 'data'),
        )
        def _update_histogram(scalar_value, histogram_field, bins, stored_state):
            state_data = stored_state or {}
            state = ViewerState.from_dict(state_data, self.base_state)

            # Update histogram field options based on available scalars
            field_options = self.scalar_options

            # Set default histogram field
            if histogram_field is None or ctx.triggered_id == self.cid('scalar'):
                histogram_field = scalar_value or self.scalar_defs[0]['value']

            # Get histogram data
            descriptor = self.scalar_map.get(histogram_field, self.scalar_defs[0])
            X_grid, Y_grid, Z_grid, stats = self.reader.get_interpolated_slice(
                axis=state.axis,
                index=state.slice_index,
                scalar_name=descriptor['array'],
                component=descriptor.get('component'),
                resolution=self.config["interpolation_resolution"]
            )
            scale = descriptor.get('scale', 1.0) or 1.0
            Z_grid = Z_grid * scale

            # Create histogram
            fig = self._build_histogram_figure(Z_grid, descriptor['label'], bins or 30)

            return fig, field_options, histogram_field

    """ NOTE: Construct the heatmap figure based on the provided data and viewer state."""

    def _build_figure(self, X_grid, Y_grid, Z_grid, state: ViewerState):
        colors = self.PALETTES.get(state.palette, self.PALETTES["aqua-fire"])

        # Determine colorscale based on mode
        if state.colorscale_mode == "dynamic":
            # Dynamic mode: create multi-segment colorscale
            # Get actual data range (not clipped)
            data_min = float(np.nanmin(Z_grid))
            data_max = float(np.nanmax(Z_grid))

            # Use user-selected range as blue/red breakpoints
            blue_cut = state.range_min
            red_cut = state.range_max

            colorscale = make_dynamic_colorscale(data_min, data_max, blue_cut, red_cut, colors)

            # In dynamic mode, show full data range
            Z_grid_display = Z_grid
            zmin_display = data_min
            zmax_display = data_max
            zmid_display = state.threshold
        else:
            # Normal mode: standard 5-color gradient
            colorscale = [
                [0.0, colors[0]],
                [0.25, colors[1]],
                [0.5, colors[2]],
                [0.75, colors[3]],
                [1.0, colors[4]]
            ]
            Z_grid_display = Z_grid
            zmin_display = state.range_min
            zmax_display = state.range_max
            zmid_display = state.threshold

        template = 'plotly_white'
        bg_color = '#ffffff'
        font_family = "Montserrat, Arial, sans-serif"
        text_color = "#0f1b2b"

        fig = go.Figure(data=go.Heatmap(
            x = X_grid[0, :],
            y = Y_grid[:, 0],
            z = Z_grid_display,

            colorscale = colorscale,
            zmid       = zmid_display,           # Center the color scale around the threshold
            zmin       = zmin_display,
            zmax       = zmax_display,
            zsmooth    = self.config["zsmooth"], # 'best' | 'fast' | 'none'

            colorbar = dict(
                title = dict(
                    text = state.scalar_label,
                    side = "right",
                    font = dict(size=18, family=font_family, color=text_color)
                ),
                len           = 0.6,             # height of colorbar relative to plot (stays consistent)
                lenmode       = 'fraction',      # 'pixels' | 'fraction'
                thickness     = 14,              # Colorbar thickness
                thicknessmode = 'pixels',        # 'pixels' | 'fraction'
                x             = 0.0,            # Fixed position relative to plot area (right edge)
                y             = 0.5,             # Centered vertically
                xpad          = 0,               # Padding in pixels
                xanchor       = 'right',          # Anchor at left edge of colorbar
                yanchor       = 'middle',        # Anchor at middle
                tickmode      = "linear",        # 'auto' | 'linear' | 'array'
                tick0         = zmin_display,    # Starting tick value
                dtick         = ((zmax_display - zmin_display) / 5) if zmax_display != zmin_display else 1,
                tickfont = dict(size=14, family=font_family, color=text_color)
            ),
            hovertemplate = 'Value: %{z:.6f}<extra></extra>'))

        # Fixed figure dimensions
        fig_width = 600
        fig_height = 500
        margins = dict(t=00, b=00, l=00, r=00, autoexpand=False)

        # Calculate data aspect ratio
        data_width = X_grid[0, -1] - X_grid[0, 0] + 1
        data_height = Y_grid[-1, 0] - Y_grid[0, 0] + 1
        data_aspect = data_width / data_height if data_height > 0 else 1.0
        # -------------------------------
        # AUTO DOMAIN BASED ON ASPECT
        # -------------------------------
        
        fig_aspect  = fig_width / fig_height
        print("--------------------------------------------------------------------------")
        print("-------------------Start Printing-----------------------------------------")
        print("--------------------------------------------------------------------------")
        print(f"data_width: {data_width}")
        print(f"data_height: {data_height}")
        print(f"data_aspect: {data_aspect}")
        print(f"fig_width: {fig_width}")
        print(f"fig_height: {fig_height}")
        print(f"fig_aspect: {fig_aspect}")
        # 1. Aspect of data and figure
        
        # 2. Reserve fixed space on right for colorbar (fraction)
        cbar_space = 0.25
        right_domain = 1 - cbar_space
        
        y_min_local = 0.1
        y_max_local = 0.9
        fig.update_xaxes(domain=[0.0, right_domain])
        fig.update_yaxes(domain=[y_min_local, y_max_local])

        if(data_aspect > fig_aspect):  # PF
            colorbar_x = right_domain + 0.02
        elif data_aspect != 1.0:        # CRSS
            fig.update_xaxes(domain=[0.0, 1.0])
            real_right = self.compute_real_heatmap_edge(fig_width, fig_height, data_width, data_height,
                domain=[0.0, 1.0])
            colorbar_x = real_right
            print(f"real_right: {real_right}")
            fig.update_yaxes(domain=[0, y_max_local])
        else:                           # Mechanis
            colorbar_x = right_domain + 0.02 - y_min_local / 2.0


        fig.update_traces(colorbar=dict(
            x=colorbar_x,
            y=0.5,
            xanchor="left",
            yanchor="middle",
            len=0.6,
            thickness=14
        ))

        print(f"data_width: {data_width}, data_height: {data_height}")

        # Compute domain manually to understand plot area geometry
        left  = margins['l']
        right = margins['r']
        top   = margins['t']
        bottom= margins['b']

        x0 = left / fig_width           # 0.1   |---
        x1 = 1 - (right / fig_width)    # 0.9   ---|
        y0 = bottom / fig_height        # 0.1   |
        y1 = 1 - (top / fig_height)     # 0.9   |

        # Convert domain → pixel geometry
        plot_left   = x0 * fig_width    # 50
        plot_right  = x1 * fig_width    # 450

        plot_top    = y1 * fig_height   # 50
        plot_bottom = y0 * fig_height   # 450

        plot_width  = plot_right - plot_left # 400
        plot_height = plot_top - plot_bottom # 400

        actual_plot_width = plot_width
        actual_plot_height = plot_width / data_aspect
        vertical_padding = (plot_height - actual_plot_height) / 2
        horizontal_padding = (plot_width - actual_plot_width) / 2

        logo_size_px = 40  # Logo size in pixels
        if(horizontal_padding):
            horizontal_padding += logo_size_px / 2.0
        if(vertical_padding):
            vertical_padding += logo_size_px / 2.0
        logo_x_px = 5 + horizontal_padding # 5px from left edge
        logo_y_px = 5 + vertical_padding # At the actual plot bottom

        # Convert to paper coordinates
        logo_x_paper = logo_x_px / fig_width
        logo_y_paper = logo_y_px / fig_height
        logo_size_paper = logo_size_px / fig_width

        # print("--------------------------------------------------------------------------")
        # print("-------------------Start Printing-----------------------------------------")
        # print("--------------------------------------------------------------------------")
        # print(f"data_width: {data_width}")
        # print(f"data_height: {data_height}")
        # print(f"data_aspect: {data_aspect}")
        # print(f"fig_width: {fig_width}")
        # print(f"fig_height: {fig_height}")
        # print("--------------------------------------------------------------------------")
        # print(f"margins: {margins}")
        # print(f"left: {left}")
        # print(f"right: {right}")
        # print(f"top: {top}")
        # print(f"bottom: {bottom}")
        # print("--------------------------------------------------------------------------")
        # print(f"x0: {x0}")
        # print(f"x1: {x1}")
        # print(f"y0: {y0}")
        # print(f"y1: {y1}")
        # print("--------------------------------------------------------------------------")
        # print(f"plot_left: {plot_left}")
        # print(f"plot_right: {plot_right}")
        # print(f"plot_top: {plot_top}")
        # print(f"plot_bottom: {plot_bottom}")
        # print(f"plot_width (Area Available for plot)   : {plot_width}")
        # print(f"plot_height ( Area Available for plot) : {plot_height}")

        # print("--------------------------------------------------------------------------")
        # print(f"actual_plot_width (Actual width):  {actual_plot_width}")
        # print(f"actual_plot_height (Actual height): {actual_plot_height}")

        # print(f"vertical_padding  (Layout - Figure) :   {vertical_padding}")
        # print(f"horizontal_padding (layout - Figure): {horizontal_padding}")
        # print("--------------------------------------------------------------------------")
        # print(f"logo_size_px: {logo_size_px}")
        # print(f"logo_x_px: {logo_x_px}")
        # print(f"logo_y_px: {logo_y_px}")
        # print(f"logo_x_paper: {logo_x_paper}")
        # print(f"logo_y_paper: {logo_y_paper}")
        # print(f"logo_size_paper: {logo_size_paper}")
        # print("--------------------------------------------------------------------------")

        fig.update_layout(
            xaxis        = dict(showticklabels=False, showgrid=False, zeroline=False, title=None, scaleanchor="y", scaleratio=1),
            yaxis        = dict(showticklabels=False, showgrid=False, zeroline=False, title=None, constrain='domain'),
            template     = template,
            autosize     = False,
            height       = fig_height,
            width        = fig_width,
            paper_bgcolor= bg_color,
            hovermode    = 'closest',
            margin       = margins,
            plot_bgcolor = bg_color,
            font         = dict(family=font_family, color=text_color)
        )
       # Force actual plot margins
 
        fig.add_layout_image(
            dict(
                source  =  "/assets/OP_Logo.png",
                xref    =  "paper",
                yref    =  "paper",
                x       =   0,
                y       =   0,
                sizex   =  logo_size_paper,
                sizey   =  logo_size_paper,
                xanchor =  "left",
                yanchor =  "bottom",
                sizing  =  "contain",
                opacity =  0.95,
                layer   =  "above"
            )
        )

        # Add line scan indicator
        if state.line_scan_direction == 'horizontal' and state.line_scan_y is not None:
            # Horizontal line
            fig.add_shape(
                type="line",
                x0=X_grid[0, 0], x1=X_grid[0, -1],
                y0=state.line_scan_y, y1=state.line_scan_y,
                line=dict(color="yellow", width=2, dash="dash"),
                layer="above"
            )
        elif state.line_scan_direction == 'vertical' and state.line_scan_x is not None:
            # Vertical line
            fig.add_shape(
                type="line",
                x0=state.line_scan_x, x1=state.line_scan_x,
                y0=Y_grid[0, 0], y1=Y_grid[-1, 0],
                line=dict(color="yellow", width=2, dash="dash"),
                layer="above"
            )

        print(f"x = {logo_x_paper}, y = {logo_y_paper}")
        return fig

    def _build_map_title(self, state: ViewerState):
        base = f"{self.label}: {state.scalar_label}"
        if state.units:
            return f"{base} ({state.units})"
        return base

    def _build_click_info(self, state: ViewerState):
        if state.clicked_message:
            return _click_box(state.clicked_message, color='#0f1b2b', background='#ffffff')
        return html.Span(className='toast-empty')

    def _build_line_scan_figure(self, X_grid, Y_grid, Z_grid, state: ViewerState):
        """Build line scan plot figure."""
        font_family = "Montserrat, Arial, sans-serif"
        text_color = "#0f1b2b"

        if state.line_scan_direction == 'horizontal':
            # Horizontal scan: extract row at y position
            if state.line_scan_y is not None:
                # Find closest y index
                y_values = Y_grid[:, 0]
                y_idx = np.argmin(np.abs(y_values - state.line_scan_y))
                x_data = X_grid[y_idx, :]
                z_data = Z_grid[y_idx, :]
                x_label = "X Position"
                title = f"Horizontal Scan at Y={state.line_scan_y:.2f}"
            else:
                # Default: middle row
                y_idx = Z_grid.shape[0] // 2
                x_data = X_grid[y_idx, :]
                z_data = Z_grid[y_idx, :]
                x_label = "X Position"
                title = "Horizontal Scan (click heatmap to set position)"
        else:
            # Vertical scan: extract column at x position
            if state.line_scan_x is not None:
                # Find closest x index
                x_values = X_grid[0, :]
                x_idx = np.argmin(np.abs(x_values - state.line_scan_x))
                x_data = Y_grid[:, x_idx]
                z_data = Z_grid[:, x_idx]
                x_label = "Y Position"
                title = f"Vertical Scan at X={state.line_scan_x:.2f}"
            else:
                # Default: middle column
                x_idx = Z_grid.shape[1] // 2
                x_data = Y_grid[:, x_idx]
                z_data = Z_grid[:, x_idx]
                x_label = "Y Position"
                title = "Vertical Scan (click heatmap to set position)"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_data,
            y=z_data,
            mode='lines',
            line=dict(color='#c50623', width=2),
            name='Line Scan'
        ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=12, family=font_family, color=text_color)),
            xaxis=dict(
                title=x_label,
                title_font=dict(size=12, family=font_family, color=text_color),
                tickfont=dict(size=10, family=font_family, color=text_color)
            ),
            yaxis=dict(
                title=state.scalar_label + (f" ({state.units})" if state.units else ""),
                title_font=dict(size=12, family=font_family, color=text_color),
                tickfont=dict(size=10, family=font_family, color=text_color)
            ),
            margin=dict(l=50, r=20, t=40, b=40),
            template='plotly_white',
            showlegend=False
        )

        return fig

    def _build_histogram_figure(self, Z_grid, label, bins):
        """Build histogram figure."""
        font_family = "Montserrat, Arial, sans-serif"
        text_color = "#0f1b2b"

        # Flatten and remove NaN values
        data = Z_grid.flatten()
        data = data[~np.isnan(data)]

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=bins,
            marker_color='#183568',
            opacity=0.7,
            name='Histogram'
        ))

        fig.update_layout(
            title=dict(text=f"Distribution of {label}", font=dict(size=12, family=font_family, color=text_color)),
            xaxis=dict(
                title=label,
                title_font=dict(size=12, family=font_family, color=text_color),
                tickfont=dict(size=10, family=font_family, color=text_color)
            ),
            yaxis=dict(
                title="Frequency",
                title_font=dict(size=12, family=font_family, color=text_color),
                tickfont=dict(size=10, family=font_family, color=text_color)
            ),
            margin=dict(l=50, r=20, t=40, b=40),
            template='plotly_white',
            showlegend=False,
            bargap=0.05
        )

        return fig

    def _handle_click(self, state: ViewerState, click_data):
        """Handle clicks in range selection mode."""
        try:
            clicked_value = click_data['points'][0]['z']
        except (KeyError, IndexError):
            return state

        if state.click_count == 0:
            state.first_click = clicked_value
            state.click_count = 1
            state.clicked_message = f"First click: {clicked_value:.6f} (click again to finish range)"
        else:
            lo, hi = sorted([state.first_click, clicked_value])
            state.range_min = lo
            state.range_max = hi
            state.threshold = (lo + hi) / 2
            state.click_count = 0
            state.first_click = None
            state.clicked_message = f"Range selected: [{lo:.6f}, {hi:.6f}]"
        return state

    def _handle_line_scan_click(self, state: ViewerState, click_data):
        """Handle clicks in line scan mode."""
        try:
            point = click_data['points'][0]
            if 'x' in point and 'y' in point:
                if state.line_scan_direction == 'horizontal':
                    state.line_scan_y = point['y']
                    state.clicked_message = f"Line scan set at Y = {point['y']:.2f}"
                else:
                    state.line_scan_x = point['x']
                    state.clicked_message = f"Line scan set at X = {point['x']:.2f}"
        except (KeyError, IndexError):
            pass
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

    def compute_real_heatmap_edge(self, fig_w, fig_h, data_w, data_h, domain):
        data_aspect = data_w / data_h
        fig_aspect = fig_w / fig_h
        
        domain_left, domain_right = domain
        domain_width = domain_right - domain_left
        
        scale = data_aspect / fig_aspect
        
        real_w = domain_width * scale
        
        pad = (domain_width - real_w) / 2
        
        real_left = domain_left + pad
        real_right = real_left + real_w
        
        return real_right

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
        className='toast',
        style={'backgroundColor': background, 'color': color}
    )
