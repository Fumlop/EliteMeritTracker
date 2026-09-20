"""Colours for the plugin's windows, and the row tag a system gets.

Two layers:

1. The theme layer - whatever EDMC is set to, plus the shades derived from it.
   get_theme_colors() is the only reader of theme.current.
2. The semantic layer - TAGS, eight fixed colours saying how a system is doing.
   Independent of the theme on purpose: red is red on any background.

tkinter and EDMC's theme are imported inside get_theme_colors(), not at module
level, so this module imports in a bare interpreter and the tag logic can be
tested without a display. Tests in emt_tests/test_palette.py.
"""

# Row background and foreground per tag. The _alt of each is the zebra stripe:
# every other row takes it so two systems in the same band stay apart.
TAGS = {
    'danger':      ('#a01010', '#fff'),
    'danger_alt':  ('#701010', '#fff'),
    'safe':        ('#107010', '#fff'),
    'safe_alt':    ('#105010', '#fff'),
    # Was #d07000, which is 3.50:1 under white text - under the 4.5 floor and
    # the only tag of the eight that was. Darkened the least that clears it,
    # hue kept: 4.58:1.
    'warning':     ('#b36000', '#fff'),
    'warning_alt': ('#a05000', '#fff'),
    'neutral':     ('#606060', '#fff'),
    'neutral_alt': ('#404040', '#fff'),
}

# Control progress in percent. Below DANGER the system is barely held; at or
# above WARNING a non-Stronghold is close to tipping.
BAND_DANGER = 20.0
BAND_WARNING = 80.0

# Used when EDMC's theme cannot be read - outside EDMC, or during a reload.
FALLBACK = {
    'bg': '#000000',
    'fg': '#ff8c00',
    'active_bg': '#000000',
    'active_fg': '#ff8c00',
    'highlight': '#ff8c00',
    'muted': '#a5a5a5',
    'button_bg': '#323232',
    'table_row_even': '#000000',
    'table_row_odd': '#323232',
}

def tag_for(system):
    """Return the base tag name for a system: one key of TAGS without _alt.

    Args:
        system: A StarSystem.

    Returns:
        'danger', 'safe', 'warning' or 'neutral'.
    """
    if system.ControllingPower == "no power":
        return 'neutral'

    progress = system.getSystemProgressNumber()
    state_text = system.getSystemStateText()
    # Past 100 % a control system has rolled over into the next band; a
    # Stronghold is measured on the raw number instead.
    display = progress - 100 if progress > 100 and state_text != "Stronghold" else progress

    if 0 <= display < BAND_DANGER:
        return 'danger'
    if BAND_DANGER <= display < BAND_WARNING:
        return 'safe'
    if display >= BAND_WARNING:
        return 'safe' if state_text == "Stronghold" else 'warning'
    # Negative progress: nothing meaningful to colour.
    return 'neutral'


def row_tag(system, row_index):
    """Return the tag for a system on row `row_index`, zebra stripe included."""
    base = tag_for(system)
    return base if row_index % 2 == 0 else f"{base}_alt"


def adjust_color_brightness(hex_color, factor):
    """Lighten or darken a colour.

    Args:
        hex_color: '#rrggbb'.
        factor: > 1 lightens towards white, < 1 darkens towards black.

    Returns:
        '#rrggbb'.
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    if factor > 1:
        r = min(255, int(r + (255 - r) * (factor - 1)))
        g = min(255, int(g + (255 - g) * (factor - 1)))
        b = min(255, int(b + (255 - b) * (factor - 1)))
    else:
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))

    return f'#{r:02x}{g:02x}{b:02x}'


def luminance(hex_color):
    """Perceived brightness of '#rrggbb' as 0.0 - 1.0.

    The cheap weighted average, used only to decide dark theme from light.
    Whether a pair can actually be read is measured by the WCAG formula in
    emt_tests/test_palette.py, which is where the only caller is.
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def get_muted(bg_color):
    """A secondary text colour that is still readable on `bg_color`.

    Text, not a surface: `button_bg` is a button's fill and sits far too close
    to the background to be read as a label on it - #323232 on EDMC's black is
    1.6:1. This lands at 8.5:1 on black and 4.8:1 on white.
    """
    if luminance(bg_color) < 0.5:
        return adjust_color_brightness(bg_color, 1.65)
    return adjust_color_brightness(bg_color, 0.45)


def get_button_bg(bg_color):
    """Return a button background that stands off the window background.

    Lightened on a dark theme, darkened on a light one. 1.2 rather than 1.4 on
    dark: on EDMC's black, 1.4 gives #666666 and the #ff8c00 label on it
    measures 2.46:1. 1.2 gives #323232 and 5.50:1, over the 4.5:1 floor.
    """
    if luminance(bg_color) < 0.5:
        return adjust_color_brightness(bg_color, 1.2)
    return adjust_color_brightness(bg_color, 0.85)


def get_theme_colors():
    """Return the current EDMC theme colours, with FALLBACK on any failure.

    The only reader of theme.current in the plugin. Imported here rather than
    at module level so this module loads outside EDMC.

    Returns:
        dict with the keys of FALLBACK.
    """
    try:
        from theme import theme                   # EDMC

        bg = theme.current.get('background', '#000000')
        is_dark = luminance(bg) < 0.5
        return {
            'bg': bg,
            'fg': theme.current.get('foreground', '#ff8c00'),
            'active_bg': theme.current.get('activebackground', '#000000'),
            'active_fg': theme.current.get('activeforeground', '#ff8c00'),
            'highlight': theme.current.get('highlight', '#ff8c00'),
            'muted': get_muted(bg),
            'button_bg': get_button_bg(bg),
            # The stripes stay close to the background. EDMC's foreground is
            # #ff8c00, whose own luminance is 0.40: anything lighter than about
            # #3b3b3b behind it drops under 4.5:1.
            'table_row_even': bg,
            'table_row_odd': adjust_color_brightness(bg, 1.2 if is_dark else 0.92),
        }
    except Exception:
        return dict(FALLBACK)
