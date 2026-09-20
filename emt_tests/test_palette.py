"""
Tests for emt_ui/palette.py - the theme colours and the semantic row tag.
"""
import pytest

from emt_ui import palette
from emt_models.system import StarSystem


def system(state, power="Felicia Winters", progress=0.5, conflict=None):
    """A StarSystem in `state` at `progress` (0.0 - 1.0 control progress)."""
    entry = {
        "StarSystem": "Test",
        "PowerplayState": state,
        "ControllingPower": power,
        "Powers": [power] if power != "no power" else [],
        "PowerplayStateControlProgress": progress,
        "PowerplayStateReinforcement": 0,
        "PowerplayStateUndermining": 0,
    }
    if conflict is not None:
        entry["PowerplayConflictProgress"] = conflict
    built = StarSystem()
    built.from_dict(entry)
    return built


class TestTagFor:
    def test_no_power_is_neutral(self):
        assert palette.tag_for(system("Exploited", power="no power")) == 'neutral'

    def test_below_20_percent_is_danger(self):
        assert palette.tag_for(system("Fortified", progress=0.0698)) == 'danger'

    def test_20_percent_is_safe(self):
        assert palette.tag_for(system("Fortified", progress=0.20)) == 'safe'

    def test_mid_band_is_safe(self):
        assert palette.tag_for(system("Fortified", progress=0.6407)) == 'safe'

    def test_at_80_percent_a_fortified_is_warning(self):
        assert palette.tag_for(system("Fortified", progress=0.80)) == 'warning'

    def test_at_80_percent_a_stronghold_is_safe(self):
        assert palette.tag_for(system("Stronghold", progress=0.80)) == 'safe'

    def test_a_low_stronghold_is_still_danger(self):
        # The band check runs before the Stronghold exception, so a Stronghold
        # under 20 % reads red - Scorpii Sector MC-V a2-3 at 6.98 %.
        assert palette.tag_for(system("Stronghold", progress=0.0698)) == 'danger'

    def test_over_100_percent_rolls_into_the_next_band(self):
        # 130 % - 100 = 30 -> safe, not warning.
        assert palette.tag_for(system("Fortified", progress=1.30)) == 'safe'

    def test_a_stronghold_over_100_percent_is_not_rolled_over(self):
        assert palette.tag_for(system("Stronghold", progress=1.30)) == 'safe'

    def test_every_tag_it_returns_is_in_TAGS(self):
        for state in ("Exploited", "Fortified", "Stronghold", "Unoccupied"):
            for progress in (0.0, 0.1, 0.5, 0.9, 1.5):
                assert palette.tag_for(system(state, progress=progress)) in palette.TAGS


class TestRowTag:
    def test_even_rows_take_the_base_tag(self):
        assert palette.row_tag(system("Fortified", progress=0.5), 0) == 'safe'

    def test_odd_rows_take_the_alt(self):
        assert palette.row_tag(system("Fortified", progress=0.5), 1) == 'safe_alt'

    def test_every_alt_exists(self):
        for tag in ('danger', 'safe', 'warning', 'neutral'):
            assert f"{tag}_alt" in palette.TAGS


class TestTags:
    def test_eight_tags(self):
        assert len(palette.TAGS) == 8

    def test_each_is_a_background_and_a_foreground(self):
        for background, foreground in palette.TAGS.values():
            assert background.startswith('#') and len(background) == 7
            assert foreground.startswith('#')


class TestBrightness:
    def test_lightening_black_moves_towards_white(self):
        # 255 * 0.19999999999999996 truncates to 50, not 51.
        assert palette.adjust_color_brightness('#000000', 1.2) == '#323232'

    def test_darkening_halves_each_channel(self):
        assert palette.adjust_color_brightness('#808080', 0.5) == '#404040'

    def test_lightening_white_stays_white(self):
        assert palette.adjust_color_brightness('#ffffff', 2.0) == '#ffffff'

    def test_a_leading_hash_is_optional(self):
        assert palette.adjust_color_brightness('808080', 0.5) == '#404040'


class TestButtonBg:
    def test_dark_theme_lightens(self):
        # 1.2, not 1.4: #ff8c00 on #666666 is 2.46:1, on #323232 it is 5.50:1.
        assert palette.get_button_bg('#000000') == '#323232'

    def test_light_theme_darkens(self):
        assert palette.luminance(palette.get_button_bg('#ffffff')) < 1.0


class TestContrast:
    """Every foreground the window draws, on the background it draws it on.

    The bug this class exists for: colors['button_bg'] was used as the text
    colour for every muted line. On EDMC's black that is #323232 on #000000,
    1.6:1 - dark grey on black.
    """

    # (background, foreground) as EDMC supplies them: its dark theme, its light
    # theme, and a custom one. The foreground is the theme's, not ours - what
    # is tested is that the surfaces the palette derives keep it readable.
    THEMES = (
        ('#000000', '#ff8c00'),     # EDMC dark
        ('#ffffff', '#000000'),     # EDMC light
        ('#202830', '#e8f2ff'),     # a custom theme
    )

    def colors(self, background, foreground):
        """What get_theme_colors() would return for that theme."""
        is_dark = palette.luminance(background) < 0.5
        return {
            'bg': background,
            'fg': foreground,
            'highlight': foreground,
            'muted': palette.get_muted(background),
            'button_bg': palette.get_button_bg(background),
            'table_row_even': background,
            'table_row_odd': palette.adjust_color_brightness(
                background, 1.2 if is_dark else 0.92),
        }

    @pytest.mark.parametrize("theme", THEMES)
    @pytest.mark.parametrize("pair", [
        ('fg', 'bg'), ('fg', 'button_bg'), ('fg', 'table_row_even'),
        ('fg', 'table_row_odd'), ('muted', 'bg'), ('highlight', 'bg'),
    ])
    def test_every_pair_the_window_draws(self, theme, pair):
        colors = self.colors(*theme)
        foreground, surface = pair
        ratio = palette.contrast(colors[foreground], colors[surface])
        assert ratio >= palette.MIN_CONTRAST, (
            f"{foreground} {colors[foreground]} on {surface} "
            f"{colors[surface]} is {ratio:.2f}:1"
        )

    @pytest.mark.parametrize("tag", sorted(palette.TAGS))
    def test_every_tag_carries_its_own_text(self, tag):
        background, foreground = palette.TAGS[tag]
        # '#fff' is the short form tkinter takes; expand it to measure.
        if len(foreground) == 4:
            foreground = '#' + ''.join(c * 2 for c in foreground[1:])
        ratio = palette.contrast(foreground, background)
        assert ratio >= palette.MIN_CONTRAST, f"{tag} is {ratio:.2f}:1"

    def test_the_muted_grey_is_not_the_button_fill(self):
        assert palette.get_muted('#000000') != palette.get_button_bg('#000000')

    def test_the_old_mistake_would_have_been_caught(self):
        assert palette.contrast(palette.get_button_bg('#000000'), '#000000') < 2.0

    def test_the_stripes_are_different_enough_to_see(self):
        colors = self.colors('#000000', '#ff8c00')
        ratio = palette.contrast(colors['table_row_even'], colors['table_row_odd'])
        assert ratio > 1.2


class TestContrastMaths:
    def test_black_on_white_is_the_maximum(self):
        assert palette.contrast('#000000', '#ffffff') == pytest.approx(21.0, abs=0.01)

    def test_a_colour_on_itself_is_one(self):
        assert palette.contrast('#ff8c00', '#ff8c00') == pytest.approx(1.0)

    def test_the_order_does_not_matter(self):
        assert (palette.contrast('#ff8c00', '#000000')
                == palette.contrast('#000000', '#ff8c00'))

    def test_relative_luminance_endpoints(self):
        assert palette.relative_luminance('#000000') == pytest.approx(0.0)
        assert palette.relative_luminance('#ffffff') == pytest.approx(1.0)


class TestThemeColors:
    def test_falls_back_outside_edmc(self):
        # The test run has no theme module, so this is the fallback path.
        colors = palette.get_theme_colors()
        assert set(colors) == set(palette.FALLBACK)

    def test_the_fallback_is_copied_not_shared(self):
        colors = palette.get_theme_colors()
        colors['bg'] = '#123456'
        assert palette.FALLBACK['bg'] == '#000000'

    def test_luminance_of_black_and_white(self):
        assert palette.luminance('#000000') == pytest.approx(0.0)
        assert palette.luminance('#ffffff') == pytest.approx(1.0)
