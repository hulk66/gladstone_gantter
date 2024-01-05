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
import uuid
import json

class Task:
    def __init__(self, title: str, id = None, type = "Task", status = "", critical = False, active = False, before = [], after = [], start = "", end = "", duration = "") -> None:
        self.id = id if id is not None else str(uuid.uuid4())
        self.title = title
        self.type = type
        self.status = status # None, active or done
        self.critical = critical
        self.active = active
        self.before = before
        self.after = after
        self.start = start
        self.end = end
        self.duration = duration

    #def to_json(self):
    #   return json.dumps(self, default=lambda obj: obj.__dict__)

    def __str__(self) -> str:
        return self.id

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def add_before(self, task) -> None:
        self.before.append(task)

    def add_after(self, task) -> None:
        self.after.append(task)

    def set_start(self, start: str) -> None:
        self.start = start

    def set_length(self, length: str) -> None:
        self.length = length

    def set_done(self, done: bool) -> None:
        self.done = done

    def set_critical(self, critical: bool) -> None:
        self.critical = critical

    def set_active(self, active: bool) -> None:
        self.active = active

    def set_title(self, title: str) -> None:
        self.title = title

    def format_array(self, name: str, arr: list) -> str:
        if len(arr) > 0:
            return name + " ".join( t.__str__() for t in arr)  + ", "
        else:
            return ""
        
    def get_mermaid_str(self) -> str:
        return f"  {self.title}: {'crit, ' if self.critical else ''}" + \
            f"{self.status + ', ' if self.status else ''}" + \
            f"{'milestone, ' if self.type == 'Milestone' else ''}" +\
            f"{self.id}, " +\
            f"{self.start + ', ' if self.start else ''}" + \
            f"{self.format_array('after ',self.after)}" + \
            f"{self.format_array('before ',self.before)}" + \
            f"{self.end if self.end else self.length if self.length else ''}\n"

class Section:
    def __init__(self, title: str, tasks = []):
        self.title = title
        self.tasks = tasks

   #def to_json(self):
   #    return json.dumps(self, default=lambda o: o.__dict__)

    def __contains__(self, task):
        return task in self.tasks

    def add_task(self, title: str, previous_task: Task = None) -> Task:
        task = Task(title)
        if not previous_task:
            self.tasks.append(task)
        else:
            index = self.tasks.index(previous_task)
            self.tasks.insert(index+1, task)
        return task

    def remove_task(self, task: Task) -> None:
        self.tasks.remove(task)

    def get_mermaid_str(self) -> str:
        result = ""
        for task in self.tasks:
            result += task.get_mermaid_str()

        return f"section {self.title}\n{result}"
        
    def format_array(self, name: str, array: list) -> str:
        return f"""
        {name} = {array}\n
        """

def gantt_decoder(obj):
    if 'sections' in obj:
        return Gantt(**obj)
    elif 'tasks' in obj:
        return Section(**obj)
    elif 'type' in obj:
        return Task(**obj)
    else:
        return obj


def gantt_encoder(obj):
    if isinstance(obj, (Gantt, Section, Task)):
        return obj.__dict__
    else:
        raise TypeError("Object of type {} is not JSON serializable".format(type(obj)))


class Gantt:

    def __init__(self, id = None, title = "", sections = [], show_weekends = False, 
                 show_title = False, axis_format = "%Y-%m-%d", 
                 tick_interval = "auto", show_today = True, 
                 section0bgcolor = "#85A0F9",
                 even_sectionbgcolor =  "#26EFE9", 
                 odd_sectionbgcolor = "#2F78C4", 
                 taskbgcolor = "#fafa05" ) -> None:
        self.id = id
        self.sections = sections
        self.title = title
        self.show_weekends = show_weekends
        self.show_title = show_title
        self.axis_format = axis_format
        self.tick_interval = tick_interval
        self.show_today = show_today
        self.section0bgcolor = section0bgcolor
        self.even_sectionbgcolor = even_sectionbgcolor
        self.odd_sectionbgcolor = odd_sectionbgcolor
        self.taskbgcolor = taskbgcolor

    def to_json(self):
       return gantt_encoder(self)

    def set_title(self, title: str) -> None:
        self.title = title

    def add_section(self, name: str) -> Section:
        section = Section(name, [])
        self.sections.append(section)
        return section

    def remove_section(self, section: Section) -> None:
        self.sections.remove(section)

    #def toJson(self):
    #    return json.dumps(self, default=lambda o: o.__dict__)

    def get_mermaid_str(self) -> str:
        result = "gantt"
        if self.show_title:
            result = f"gantt\n title {self.title}\n"
        else:
            result = "gantt\n"
        result += f"  axisFormat {self.axis_format}\n"
        result += f"  tickInterval {self.tick_interval}\n"
        if not self.show_today:
            result += "  todayMarker off\n"
        result += "  dateformat YYYY-MM-DD\n"

        if self.show_weekends:
            # this is a bit strange, as we do not use mermaid calculation for the task dependencies, it has to be done this way
            result += "  excludes weekends\n"
        for section in self.sections:
            result += section.get_mermaid_str()
        return result

    #@property
    #def mermaid(self) -> str:
    #    return self.get_mermaid_str()

