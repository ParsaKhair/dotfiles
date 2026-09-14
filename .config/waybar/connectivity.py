#!/usr/bin/python3
"""Small Waybar popover for NetworkManager Wi-Fi and BlueZ Bluetooth."""

import os
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("NM", "1.0")
from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell, NM, Pango


BLUEZ = "org.bluez"
AGENT_PATH = "/org/waybar/ConnectivityAgent"
AGENT_XML = """
<node><interface name="org.bluez.Agent1">
  <method name="Release"/>
  <method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
  <method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
  <method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
  <method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/></method>
  <method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
  <method name="RequestAuthorization"><arg type="o" direction="in"/></method>
  <method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
  <method name="Cancel"/>
</interface></node>
"""
SEC = getattr(NM, "80211ApSecurityFlags")
ENTERPRISE = int(SEC.KEY_MGMT_802_1X) | int(SEC.KEY_MGMT_EAP_SUITE_B_192)
PERSONAL = int(SEC.KEY_MGMT_PSK) | int(SEC.KEY_MGMT_SAE)
OWE = int(SEC.KEY_MGMT_OWE) | int(SEC.KEY_MGMT_OWE_TM)


def wifi_security(ap):
    """Classify the AP without assuming every protected network uses a PSK."""
    flags = int(ap.get_flags())
    methods = int(ap.get_wpa_flags()) | int(ap.get_rsn_flags())
    if methods & ENTERPRISE:
        return "enterprise"
    if methods & PERSONAL:
        return "personal"
    if methods & OWE:
        return "open"
    if flags & int(getattr(NM, "80211ApFlags").PRIVACY) or methods:
        return "personal"  # Includes WEP and other password-based APs.
    return "open"


def ssid_text(ap):
    raw = ap.get_ssid()
    if raw is None:
        return None
    data = raw.get_data()
    return NM.utils_ssid_to_utf8(data) if data else None


def run_nmcli(args, password=None, timeout=40):
    """Pass passwords over stdin so they never appear in a process argument."""
    command = ["nmcli", "--wait", str(timeout - 5)]
    if password is not None:
        command.append("--ask")
    command.extend(args)
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    result = subprocess.run(
        command,
        input=None if password is None else password + "\n",
        text=True,
        capture_output=True,
        timeout=timeout,
        env=environment,
        check=False,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or "Connection failed.")
    return result.stdout.strip()


def saved_wifi_profiles():
    """Read saved SSIDs and UUIDs without reading any stored secrets."""
    env = os.environ.copy()
    env["LC_ALL"] = "C"

    def output(args):
        result = subprocess.run(
            ["nmcli", *args], capture_output=True, text=True,
            timeout=10, env=env, check=False,
        )
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout).strip())
        return result.stdout

    profiles = {}
    for line in output(["-t", "-f", "UUID,TYPE", "connection", "show"]).splitlines():
        uuid, _, kind = line.partition(":")
        if kind not in ("wifi", "802-11-wireless"):
            continue
        details = output([
            "-g", "802-11-wireless.ssid,802-11-wireless-security.key-mgmt",
            "connection", "show", "uuid", uuid,
        ]).splitlines()
        if not details or not details[0] or details[0] == "--":
            continue
        ssid = details[0]
        method = details[1].strip() if len(details) > 1 else ""
        security = (
            "enterprise" if method in ("wpa-eap", "wpa-eap-suite-b-192", "ieee8021x")
            else "personal" if method in ("wpa-psk", "sae", "none")
            else "open"
        )
        profiles.setdefault((ssid, security), uuid)
    return profiles


def bluez_call(bus, path, interface, method, parameters=None, timeout=15000):
    return bus.call_sync(
        BLUEZ, path, interface, method, parameters, None,
        Gio.DBusCallFlags.NONE, timeout, None,
    )


def bluez_set(bus, path, interface, prop, value):
    bluez_call(
        bus, path, "org.freedesktop.DBus.Properties", "Set",
        GLib.Variant("(ssv)", (interface, prop, GLib.Variant("b", value))),
    )


def unpack(value):
    return value.unpack() if isinstance(value, GLib.Variant) else value


def make_label(text, css_class=None, xalign=0):
    label = Gtk.Label(label=text, xalign=xalign)
    if css_class:
        label.get_style_context().add_class(css_class)
    if css_class in ("item-title", "item-subtitle"):
        label.set_max_width_chars(28)
        label.set_ellipsize(Pango.EllipsizeMode.END)
    return label


class ConnectivityWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Connectivity")
        self.set_default_size(320, 320)
        self.set_size_request(300, 300)
        self.set_decorated(False)
        self.get_style_context().add_class("connectivity-panel")
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "connectivity-panel")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 4)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 4)
        GtkLayerShell.set_exclusive_zone(self, 0)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        css = Gtk.CssProvider()
        css.load_from_path(os.path.join(os.path.dirname(__file__), "connectivity.css"))
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self.connect("key-press-event", self.on_key)
        self.connect("destroy", self.on_destroy)
        self.pool = ThreadPoolExecutor(max_workers=3)
        self.page = "wifi"
        self.nm = None
        self.saved_profiles = {}
        self.profiles_ready = False
        self.profiles_loading = False
        self.refresh_count = 0
        self.bus = None
        self.agent_id = None
        self.discovery_path = None
        self.bt_loading = False
        self.bt_objects = {}
        self.show_unnamed_devices = False
        self.pair_dialog = None
        self.build()
        GLib.timeout_add_seconds(5, self.periodic_refresh)
        GLib.idle_add(self.load_saved_profiles)

    def on_key(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def on_destroy(self, *_args):
        if self.discovery_path and self.bus:
            try:
                bluez_call(self.bus, self.discovery_path, "org.bluez.Adapter1", "StopDiscovery", timeout=2000)
            except GLib.Error:
                pass
        self.discovery_path = None
        if self.agent_id and self.bus:
            self.bus.unregister_object(self.agent_id)
        self.pool.shutdown(wait=False, cancel_futures=True)
        app = self.get_application()
        if app:
            app.window = None

    def background(self, work, done):
        future = self.pool.submit(work)

        def relay(result):
            def deliver():
                if self.get_realized():
                    try:
                        value, error = result.result(), None
                    except Exception as exc:
                        value, error = None, exc
                    done(value, error)
                return False
            GLib.idle_add(deliver)

        future.add_done_callback(relay)

    def build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.get_style_context().add_class("panel-content")
        self.add(root)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class("panel-header")
        title = make_label("Connectivity", "panel-title")
        header.pack_start(title, True, True, 0)
        close = Gtk.Button(label="×")
        close.get_style_context().add_class("icon-button")
        close.set_tooltip_text("Close")
        close.connect("clicked", lambda *_: self.close())
        header.pack_end(close, False, False, 0)
        root.pack_start(header, False, False, 0)

        segment = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        segment.get_style_context().add_class("segment")
        self.wifi_tab = Gtk.Button(label="Wi-Fi")
        self.bt_tab = Gtk.Button(label="Bluetooth")
        for button, page in ((self.wifi_tab, "wifi"), (self.bt_tab, "bluetooth")):
            button.get_style_context().add_class("segment-button")
            button.connect("clicked", lambda _button, target=page: self.select(target))
            segment.pack_start(button, True, True, 0)
        root.pack_start(segment, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(160)
        root.pack_start(self.stack, True, True, 0)
        self.wifi_page, self.wifi_rows = self.make_page("Wi-Fi", self.scan_wifi)
        self.bt_page, self.bt_rows = self.make_page("Bluetooth", self.scan_bluetooth)
        wifi_footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        wifi_footer.get_style_context().add_class("footer")
        wifi_footer.pack_start(self.action("Other Network…", self.other_network), False, False, 0)
        wifi_footer.pack_end(self.action("Profiles…", lambda: self.open_editor()), False, False, 0)
        self.wifi_page.pack_end(wifi_footer, False, False, 0)
        self.stack.add_named(self.wifi_page, "wifi")
        self.stack.add_named(self.bt_page, "bluetooth")
        self.wifi_switch = self.wifi_page.radio_switch
        self.bt_switch = self.bt_page.radio_switch
        self.wifi_scan = self.wifi_page.scan_button
        self.bt_scan = self.bt_page.scan_button
        self.wifi_switch_handler = self.wifi_switch.connect(
            "toggled", lambda button: self.toggle_wifi(button.get_active()),
        )
        self.bt_switch_handler = self.bt_switch.connect(
            "toggled", lambda button: self.toggle_bluetooth(button.get_active()),
        )

        self.status = make_label("", "status-message")
        self.status.set_line_wrap(True)
        self.status.set_no_show_all(True)
        root.pack_end(self.status, False, False, 0)

    def make_page(self, name, scan):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.get_style_context().add_class("page-controls")
        controls.pack_start(make_label(name, "section-title"), True, True, 0)
        refresh = Gtk.Button(label="↻")
        refresh.get_style_context().add_class("icon-button")
        refresh.set_tooltip_text("Scan again")
        refresh.connect("clicked", lambda *_: scan())
        controls.pack_end(refresh, False, False, 0)
        switch = Gtk.ToggleButton()
        switch.get_style_context().add_class("radio-toggle")
        knob = make_label(" ", "toggle-knob")
        switch.add(knob)
        switch.set_valign(Gtk.Align.CENTER)
        switch.set_tooltip_text(f"Turn {name} on or off")
        controls.pack_end(switch, False, False, 0)
        page.pack_start(controls, False, False, 0)
        page.radio_switch = switch
        page.scan_button = refresh

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(150)
        rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        rows.get_style_context().add_class("rows")
        scroll.add(rows)
        page.pack_start(scroll, True, True, 0)
        return page, rows

    def select(self, page):
        self.page = page
        self.stack.set_visible_child_name(page)
        for button, selected in ((self.wifi_tab, page == "wifi"), (self.bt_tab, page == "bluetooth")):
            context = button.get_style_context()
            context.add_class("selected") if selected else context.remove_class("selected")
        self.clear_status()
        if page == "wifi":
            self.refresh_wifi()
        else:
            self.refresh_bluetooth()
            self.scan_bluetooth()

    def periodic_refresh(self):
        if not self.get_realized():
            return False
        if self.page == "wifi":
            self.refresh_count += 1
            if self.refresh_count % 6 == 0:
                self.load_saved_profiles()
            self.refresh_wifi()
        else:
            self.refresh_bluetooth()
        return True

    def clear_rows(self, box):
        for child in box.get_children():
            box.remove(child)

    def notice(self, message):
        self.status.set_text(message)
        self.status.show()

    def clear_status(self):
        self.status.hide()
        self.status.set_text("")

    def section(self, box, title):
        label = make_label(title.upper(), "list-section")
        box.pack_start(label, False, False, 0)

    def empty(self, box, message):
        label = make_label(message, "empty-message")
        label.set_line_wrap(True)
        box.pack_start(label, False, False, 0)

    def action(self, title, callback):
        button = Gtk.Button(label=title)
        button.get_style_context().add_class("text-button")
        button.connect("clicked", lambda *_: callback())
        return button

    def item(self, box, icon, title, subtitle, callback=None, badge=None, trailing=None):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.get_style_context().add_class("item")
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        body.set_valign(Gtk.Align.CENTER)
        image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
        image.get_style_context().add_class("item-icon")
        image.set_valign(Gtk.Align.CENTER)
        body.pack_start(image, False, False, 0)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        texts.set_valign(Gtk.Align.CENTER)
        texts.pack_start(make_label(title, "item-title"), False, False, 0)
        texts.pack_start(make_label(subtitle, "item-subtitle"), False, False, 0)
        body.pack_start(texts, True, True, 0)
        if callback:
            button = Gtk.Button()
            button.get_style_context().add_class("item-main")
            button.add(body)
            button.connect("clicked", lambda *_: callback())
            row.pack_start(button, True, True, 0)
        else:
            row.pack_start(body, True, True, 0)
        if badge:
            badge_label = make_label(badge, "item-badge", 1)
            badge_label.set_valign(Gtk.Align.CENTER)
            row.pack_end(badge_label, False, False, 0)
        if trailing:
            trailing.get_style_context().add_class("row-action")
            row.pack_end(trailing, False, False, 0)
        box.pack_start(row, False, False, 0)
        return row

    def nm_client(self):
        if self.nm is None:
            self.nm = NM.Client.new(None)
        return self.nm

    def load_saved_profiles(self):
        if self.profiles_loading or not self.get_realized():
            return False
        self.profiles_loading = True

        def finished(profiles, error):
            self.profiles_loading = False
            if error:
                self.profiles_ready = False
                self.notice(f"Could not read saved Wi-Fi profiles: {error}")
            else:
                self.saved_profiles = profiles
                self.profiles_ready = True
                if self.page == "wifi":
                    self.refresh_wifi()

        self.background(saved_wifi_profiles, finished)
        return False

    def wifi_device(self):
        devices = [d for d in self.nm_client().get_devices() if isinstance(d, NM.DeviceWifi)]
        devices.sort(key=lambda d: d.get_state() != NM.DeviceState.ACTIVATED)
        return devices[0] if devices else None

    def refresh_wifi(self):
        box = self.wifi_rows
        self.clear_rows(box)
        try:
            client = self.nm_client()
            device = self.wifi_device()
            enabled = client.wireless_get_enabled()
            self.wifi_switch.handler_block(self.wifi_switch_handler)
            self.wifi_switch.set_active(enabled)
            self.wifi_switch.handler_unblock(self.wifi_switch_handler)
            self.wifi_switch.set_sensitive(bool(device) and client.wireless_hardware_get_enabled())
            self.wifi_scan.set_sensitive(bool(device) and enabled)
            if not device:
                self.empty(box, "No Wi-Fi adapter was found.")
                box.show_all()
                return
            if not client.wireless_hardware_get_enabled():
                self.empty(box, "Wi-Fi is disabled by a hardware switch.")
                box.show_all()
                return
            if not enabled:
                self.empty(box, "Turn on Wi-Fi to see nearby networks.")
                box.show_all()
                return

            current = device.get_active_access_point()
            current_bssid = current.get_bssid() if current else None
            groups = {}
            for ap in device.get_access_points():
                ssid = ssid_text(ap)
                if not ssid:
                    continue  # Hidden SSIDs are handled by Other Network.
                security = wifi_security(ap)
                active = ap.get_bssid() == current_bssid and device.get_state() == NM.DeviceState.ACTIVATED
                key = (ssid, security)
                if key not in groups or active or (
                    not groups[key]["active"] and ap.get_strength() > groups[key]["ap"].get_strength()
                ):
                    groups[key] = dict(
                        ap=ap, ssid=ssid, security=security, active=active,
                        profile=self.saved_profiles.get(key),
                        iface=device.get_iface(),
                    )
            networks = sorted(groups.values(), key=lambda n: (not n["active"], -n["ap"].get_strength(), n["ssid"].casefold()))
            if current and not any(n["active"] for n in networks):
                # Active hidden networks still deserve a visible status row.
                self.section(box, "Connected")
                self.item(box, "network-wireless-symbolic", "Hidden network", "Connected", badge="✓")
            for index, network in enumerate(networks):
                if index == 0 or (networks[index - 1]["active"] and not network["active"]):
                    self.section(box, "Connected" if network["active"] else "Nearby")
                self.wifi_item(box, network, device)
            if not networks and not current:
                self.empty(box, "No networks found. Try scanning again.")
            box.show_all()
        except Exception as error:
            self.wifi_switch.set_sensitive(False)
            self.wifi_scan.set_sensitive(False)
            self.empty(box, f"NetworkManager is unavailable: {error}")
            box.show_all()

    def wifi_item(self, box, network, device):
        active = network["active"]
        security = network["security"]
        profile = network["profile"]
        strength = network["ap"].get_strength()
        icon = (
            "network-wireless-signal-excellent-symbolic" if strength >= 75
            else "network-wireless-signal-good-symbolic" if strength >= 50
            else "network-wireless-signal-ok-symbolic" if strength >= 25
            else "network-wireless-signal-weak-symbolic"
        )
        if active:
            state = device.get_connectivity(socket.AF_UNSPEC)
            if state == NM.ConnectivityState.PORTAL:
                subtitle = "Sign-in required"
            elif state == NM.ConnectivityState.LIMITED:
                subtitle = "Connected · limited internet"
            else:
                subtitle = "Connected"
            self.item(box, icon, network["ssid"], subtitle, badge="✓")
            if state in (NM.ConnectivityState.PORTAL, NM.ConnectivityState.LIMITED, NM.ConnectivityState.UNKNOWN):
                box.pack_start(self.action("Open sign-in page", self.open_portal), False, False, 0)
            return
        subtitle = {
            "enterprise": "School / work sign-in",
            "personal": "Password required",
            "open": "Open network",
        }[security]
        if profile:
            subtitle = "Saved profile" + (" · school / work" if security == "enterprise" else "")
        self.item(
            box, icon, network["ssid"], subtitle,
            callback=lambda n=network: self.join_wifi(n),
        )

    def toggle_wifi(self, enabled):
        try:
            self.nm_client().wireless_set_enabled(enabled)
            GLib.timeout_add_seconds(1, self.refresh_wifi_once)
        except Exception as error:
            self.notice(f"Could not change Wi-Fi state: {error}")
        return False

    def refresh_wifi_once(self):
        self.refresh_wifi()
        return False

    def scan_wifi(self):
        try:
            device = self.wifi_device()
            if not device:
                return
            self.wifi_scan.set_sensitive(False)

            def completed(wifi, result):
                try:
                    wifi.request_scan_finish(result)
                except GLib.Error as error:
                    self.notice(f"Wi-Fi scan failed: {error.message}")
                GLib.timeout_add_seconds(2, self.refresh_wifi_once)

            device.request_scan_async(None, completed)
            GLib.timeout_add_seconds(8, self.refresh_wifi_once)
        except Exception as error:
            self.notice(f"Could not scan: {error}")

    def join_wifi(self, network):
        if not self.profiles_ready:
            self.notice("Checking saved network profiles. Try again in a moment.")
            self.load_saved_profiles()
            return
        ssid = network["ssid"]
        iface = network["iface"]
        profile = network["profile"]
        if profile:
            uuid = profile
            args = ["connection", "up", "uuid", uuid, "ifname", iface]
            self.run_wifi_command(args, on_error=lambda error: self.saved_profile_error(uuid, error))
        elif network["security"] == "enterprise":
            self.notice(f"Set up a school/work profile for “{ssid}” in the connection editor, then connect here.")
            self.open_editor(create=True)
        elif network["security"] == "personal":
            password = self.password_dialog(ssid)
            if password is not None:
                args = ["device", "wifi", "connect", ssid, "ifname", iface]
                self.run_wifi_command(args, password=password)
        else:
            args = ["device", "wifi", "connect", ssid, "ifname", iface]
            self.run_wifi_command(args)

    def saved_profile_error(self, uuid, error):
        if any(term in str(error).lower() for term in ("secret", "password", "802.1x", "authentication")):
            self.notice("This profile needs sign-in details. Opening its settings.")
            self.open_editor(uuid)

    def run_wifi_command(self, args, password=None, on_error=None):
        self.notice("Connecting…")

        def finished(_result, error):
            if error:
                self.notice(f"Could not connect: {error}")
                if on_error:
                    on_error(error)
            else:
                self.notice("Connected.")
                try:
                    self.nm_client().check_connectivity_async(None, lambda *_: self.refresh_wifi())
                except GLib.Error:
                    pass
            self.refresh_wifi()
            GLib.timeout_add_seconds(3, self.refresh_wifi_once)

        self.background(lambda: run_nmcli(args, password), finished)

    def password_dialog(self, ssid):
        dialog = Gtk.Dialog(title=f"Join {ssid}", transient_for=self, flags=Gtk.DialogFlags.MODAL)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Join", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_spacing(10)
        area.set_margin_start(18)
        area.set_margin_end(18)
        area.set_margin_top(14)
        area.set_margin_bottom(12)
        area.add(make_label("Wi-Fi password"))
        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.set_placeholder_text("Password")
        entry.set_activates_default(True)
        area.add(entry)
        dialog.show_all()
        response = dialog.run()
        value = entry.get_text() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        return value if value else None

    def other_network(self):
        dialog = Gtk.Dialog(title="Other Network", transient_for=self, flags=Gtk.DialogFlags.MODAL)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Join", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_spacing(8)
        area.set_margin_start(18)
        area.set_margin_end(18)
        area.set_margin_top(14)
        area.set_margin_bottom(12)
        name = Gtk.Entry()
        name.set_placeholder_text("Network name (SSID)")
        area.add(name)
        security = Gtk.ComboBoxText()
        for key, label in (("open", "Open"), ("personal", "Password"), ("enterprise", "School / work profile")):
            security.append(key, label)
        security.set_active_id("open")
        area.add(security)
        password = Gtk.Entry()
        password.set_placeholder_text("Password")
        password.set_visibility(False)
        password.set_no_show_all(True)
        area.add(password)
        security.connect("changed", lambda combo: password.show() if combo.get_active_id() == "personal" else password.hide())
        dialog.show_all()
        password.hide()
        response = dialog.run()
        ssid = name.get_text().strip()
        kind = security.get_active_id()
        secret = password.get_text()
        dialog.destroy()
        if response != Gtk.ResponseType.OK or not ssid:
            return
        if kind == "enterprise":
            self.notice(f"Set up “{ssid}” in the connection editor, then connect from this panel.")
            self.open_editor(create=True)
            return
        if kind == "personal" and not secret:
            self.notice("Enter a password for this network.")
            return
        device = self.wifi_device()
        if not device:
            return
        args = ["device", "wifi", "connect", ssid, "ifname", device.get_iface(), "hidden", "yes"]
        self.run_wifi_command(args, password=secret if kind == "personal" else None)

    def open_editor(self, uuid=None, create=False):
        args = ["nm-connection-editor"]
        if uuid:
            args.extend(["--edit", uuid])
        elif create:
            args.extend(["--create", "--type", "802-11-wireless"])
        try:
            subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as error:
            self.notice(f"Could not open the profile editor: {error}")

    def open_portal(self):
        try:
            Gio.AppInfo.launch_default_for_uri("http://neverssl.com/", None)
        except GLib.Error as error:
            self.notice(f"Could not open the sign-in page: {error.message}")

    def system_bus(self):
        if self.bus is None:
            self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        return self.bus

    def bluez_snapshot(self):
        bus = self.system_bus()
        result = bluez_call(bus, "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")
        objects = result.unpack()[0]
        adapters = []
        devices = []
        for path, interfaces in objects.items():
            if "org.bluez.Adapter1" in interfaces:
                props = interfaces["org.bluez.Adapter1"]
                adapters.append(dict(path=path, powered=bool(unpack(props.get("Powered")))))
            if "org.bluez.Device1" in interfaces:
                props = interfaces["org.bluez.Device1"]
                alias = unpack(props.get("Alias")) or unpack(props.get("Name")) or ""
                devices.append(dict(
                    path=path, name=alias, paired=bool(unpack(props.get("Paired"))),
                    connected=bool(unpack(props.get("Connected"))),
                    rssi=unpack(props.get("RSSI")),
                ))
        adapter = next((a for a in adapters if a["powered"]), adapters[0] if adapters else None)
        if adapter:
            devices = [d for d in devices if d["path"].startswith(adapter["path"] + "/") and d["name"]]
        return adapter, devices

    def refresh_bluetooth(self):
        if self.bt_loading:
            return
        self.bt_loading = True

        def finished(snapshot, error):
            self.bt_loading = False
            if error:
                self.clear_rows(self.bt_rows)
                self.empty(self.bt_rows, f"Bluetooth is unavailable: {error}")
                self.bt_rows.show_all()
                self.bt_switch.set_sensitive(False)
                self.bt_scan.set_sensitive(False)
            else:
                self.render_bluetooth(*snapshot)

        self.background(self.bluez_snapshot, finished)

    def render_bluetooth(self, adapter, devices):
        self.bt_adapter = adapter
        box = self.bt_rows
        self.clear_rows(box)
        self.bt_switch.handler_block(self.bt_switch_handler)
        self.bt_switch.set_active(adapter["powered"] if adapter else False)
        self.bt_switch.handler_unblock(self.bt_switch_handler)
        self.bt_switch.set_sensitive(adapter is not None)
        self.bt_scan.set_sensitive(bool(adapter and adapter["powered"]))
        if adapter is None:
            self.empty(box, "No Bluetooth adapter was found.")
        elif not adapter["powered"]:
            self.empty(box, "Turn on Bluetooth to see your devices.")
        else:
            paired = sorted((d for d in devices if d["paired"]), key=lambda d: (not d["connected"], d["name"].casefold()))
            unnamed = [
                d for d in devices
                if not d["paired"] and d["rssi"] is not None
                and re.fullmatch(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", d["name"])
            ]
            nearby = sorted(
                (
                    d for d in devices
                    if not d["paired"]
                    and d["rssi"] is not None
                    and (self.show_unnamed_devices or d not in unnamed)
                ),
                key=lambda d: (-d["rssi"], d["name"].casefold()),
            )
            if paired:
                self.section(box, "My devices")
                for device in paired:
                    self.bluetooth_item(box, device)
            self.section(box, "Nearby")
            if nearby:
                for device in nearby:
                    self.bluetooth_item(box, device)
            else:
                message = (
                    "No named devices nearby. Show unnamed devices or scan again."
                    if unnamed else "No nearby devices yet. Put a device in pairing mode and scan."
                )
                self.empty(box, message)
            if unnamed:
                label = "Hide unnamed devices" if self.show_unnamed_devices else f"Show {len(unnamed)} unnamed devices"
                box.pack_start(self.action(label, self.toggle_unnamed_devices), False, False, 0)
        box.show_all()

    def toggle_unnamed_devices(self):
        self.show_unnamed_devices = not self.show_unnamed_devices
        self.refresh_bluetooth()

    def bluetooth_item(self, box, device):
        connected = device["connected"]
        paired = device["paired"]
        subtitle = "Connected" if connected else ("Paired" if paired else "Available to pair")
        icon = "bluetooth-active-symbolic" if connected else "bluetooth-symbolic"
        badge = "✓" if connected else None
        callback = (
            (lambda d=device: self.bluetooth_method(d, "Disconnect"))
            if connected else (lambda d=device: self.bluetooth_method(d, "Connect"))
            if paired else (lambda d=device: self.pair_device(d))
        )
        self.item(box, icon, device["name"], subtitle, callback=callback, badge=badge)

    def toggle_bluetooth(self, enabled):
        try:
            adapter = getattr(self, "bt_adapter", None)
            if adapter:
                self.background(
                    lambda: bluez_set(self.system_bus(), adapter["path"], "org.bluez.Adapter1", "Powered", enabled),
                    lambda _value, error: self.bluetooth_done("Bluetooth updated.", error),
                )
        except Exception as error:
            self.notice(f"Could not change Bluetooth state: {error}")
        return False

    def scan_bluetooth(self):
        if self.page != "bluetooth":
            return

        def begin(snapshot, error):
            if error or not snapshot[0] or not snapshot[0]["powered"]:
                return
            if self.discovery_path:
                return
            path = snapshot[0]["path"]
            self.discovery_path = path
            self.bt_scan.set_sensitive(False)
            self.background(
                lambda: bluez_call(self.system_bus(), path, "org.bluez.Adapter1", "StartDiscovery"),
                lambda _value, error: self.scan_started(error),
            )

        self.background(self.bluez_snapshot, begin)

    def scan_started(self, error):
        if error:
            self.discovery_path = None
            self.notice(f"Bluetooth scan failed: {error}")
            self.bt_scan.set_sensitive(True)
            return
        GLib.timeout_add_seconds(12, self.stop_bluetooth_scan)

    def stop_bluetooth_scan(self):
        path = self.discovery_path
        self.discovery_path = None
        if path:
            self.background(
                lambda: bluez_call(self.system_bus(), path, "org.bluez.Adapter1", "StopDiscovery"),
                lambda _value, _error: self.refresh_bluetooth(),
            )
        return False

    def bluetooth_method(self, device, method):
        self.notice(f"{method}ing {device['name']}…")
        self.background(
            lambda: bluez_call(self.system_bus(), device["path"], "org.bluez.Device1", method, timeout=45000),
            lambda _value, error: self.bluetooth_done(f"{device['name']} updated.", error),
        )

    def bluetooth_done(self, success, error):
        self.notice(f"Bluetooth: {error}" if error else success)
        self.refresh_bluetooth()

    def ensure_agent(self):
        if self.agent_id:
            return
        bus = self.system_bus()
        interface = Gio.DBusNodeInfo.new_for_xml(AGENT_XML).interfaces[0]
        registration = bus.register_object(AGENT_PATH, interface, self.agent_request, None, None)
        try:
            bluez_call(
                bus, "/org/bluez", "org.bluez.AgentManager1", "RegisterAgent",
                GLib.Variant("(os)", (AGENT_PATH, "KeyboardDisplay")),
            )
        except Exception:
            bus.unregister_object(registration)
            raise
        self.agent_id = registration

    def pair_device(self, device):
        try:
            self.ensure_agent()
        except Exception as error:
            self.notice(f"Could not start Bluetooth pairing: {error}")
            return
        self.notice(f"Pairing with {device['name']}…")

        def pair():
            bus = self.system_bus()
            bluez_call(bus, device["path"], "org.bluez.Device1", "Pair", timeout=90000)
            bluez_set(bus, device["path"], "org.bluez.Device1", "Trusted", True)
            try:
                bluez_call(bus, device["path"], "org.bluez.Device1", "Connect", timeout=45000)
            except GLib.Error as error:
                if "AlreadyConnected" not in str(error):
                    raise

        self.background(pair, lambda _value, error: self.bluetooth_done(f"{device['name']} paired.", error))

    def device_name(self, path):
        for device in self.bluez_snapshot()[1]:
            if device["path"] == path:
                return device["name"]
        return "this device"

    def agent_request(self, _connection, _sender, _path, _interface, method, params, invocation):
        values = params.unpack()
        name = self.device_name(values[0]) if values and isinstance(values[0], str) else "this device"
        try:
            if method in ("Release", "Cancel"):
                if self.pair_dialog:
                    self.pair_dialog.destroy()
                    self.pair_dialog = None
                invocation.return_value(None)
            elif method in ("DisplayPinCode", "DisplayPasskey"):
                code = values[1] if method == "DisplayPinCode" else f"{values[1]:06d}"
                if self.pair_dialog:
                    self.pair_dialog.destroy()
                dialog = Gtk.MessageDialog(
                    transient_for=self, flags=Gtk.DialogFlags.MODAL,
                    message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                    text=f"Enter {code} on {name}",
                )
                dialog.connect("response", self.close_pair_dialog)
                dialog.show_all()
                self.pair_dialog = dialog
                invocation.return_value(None)
            elif method == "RequestConfirmation":
                accepted = self.confirm_pair(f"Does {values[1]:06d} match the code on {name}?")
                self.answer_void(invocation, accepted)
            elif method in ("RequestAuthorization", "AuthorizeService"):
                accepted = self.confirm_pair(f"Allow pairing with {name}?")
                self.answer_void(invocation, accepted)
            elif method in ("RequestPinCode", "RequestPasskey"):
                numeric = method == "RequestPasskey"
                answer = self.pair_input(name, numeric)
                if answer is None:
                    invocation.return_dbus_error("org.bluez.Error.Rejected", "Pairing cancelled")
                elif numeric:
                    invocation.return_value(GLib.Variant("(u)", (int(answer),)))
                else:
                    invocation.return_value(GLib.Variant("(s)", (answer,)))
            else:
                invocation.return_dbus_error("org.bluez.Error.Rejected", "Unsupported pairing request")
        except Exception as error:
            invocation.return_dbus_error("org.bluez.Error.Rejected", str(error))

    def answer_void(self, invocation, accepted):
        if accepted:
            invocation.return_value(None)
        else:
            invocation.return_dbus_error("org.bluez.Error.Rejected", "Pairing declined")

    def close_pair_dialog(self, dialog, *_args):
        dialog.destroy()
        if self.pair_dialog is dialog:
            self.pair_dialog = None

    def confirm_pair(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.NONE,
            text=message,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Pair", Gtk.ResponseType.OK)
        dialog.show_all()
        accepted = dialog.run() == Gtk.ResponseType.OK
        dialog.destroy()
        return accepted

    def pair_input(self, name, numeric):
        dialog = Gtk.Dialog(title=f"Pair with {name}", transient_for=self, flags=Gtk.DialogFlags.MODAL)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Pair", Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_margin_start(18)
        area.set_margin_end(18)
        area.set_margin_top(14)
        area.set_margin_bottom(12)
        entry = Gtk.Entry()
        entry.set_placeholder_text("6-digit passkey" if numeric else "PIN code")
        entry.set_max_length(6 if numeric else 16)
        area.add(entry)
        dialog.show_all()
        value = entry.get_text().strip() if dialog.run() == Gtk.ResponseType.OK else ""
        dialog.destroy()
        if not value or numeric and (not value.isascii() or not value.isdigit()):
            return None
        return value


class ConnectivityApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="org.waybar.ConnectivityPanel",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.window = None

    def do_command_line(self, command_line):
        args = command_line.get_arguments()
        page = "bluetooth" if len(args) > 1 and args[1] == "bluetooth" else "wifi"
        if self.window and self.window.get_visible() and self.window.page == page:
            self.window.close()
            self.window = None
        else:
            if self.window is None:
                self.window = ConnectivityWindow(self)
            self.window.show_all()
            self.window.select(page)
            self.window.present()
        return 0

    def do_activate(self):
        if self.window:
            self.window.present()


if __name__ == "__main__":
    sys.exit(ConnectivityApp().run(sys.argv))
