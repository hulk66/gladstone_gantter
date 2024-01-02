'''
Copyright (C) 2024 Tobias Himstedt


This file is part of Gladstone Gantter (GG).

GG is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

GG is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

from nicegui import ui, context, events
from gantt.gantt_builder  import Section, Task, Gantt, gantt_encoder, gantt_decoder
from datetime import date, datetime
import re
import numpy as np
import json
# from functools import partial

class GanttEditor:

    CHART_LABEL = "Timeline"
    DATA_LABEL = "Data"

    gantt = Gantt()
    # active_section = gantt.add_section("Swimlane")
    # active_task = None
    plus_button = None

    def __init__(self):
        self.gantt = Gantt()
        self.config = '''
---
config:
    theme: base
    themeVariables: 
      sectionBkgColor: "{section0bgcolor}"
      altSectionBkgColor: "{odd_sectionbgcolor}"
      sectionBkgColor2: "{even_sectionbgcolor}"
      taskBkgColor: "{taskbgcolor}"
    gantt:
        barGap: 10
        barHeight: 40
        fontSize: 20
        sectionFontSize: 20
        leftPadding: 200
        topPadding: 75
        gridLineStartPadding: 50
---
''' 

    def update_gantt(self):
        config = self.config.format(section0bgcolor = self.gantt.section0bgcolor, 
                                    odd_sectionbgcolor = self.gantt.odd_sectionbgcolor, 
                                    even_sectionbgcolor = self.gantt.even_sectionbgcolor, 
                                    taskbgcolor = self.gantt.taskbgcolor)
        print(config)
        self.mermaid.set_content(config  + self.gantt.get_mermaid_str())
        self.mermaid.update()   

    def add_days_date_as_str(self, date_str:str, days:int) -> str:
        d = date.fromisoformat(date_str)
        result = np.busday_offset(d, days, roll="forward")      
        return str(result.astype("datetime64[D]"))


    def calc_end_date(self, active_task: Task) -> None:
        d = date.fromisoformat(active_task.start)
        if active_task.duration == "":
            active_task.duration = "0d"

        duration = "".join(active_task.duration.split())
        num = int(duration[:-1])
        unit = duration[-1:]

        if unit == "d":
            end = np.busday_offset(d, num, roll="forward")
        elif unit == "w":
            end = np.busday_offset(d, num*7, roll="forward")
        elif unit == "m":
            end = np.busday_offset(d, num*30, roll="forward")
        elif unit == "y":
            end = np.busday_offset(d, num*365, roll="forward")

        active_task.end = str(end.astype("datetime64[D]"))

    

    def on_change_tab(self, event):
        if event.args[0] == self.CHART_LABEL:
            self.update_gantt()
 
    def remove_task(self, section: Section, task: Task = None, row = None) -> None:
        # get position of task to delete
        cur_task_pos = section.tasks.index(task)
        if cur_task_pos == 0 and len(section.tasks) > 1:
            current_row_position = row.parent_slot.parent.default_slot.children.index(row)
            if len(row.parent_slot.parent.default_slot.children) > 1:
                # The first task of a section has been removed, so enable the swimlane input fields for the following task
                next_row = row.parent_slot.parent.default_slot.children[current_row_position+1]
                next_row.default_slot.children[0] = ui.input(placeholder='Swimlane ...', validation={"Name needed": lambda value: value!= "" }).bind_value(section, "title" ).classes("col-1")
                next_row.update()

        section.remove_task(task) 
        if len(section.tasks) == 0:
            self.gantt.remove_section(section)
 
        row.delete()        
        if len(self.gantt.sections) == 0:
            self.add_swimlane()

    def update_ui_after_loading(self) -> None:

        self.card.clear()
        self.add_diagram_settings()
        self.data_container.clear()
        self.add_header()

        with self.data_container:

            for active_section in self.gantt.sections:
                for index, active_task in enumerate(active_section.tasks):


                    with ui.element("div").classes("w-full row q-gutter-md") as active_row:    

                        if index == 0:
                            ui.input(placeholder='Swimlane ...', validation={"Name needed": lambda value: value!= "" }).bind_value(active_section, "title" ).classes("col-1")
                        else:
                            ui.label("").classes("col-1")

                        ui.input(placeholder='Task ...', validation={"Title needed": lambda value: value!= "" }).bind_value(active_task, "title" ).classes("col")
                        ui.select(["Task", "Milestone"]).bind_value(active_task, "type").classes("col-1")
                        with ui.input().classes("col-1") as start_date:
                            start_date.bind_value(active_task, "start")
                            with start_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                            with ui.menu() as menu:
                                ui.date().bind_value(start_date).props("first-day-of-week=1")


                        ui.input(
                            placeholder='Duration in d,w,m,y', 
                            validation={"Number followed by d for days, w for weeks, m for months, y for years":
                            lambda value: re.match("[0-9]*[d,w,m,y]", "".join(value.split()))}) \
                            .bind_value(active_task, "duration" ) \
                            .on("blur", lambda: self.calc_end_date(active_task)).classes("col-1")

                        with ui.input().classes("col-1") as end_date:
                            end_date.bind_value(active_task, "end")
                            with end_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                            with ui.menu() as menu:
                                ui.date().bind_value(end_date).props("first-day-of-week=1")

                        ui.select(["active", "done"]).bind_value(active_task, "status").classes("col-1")
                        ui.checkbox("Critical").bind_value(active_task, "critical").classes("col-1")
                        with ui.element("q-btn-group").classes("col-1").props("flat"):
                            # this is cumbersome but I don't have a better solution for now
                            # assign section, task and row to the gui button in order to use them in the event
                            add = ui.button(icon="add", on_click = lambda e: self.add_task(e.sender.section, e.sender.task, e.sender.row)).props("flat") # .bind_enabled(self, "edit_visible")
                            add.task = active_task
                            add.section = active_section
                            add.row = active_row
                            remove = ui.button(icon="remove", on_click = lambda e: self.remove_task(e.sender.section, e.sender.task, e.sender.row)).props("flat") # .bind_enabled(self, "edit_visible")
                            remove.task = active_task
                            remove.section = active_section
                            remove.row = active_row


    def add_task(self, active_section: Section, previous_task: Task = None, previous_row = None) -> Task:
        
        active_task = active_section.add_task("", previous_task)
        active_task.end = str(datetime.now().date())

        if previous_task and previous_task.end:
            active_task.start = previous_task.end
        else:
            active_task.start = str(datetime.now().date())

        with self.data_container:
            with ui.element("div").classes("w-full row q-gutter-md") as active_row:    
                if len(active_section.tasks) == 1:
                    ui.input(placeholder='Swimlane ...', validation={"Name needed": lambda value: value!= "" }).bind_value(active_section, "title" ).classes("col-1")
                else:
                    ui.label("").classes("col-1")

  
                if previous_row:
                    position = active_row.parent_slot.parent.default_slot.children.index(previous_row)
                    active_row.move(target_index=position+1)
                ui.input(placeholder='Task ...', validation={"Title needed": lambda value: value!= "" }).bind_value(active_task, "title" ).classes("col")
                ui.select(["Task", "Milestone"]).bind_value(active_task, "type").classes("col-1")
                with ui.input().classes("col-1") as start_date:
                    start_date.bind_value(active_task, "start")
                    with start_date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                    with ui.menu() as menu:
                        ui.date().bind_value(start_date).props("first-day-of-week=1")

                ui.input(
                    placeholder='Duration in d,w,m,y', 
                    validation={"Number followed by d for days, w for weeks, m for months, y for years":
                    lambda value: re.match("[0-9]*[d,w,m,y]", "".join(value.split()))}) \
                    .bind_value(active_task, "duration" ) \
                    .on("blur", lambda: self.calc_end_date(active_task)).classes("col-1")

                with ui.input().classes("col-1") as end_date:
                    end_date.bind_value(active_task, "end")
                    with end_date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                    with ui.menu() as menu:
                        ui.date().bind_value(end_date).props("first-day-of-week=1")

                ui.select(["active", "done"]).bind_value(active_task, "status").classes("col-1")
                ui.checkbox("Critical").bind_value(active_task, "critical").classes("col-1")
                with ui.element("q-btn-group").classes("col-1").props("flat"):
                    ui.button(icon="add", on_click=lambda: self.add_task(active_section, active_task, active_row)).props("flat") # .bind_enabled(self, "edit_visible")
                    ui.button(icon="delete", on_click=lambda: self.remove_task(active_section, active_task, active_row)).props("flat")
                    # ui.button(icon="reorder").props("flat").bind_enabled(self, "edit_visible")


    def save_to_file(self): 
        json_str = json.dumps(self.gantt, default=gantt_encoder, indent=2)
        ui.download(json_str.encode(), f'{self.gantt.title if self.gantt.title else "most_import_gantt_diagram_ever"}.json')

    def load_from_file(self, event: events.UploadEventArguments) -> None:
        content = event.content.read().decode()
        self.gantt = json.loads(content, object_hook=gantt_decoder)
        self.update_ui_after_loading()
        # print(self.gantt.get_mermaid_str())

    def add_swimlane(self) -> Section:
        active_section = self.gantt.add_section("")
        #with self.data_container:
        #    ui.input(placeholder='Swimlane ...', validation={"Name needed": lambda value: value!= "" }).bind_value(active_section, "title" ).classes("text-h5")
        self.add_task(active_section)
        return active_section


    def setup_ui(self) -> None:
        ui.add_head_html('''
            <style id="mermaidcss">
            .titleText {
                text-anchor: middle;
                font-size: 36px !important;
            }
            .tick text {
                font-size: 16px;
            }
            </style> 
        ''')
        ui.page_title('Gladstone Gantther')
        context.get_client().content.classes('h-[100vh]') 

        with ui.tabs().classes('w-full') as tabs:
            data_tab = ui.tab(self.DATA_LABEL)
            diagram_tab = ui.tab(self.CHART_LABEL)

        with ui.tab_panels(tabs, value=data_tab).classes('row fit') as tab_panels: 
            tab_panels.on("transition", self.on_change_tab)

            with ui.tab_panel(diagram_tab):
                #with ui.card().classes("row fit"):
                #    ui.textarea("Tweak UI").bind_value(self, "config").classes("col-12")
                #    ui.button("Update", on_click=lambda: self.update_gantt())

                with ui.card().classes("row fit"):
                    self.mermaid = ui.mermaid("").classes("col fit")
    

            with ui.tab_panel(data_tab):
                self.card = ui.card().classes("w-full no-shadow")
                self.add_diagram_settings()

                ui.row()
                ui.separator()
                ui.row()

                self.data_container = ui.element("div").classes("w-full")
                self.add_header()
                with ui.element("div").classes("col-12"):
                    ui.button("Add Swimlane", on_click=self.add_swimlane)

                ui.row()
                ui.separator()
                ui.row()

                with ui.element("div").classes("row w-full items-end q-gutter-md"):
                    ui.button("Save Diagram", on_click=self.save_to_file)
                    with ui.expansion("Load"):
                        ui.upload(label="Load", on_upload=self.load_from_file, auto_upload=True).props("hide-upload-btn")

        self.add_swimlane()   
        #ui.label().bind_text_from(self.gantt, "mermaid")
        #ui.button("print", on_click=self.update_gantt)

    def add_diagram_settings(self) -> None:
        with self.card:
            with ui.element("div").classes("row w-full items-end q-gutter-md"):
                ui.checkbox('Show Title').bind_value(self.gantt, "show_title").classes("col-1")
                ui.input(placeholder='Diagram Title ', validation={"Title needed": lambda value: value != "" }).bind_value(self.gantt, "title" ).classes("col").bind_enabled(self.gantt, "show_title")    
                ui.select(["%Y-%m-%d", "%d-%m-%Y", "%m-%Y", "%m"], label="Select Axis Time Format").bind_value(self.gantt, "axis_format").classes("col-1")
                ui.select(["auto", "1day", "1week", "1month"], label="Select Tick Interval").bind_value(self.gantt, "tick_interval").classes("col-1")
                ui.checkbox('Show Weekends in Timeline').bind_value(self.gantt, "show_weekends").classes("col-2")
                ui.checkbox('Show Today Marker').bind_value(self.gantt, "show_today").classes("col-2")
            with ui.element("div").classes("row w-full items-end q-gutter-md"):                
                ui.color_input(label='Starting Swimlane Color').classes("col").bind_value(self.gantt, "section0bgcolor")
                ui.color_input(label='Odd Swimlanes Color').classes("col").bind_value(self.gantt, "odd_sectionbgcolor")
                ui.color_input(label='Even Swimlanes Color').classes("col").bind_value(self.gantt, "even_sectionbgcolor")
                ui.color_input(label='Task Background Color').classes("col").bind_value(self.gantt, "taskbgcolor")

    def add_header(self):
        with self.data_container:
            with ui.element("div").classes("row w-full q-gutter-md") as self.header:
                ui.label("Swimlane").classes("col-1 text-h6")
                ui.label("Task").classes("col text-h6")
                ui.label("Type").classes("col-1 text-h6")
                ui.label("Start").classes("col-1 text-h6")
                ui.label("Duration").classes("col-1 text-h6")
                ui.label("End").classes("col-1 text-h6")
                ui.label("Status").classes("col-1 text-h6")
                ui.label("Critical").classes("col-1 text-h6")
                ui.label("Edit").classes("col-1 text-h6")

editor = GanttEditor()
editor.setup_ui()
ui.run()
