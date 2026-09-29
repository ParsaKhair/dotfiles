#!/usr/bin/python3
"""A short-lived, single-instance volume indicator for the layer shell."""

import math
import sys

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gio, GLib, Gtk, GtkLayerShell


class VolumeOSD(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.waybar.VolumeOSD",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None
        self.timeout = None
        self.level = 0
        self.display_level = 0.0
        self.tick_id = None
        self.muted = False

    def do_command_line(self, command_line):
        args = command_line.get_arguments()
        try:
            level = max(0, min(100, int(args[1])))
            muted = args[2] == "yes"
        except (IndexError, ValueError):
            return 1
        self.level = 0 if muted else level
        self.muted = muted
        if self.window is None:
            self.display_level = self.level
            self.build()
        self.area.get_accessible().set_name(
            "Muted" if muted else f"Volume {self.level}%")
        self.window.show_all()
        if self.tick_id is None:
            self.last_frame = GLib.get_monotonic_time()
            self.tick_id = self.area.add_tick_callback(self.animate)
        if self.timeout is not None:
            GLib.source_remove(self.timeout)
        self.timeout = GLib.timeout_add(1600, self.dismiss)
        return 0

    def animate(self, area, clock):
        now = clock.get_frame_time()
        elapsed = max(0, now - self.last_frame)
        self.last_frame = now
        # Follow the latest target without restarting on repeated key presses.
        self.display_level += (self.level - self.display_level) * -math.expm1(-elapsed / 35_000)
        settled = abs(self.level - self.display_level) < 0.05
        if settled:
            self.display_level = self.level
        area.queue_draw()
        if settled:
            self.tick_id = None
            return False
        return True

    def build(self):
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Volume indicator")
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        visual = self.window.get_screen().get_rgba_visual()
        if visual:
            self.window.set_visual(visual)
        style = Gtk.CssProvider()
        style.load_from_data(b"window { background: transparent; box-shadow: none; }")
        self.window.get_style_context().add_provider(
            style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        GtkLayerShell.init_for_window(self.window)
        GtkLayerShell.set_namespace(self.window, "volume-osd")
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self.window, edge, True)
            GtkLayerShell.set_margin(self.window, edge, 4)
        GtkLayerShell.set_exclusive_zone(self.window, 0)
        GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.NONE)
        self.window.connect("realize", lambda window:
                            window.get_window().input_shape_combine_region(cairo.Region(), 0, 0))
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(168, 28)
        self.area.connect("draw", self.draw)
        self.window.add(self.area)

    @staticmethod
    def outline(ctx, width, height, inset=0):
        radius = min(width, height) / 2
        ctx.new_sub_path()
        for x, y, start in ((width - radius, radius, -90),
                            (width - radius, height - radius, 0),
                            (radius, height - radius, 90),
                            (radius, radius, 180)):
            ctx.arc(x + inset, y + inset, radius, math.radians(start), math.radians(start + 90))
        ctx.close_path()

    def speaker(self, ctx):
        ctx.move_to(10, 11)
        ctx.line_to(14, 11)
        ctx.line_to(19, 7)
        ctx.line_to(19, 21)
        ctx.line_to(14, 17)
        ctx.line_to(10, 17)
        ctx.close_path()
        ctx.fill()
        ctx.set_line_width(1.5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        if self.muted:
            ctx.move_to(23, 11)
            ctx.line_to(29, 17)
            ctx.move_to(29, 11)
            ctx.line_to(23, 17)
            ctx.stroke()
        elif self.level:
            for radius in ((5, 9) if self.level > 50 else (5,)):
                ctx.new_sub_path()
                ctx.arc(19, 14, radius, -0.8, 0.8)
                ctx.stroke()

    def draw(self, area, ctx):
        width, height = area.get_allocated_width(), area.get_allocated_height()
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        self.outline(ctx, width - 1, height - 1, 0.5)
        ctx.set_source_rgba(60 / 255, 56 / 255, 54 / 255, 0.96)
        ctx.fill()
        ctx.save()
        self.outline(ctx, width - 1, height - 1, 0.5)
        ctx.clip()
        filled = (width - 1) * self.display_level / 100
        if filled > 0:
            self.outline(ctx, filled, height - 1, 0.5)
            ctx.set_source_rgb(213 / 255, 196 / 255, 161 / 255)
            ctx.fill()
        ctx.set_source_rgb(235 / 255, 219 / 255, 178 / 255)
        self.speaker(ctx)
        if filled > 0:
            ctx.save()
            self.outline(ctx, filled, height - 1, 0.5)
            ctx.clip()
            ctx.set_source_rgb(40 / 255, 40 / 255, 40 / 255)
            self.speaker(ctx)
            ctx.restore()
        ctx.restore()
        self.outline(ctx, width - 1, height - 1, 0.5)
        ctx.set_source_rgb(80 / 255, 73 / 255, 69 / 255)
        ctx.set_line_width(1)
        ctx.stroke()
        ctx.restore()
        return False

    def dismiss(self):
        self.timeout = None
        if self.tick_id is not None:
            self.area.remove_tick_callback(self.tick_id)
            self.tick_id = None
        self.window.destroy()
        self.window = None
        return False


if __name__ == "__main__":
    sys.exit(VolumeOSD().run(sys.argv))
