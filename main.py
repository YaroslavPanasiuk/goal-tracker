#!/usr/bin/env python3

import gi
import os
import os.path
from pathlib import Path
import json
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
from datetime import datetime

def seconds_to_ymdhms(seconds):
    years = seconds // (365*24*3600)
    seconds %= (365*24*3600)
    months = seconds // (30*24*3600)
    seconds %= (30*24*3600)
    days = seconds // (24*3600)
    seconds %= (24*3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    result = ""
    if years > 0:
        result += f"{int(years)}Y "
    if months > 0:
        result += f"{int(months)}M "
    if days > 0:
        result += f"{int(days)}d "
    if hours > 0:
        result += f"{int(hours)}h "
    if minutes > 0:
        result += f"{int(minutes)}min "
    if seconds > 0 or result == "":
        result += f"{int(seconds)}s"
    return result.strip()

class ProgressBarWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Goal Tracker")
        css_provider = Gtk.CssProvider()
        config_dir = os.path.join(Path.home(), '.config', 'goal-tracker')
        os.makedirs(config_dir, exist_ok=True)  # Create directory if it doesn't exist

        # Path to style.css in config directory
        config_style_path = os.path.join(config_dir, 'style.css')

        # If style.css doesn't exist in config, create a default one
        if not os.path.exists(config_style_path):
            with open(config_style_path, 'w') as f:
                f.write("")

        # Load CSS from config directory
        css_provider.load_from_path(config_style_path)
        
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.set_name("main_window")

        self.tasks = []
        self.task_id_counter = 1


        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_name("main_vbox")
        vbox.set_halign(Gtk.Align.FILL)
        vbox.set_valign(Gtk.Align.START)
        scrolled_window.add(vbox)
        self.add(scrolled_window)

        self.tasks_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.tasks_container.set_halign(Gtk.Align.FILL)
        vbox.pack_start(self.tasks_container, True, True, 0)

        add_task_button = Gtk.Button(label="")
        add_task_button.set_name("add_task_button")
        add_task_button.connect("clicked", lambda w: self.add_task())
        add_task_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        add_task_box.set_halign(Gtk.Align.START)
        add_task_box.pack_start(add_task_button, False, False, 0)
        vbox.pack_start(add_task_box, False, False, 0)

        self.load_tasks_from_json()

    def update_progressbar_time(self, progressbar_time, time_left_label, entries):
        try:
            start_date_entry, start_time_entry, end_date_entry, end_time_entry = entries
            start_time = datetime.strptime(f"{start_date_entry.get_text()} {start_time_entry.get_text()}", "%d.%m.%Y %H:%M:%S")
            end_time = datetime.strptime(f"{end_date_entry.get_text()} {end_time_entry.get_text()}", "%d.%m.%Y %H:%M:%S")
        except ValueError:
            progressbar_time.set_fraction(0)
            return True
        total_duration = (end_time - start_time).total_seconds()
        elapsed_duration = (datetime.now() - start_time).total_seconds()
        remaining_duration = total_duration - elapsed_duration
        if remaining_duration < 0:
            remaining_duration = 0
        time_left_label.set_text(f"Time left: {seconds_to_ymdhms(remaining_duration)}")
        if total_duration > 0:
            fraction = max(0, min(1, elapsed_duration / total_duration))
            progressbar_time.set_fraction(fraction)
            progressbar_time.set_text(f"{fraction*100:.2f}%")
        else:
            progressbar_time.set_fraction(0)
            progressbar_time.set_text("0.00%")
        return True  # Continue calling

    def update_progressbar_progress(self, progressbar_progress, entries):
        try:
            current_progress_entry, goal_entry = entries
            current_value = int(current_progress_entry.get_text())
            goal_value = int(goal_entry.get_text())
        except ValueError:
            progressbar_progress.set_fraction(0)
            return True
        if goal_value == 0:
            progressbar_progress.set_fraction(1)
            progressbar_progress.set_text("100%")
            return True
        fraction = max(0, min(1, current_value / goal_value))
        progressbar_progress.set_fraction(fraction)
        progressbar_progress.set_text(f"{fraction*100:.2f}%")
        return True  # Continue calling
    
    def on_datetime_entry_changed(self, entries, datetime_label):
        start_date_entry, start_time_entry, end_date_entry, end_time_entry = entries
        start_date = start_date_entry.get_text()
        start_time = start_time_entry.get_text()
        end_date = end_date_entry.get_text()
        end_time = end_time_entry.get_text()
        if start_date == end_date:
            datetime_label.set_text(f"{start_date} {start_time} - {end_time}")
            return
        if start_time == end_time:
            datetime_label.set_text(f"{start_date} - {end_date}")
            return
        datetime_label.set_text(start_date_entry.get_text() + " " + start_time_entry.get_text() + " - " + end_date_entry.get_text() + " " + end_time_entry.get_text())

    def toggle_datetime_visibility(self, date_time_box):
        if date_time_box.get_visible():
            date_time_box.hide()
        else:
            date_time_box.show()

    def remove_task(self, task_box, task_id):
        self.tasks_container.remove(task_box)
        self.tasks = [task for task in self.tasks if task["id"] != task_id]
        self.export_tasks_to_json()

    def add_task(self, id=None, name="Task Name", progress="", goal="", start_date=None, start_time=None, end_date=None, end_time=None):

        task_id = id
        if task_id is None:
            task_id = self.task_id_counter

        if start_date is None or start_date == "":
            start_date = datetime.now().strftime("%d.%m.%Y")
        if start_time is None or start_time == "":
            start_time = datetime.now().strftime("%H:%M:%S")
        if end_date is None or end_date == "":
            end_date = datetime.now().strftime("%d.%m.%Y")
        if end_time is None or end_time == "":
            end_time = datetime.now().strftime("%H:%M:%S")

        self.task_id_counter = max(self.task_id_counter, task_id + 1)

        task_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        task_box.set_valign(Gtk.Align.CENTER)
        task_box.set_name("main_task_box")

        # Task name entry
        task_title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        task_title_box.set_halign(Gtk.Align.FILL)
        task_name_entry = Gtk.Entry()
        task_name_entry.set_text(name)
        task_name_entry.set_name("task_name_entry") 
        task_name_entry.set_width_chars(30)
        remove_task_button = Gtk.Button(label="")
        remove_task_button.set_name("remove_task_button")
        remove_task_button.connect("clicked", lambda w: self.remove_task(task_box, task_id))
        task_title_box.pack_end(remove_task_button, False, False, 0)
        task_title_box.pack_start(task_name_entry, False, False, 0)
        task_box.pack_start(task_title_box, False, False, 0)

        # Progress bars
        progressbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        progressbar_box.set_valign(Gtk.Align.FILL)
        progressbar_box.set_halign(Gtk.Align.FILL)
        progressbar_progress = Gtk.ProgressBar()
        progressbar_progress.set_name("progressbar-progress")
        progressbar_box.pack_start(progressbar_progress, True, True, 0)
        progressbar_time = Gtk.ProgressBar()
        progressbar_time.set_name("progressbar-time")
        progressbar_box.pack_start(progressbar_time, True, True, 0)
        task_box.pack_start(progressbar_box, True, True, 0)

        date_time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        date_time_box.set_halign(Gtk.Align.FILL)
        date_time_box.set_spacing(100)
        date_time_box.set_name("date_time_box")
        task_box.pack_end(date_time_box, False, False, 0)

        start_datetime_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        start_datetime_box.set_halign(Gtk.Align.START)
        start_datetime_box.set_spacing(6)
        start_datetime_box.set_name("start_datetime_box")
        date_time_box.pack_start(start_datetime_box, True, True, 0)
        end_datetime_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        end_datetime_box.set_halign(Gtk.Align.END)
        end_datetime_box.set_spacing(6)
        end_datetime_box.set_name("end_datetime_box")
        date_time_box.pack_start(end_datetime_box, True, True, 0)

        self.calendar = Gtk.Calendar()
        now = datetime.now()

        date_time_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        date_time_label_box.set_halign(Gtk.Align.END)
        date_time_label_box.set_name("date_time_label_box")
        datetime_label = Gtk.Label(label="")
        datetime_label.set_name("datetime_label")
        datetime_label_event_box = Gtk.EventBox()
        datetime_label_event_box.add(datetime_label)
        datetime_label_event_box.set_tooltip_text("Click to set time margins")
        datetime_label_event_box.connect("button-press-event", lambda w, e: self.toggle_datetime_visibility(date_time_box))
        date_time_label_box.pack_start(datetime_label_event_box, False, False, 0)
        progressbar_box.pack_end(date_time_label_box, False, False, 0)

        time_entries = ()
        start_date_entry = Gtk.Entry()
        start_date_entry.set_text(start_date)
        start_date_entry.set_name("entry")
        start_date_entry.set_width_chars(10)
        start_datetime_box.pack_start(Gtk.Label(label="Start date:"), False, False, 0)
        start_datetime_box.pack_start(start_date_entry, False, False, 0)
        start_date_entry.connect("changed", lambda w: self.on_datetime_entry_changed(time_entries, datetime_label))

        start_time_entry = Gtk.Entry()
        start_time_entry.set_text(start_time)
        start_time_entry.set_name("entry")
        start_time_entry.set_width_chars(8)
        start_datetime_box.pack_start(Gtk.Label(label="time:"), False, False, 0)
        start_datetime_box.pack_start(start_time_entry, False, False, 0)
        start_time_entry.connect("changed", lambda w: self.on_datetime_entry_changed(time_entries, datetime_label))

        end_date_entry = Gtk.Entry()
        end_date_entry.set_text(end_date)
        end_date_entry.set_name("entry")
        end_date_entry.set_width_chars(10)
        end_datetime_box.pack_start(Gtk.Label(label="End date:"), False, False, 0)
        end_datetime_box.pack_start(end_date_entry, False, False, 0)
        end_date_entry.connect("changed", lambda w: self.on_datetime_entry_changed(time_entries, datetime_label))

        end_time_entry = Gtk.Entry()
        end_time_entry.set_text(end_time)
        end_time_entry.set_name("entry")
        end_time_entry.set_width_chars(8)
        end_datetime_box.pack_start(Gtk.Label(label="time:"), False, False, 0)
        end_datetime_box.pack_start(end_time_entry, False, False, 0)
        end_time_entry.connect("changed", lambda w: self.on_datetime_entry_changed(time_entries, datetime_label))
        time_entries = (start_date_entry, start_time_entry, end_date_entry, end_time_entry)

        self.on_datetime_entry_changed(time_entries, datetime_label)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        progress_box.set_halign(Gtk.Align.FILL)
        progress_box.set_name("progress_box")
        progress_box_start = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        progress_box_start.set_halign(Gtk.Align.START)
        progress_box_end = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        progress_box_end.set_halign(Gtk.Align.START)
        
        goal_entry = Gtk.Entry()
        current_progress_entry = Gtk.Entry()
        current_progress_entry.set_name("entry")
        progress_entries = (current_progress_entry, goal_entry)
        current_progress_entry.set_text(progress)
        current_progress_entry.set_width_chars(4)
        progress_box_start.pack_start(Gtk.Label(label="Current progress:"), False, False, 0)
        progress_box_start.pack_start(current_progress_entry, False, False, 0)
        progress_box.pack_start(progress_box_start, True, True, 0)
        current_progress_entry.connect("changed", lambda w: self.update_progressbar_progress(progressbar_progress, progress_entries))

        goal_entry.set_text(goal)
        goal_entry.set_name("entry")
        goal_entry.set_width_chars(4)
        progress_box_end.pack_start(Gtk.Label(label="Goal:"), False, False, 0)
        progress_box_end.pack_start(goal_entry, False, False, 0)
        progress_box.pack_start(progress_box_end, True, True, 0)

        time_left_label = Gtk.Label()
        time_left_label.set_text("")

        progress_box.pack_start(time_left_label, True, True, 0)

        goal_entry.connect("changed", lambda w: self.update_progressbar_progress(progressbar_progress, progress_entries))
        task_box.pack_start(progress_box, False, False, 0)
        current_progress_entry.grab_focus()
        
        task_data = {
            "id": task_id,
            "name_entry": task_name_entry,
            "progress_entry": current_progress_entry,
            "goal_entry": goal_entry,
            "start_date_entry": start_date_entry,
            "start_time_entry": start_time_entry,
            "end_date_entry": end_date_entry,
            "end_time_entry": end_time_entry,
            "date_time_box": date_time_box,
        }
        self.tasks.append(task_data)

        task_name_entry.connect("changed", lambda w: self.export_tasks_to_json())
        current_progress_entry.connect("changed", lambda w: self.export_tasks_to_json())
        goal_entry.connect("changed", lambda w: self.export_tasks_to_json())
        start_date_entry.connect("changed", lambda w: self.export_tasks_to_json())
        start_time_entry.connect("changed", lambda w: self.export_tasks_to_json())
        end_date_entry.connect("changed", lambda w: self.export_tasks_to_json())
        end_time_entry.connect("changed", lambda w: self.export_tasks_to_json())
        self.export_tasks_to_json()

        # Add the new task box to the container
        self.tasks_container.pack_start(task_box, True, True, 0)
        self.tasks_container.show_all()

        self.update_progressbar_progress(progressbar_progress, progress_entries)
        self.update_progressbar_time(progressbar_time, time_left_label, time_entries)
        GLib.timeout_add(1000, lambda: self.update_progressbar_time(progressbar_time, time_left_label, time_entries))

        for task in self.tasks:
            task["date_time_box"].hide()


    def export_tasks_to_json(self, filename="tasks.json"):
        config_dir = os.path.join(Path.home(), '.config', 'goal-tracker')
        os.makedirs(config_dir, exist_ok=True)
        filepath = os.path.join(config_dir, filename)
        
        tasks_json = []
        for task in self.tasks:
            tasks_json.append({
                "id": task["id"],
                "name": task["name_entry"].get_text(),
                "progress": task["progress_entry"].get_text(),
                "goal": task["goal_entry"].get_text(),
                "start_date": task["start_date_entry"].get_text(),
                "start_time": task["start_time_entry"].get_text(),
                "end_date": task["end_date_entry"].get_text(),
                "end_time": task["end_time_entry"].get_text(),
            })
        with open(filepath, "w") as f:
            json.dump(tasks_json, f, indent=2)

    def load_tasks_from_json(self, filename="tasks.json"):
        config_dir = os.path.join(Path.home(), '.config', 'goal-tracker')
        filepath = os.path.join(config_dir, filename)
        
        try:
            with open(filepath, "r") as f:
                tasks_json = json.load(f)
            for task in tasks_json:
                self.add_task(
                    id=task.get("id"),
                    name=task.get("name", "Task Name"),
                    progress=task.get("progress", ""),
                    goal=task.get("goal", ""),
                    start_date=task.get("start_date", ""),
                    start_time=task.get("start_time", ""),
                    end_date=task.get("end_date", ""),
                    end_time=task.get("end_time", "")
                )
        except (FileNotFoundError, json.JSONDecodeError):
            pass

def main():
    win = ProgressBarWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    for task in win.tasks:
        task["date_time_box"].hide()
    Gtk.main()

if __name__ == "__main__":
    main()