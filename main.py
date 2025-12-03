# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 12:18:09 2025

@author: Frank.Brewster

"""
import csv
from datetime import datetime, timedelta
from nicegui import app, ui, Event
import re

# HOST = sys.argv[0]
# PORT = sys.argv[1]
TIME_RESET = datetime.strptime("00:00:00", '%X')

app.storage.general.indent = True
        
settings_update = Event()

# TODO: probably needs spliting into different files

def _on_start_click(btn, timer) -> None:
    # Logs  and starts timer
    btn.disable()
    app.storage.client['start_time'] = datetime.now()
    timer.activate()
    btn.bind_enabled_from(timer, 'active', backward=lambda e: not e)


def _on_end_click(timer) -> None:
    # Logs time and stops timer
    end_label.set_text(f"{datetime.now():%X}")
    timer.deactivate()


def _reset() -> None:
    # Resets client storage values
    for key, value in app.storage.client.items():
        if isinstance(value, datetime):
            app.storage.client[key] = TIME_RESET
        elif isinstance(value, bool):
            app.storage.client[key] = False
        elif isinstance(value, str):
            app.storage.client[key] = ''
        elif isinstance(value, timedelta):
            app.storage.client[key] = timedelta()
        else:
            app.storage.client[key] = None
    timer_label.set_text("0:00:00")


def _on_record_click() -> None:
    # Appends client storage dict to csv

    # TODO: check fields aren't empty
    try:
        with open(app.storage.general['csv_path'], 'r', newline='') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
        with open(app.storage.general['csv_path'], 'a', newline='') as f:
            writer = csv.DictWriter(f, header, dialect='excel',
                                    extrasaction='ignore')
            writer.writerow(app.storage.client)
    except IOError as e:
        ui.notify(e, type='negative')
        return
    _reset()
    ui.notify("Data has been saved", type='positive')


def _update_select_with_storage(e):
    # Handles new value on dropdown by adding to server storage

    # TODO: confirm add with dialog?
    if e.sender.label == "Contoured by":
        list_name = 'contourers'
        val = e.args[0].upper()
    elif e.sender.label == "Site":
        list_name = 'sites'
        val = e.args[0]
    else:
        return
    app.storage.general[list_name].append(val)
    e.sender.set_options(app.storage.general[list_name])
    e.sender.set_value(val)
    settings_update.emit()
    ui.notification(
        f"{val} has been added to the {list_name} list",
                    type='warning')
    
def _remove_options(dialog, options):
    # Changes the options on select boxes
    app.storage.general.update(options)
    dialog.close()
    settings_update.emit()
    
# Admin settings dialog
with ui.dialog() as admin_dialog, ui.card():
    ui.label("Administration").classes('text-3xl')
    
    ui.label("List removal")
    ui.separator()
    site_rm_select = ui.select(app.storage.general['sites'],
                               value=app.storage.general['sites'],
                                multiple=True,
                                label="Sites").\
        props('use-chips').classes('min-w-50')
    settings_update.subscribe(lambda: site_rm_select.set_options(
        app.storage.general['sites']))
    settings_update.subscribe(lambda: site_rm_select.set_value(
        app.storage.general['sites']))
        
    cnt_rm_select = ui.select(app.storage.general['contourers'],
                              value=app.storage.general['contourers'],
                                multiple=True,
                                label="Contourers").\
        props('use-chips').classes('min-w-50')
    settings_update.subscribe(lambda: cnt_rm_select.set_options(
        app.storage.general['contourers']))
    settings_update.subscribe(lambda: cnt_rm_select.set_value(
        app.storage.general['contourers']))
        
    ui.button("Save", icon='save', on_click=lambda: _remove_options(
        admin_dialog,
        {'sites': site_rm_select.value,'contourers': cnt_rm_select.value}))
    

# Header
with ui.row().classes('w-full'):
    ui.label("MRL Timings").classes("text-5xl")
    
    ui.space()
    ui.button(icon='manage_accounts', on_click=admin_dialog.open)

# Demographic details
with ui.row():
    ptID = ui.input(label="Patient ID",
                    validation={"Not a valid patient ID": lambda value:
                                re.fullmatch(app.storage.general['pt_id_regex'],
                                             value) or
                                len(value) == 0}).\
        bind_value(app.storage.client, 'ptID')

    fracNumber = ui.number(label="Fraction",
                           placeholder='#',
                           min=1,
                           precision=0,
                           step=1)\
        .bind_value(app.storage.client, 'frac')

    site_select = ui.select(app.storage.general['sites'],
                            label="Site",
                            new_value_mode='add').\
        on('new-value', _update_select_with_storage).\
        bind_value(app.storage.client, 'site')
    settings_update.subscribe(lambda: site_select.set_options(
        app.storage.general['sites']))
    

# Elapsed time
with ui.card(align_items='center').classes(
        'w-full no-shadow border border-gray-200'):
    timer_label = ui.label("0:00:00").classes("text-7xl font-bold")
app.storage.client['start_time'] = TIME_RESET

# TODO: don't like this method for formatting the timedelta object but
# the class doesn't implement the internal __format__ method for f strings
timer = ui.timer(1.0, lambda: timer_label.set_text(
    str(datetime.now()-app.storage.client['start_time']).split(".")[0]))
timer.deactivate()
# TODO: warning when time is over specified limit

# Time buttons and labels
with ui.grid(columns=7).classes("w-full min-w-1/2 overflow-x-auto"):
    start_btn = ui.button("Start",
                          on_click=lambda e: _on_start_click(e.sender, timer),
                          color='green',
                          icon='login')

    ui.button("Imaging",
              on_click=lambda: img_label.set_text(f"{datetime.now():%X}"),
              icon='compare')

    ui.button("Contouring",
              on_click=lambda: cnt_label.set_text(f"{datetime.now():%X}"),
              icon='draw')

    ui.button("Planning",
              on_click=lambda: pln_label.set_text(f"{datetime.now():%X}"),
              icon='tune')

    ui.button("Checking",
              on_click=lambda: chk_label.set_text(f"{datetime.now():%X}"),
              icon='playlist_add_check_circle')

    ui.button("Beam on",
              on_click=lambda: bon_label.set_text(f"{datetime.now():%X}"),
              color='amber',
              icon='flare')

    ui.button("Beam off",
              on_click=lambda: _on_end_click(timer),
              color='red',
              icon='logout')

    # All labels are bound to correspoing client storage
    start_label = ui.label("00:00:00")
    start_label.bind_text_from(app.storage.client,
                               'start_time', backward=lambda t: f"{t:%X}")
    img_label = ui.label("00:00:00").bind_text(app.storage.client,
                                               'img_time',
                                               backward=lambda t: f"{t:%X}",
                                               forward=lambda s:
                                                   datetime.strptime(s, '%X'))
    cnt_label = ui.label("00:00:00").bind_text(app.storage.client,
                                               'cnt_time',
                                               backward=lambda t: f"{t:%X}",
                                               forward=lambda s:
                                                   datetime.strptime(s, '%X'))
    pln_label = ui.label("00:00:00").bind_text(app.storage.client,
                                               'pln_time',
                                               backward=lambda t: f"{t:%X}",
                                               forward=lambda s: 
                                                   datetime.strptime(s, '%X'))
    chk_label = ui.label("00:00:00").bind_text(app.storage.client,
                                               'chk_time',
                                               backward=lambda t: f"{t:%X}",
                                               forward=lambda s: 
                                                   datetime.strptime(s, '%X'))
    bon_label = ui.label("00:00:00").bind_text(app.storage.client,
                                               'bon_time',
                                               backward=lambda t: f"{t:%X}",
                                               forward=lambda s: 
                                                   datetime.strptime(s, '%X'))
    end_label = ui.label("00:00:00").bind_text(app.storage.client,
                                               'end_time',
                                               backward=lambda t: f"{t:%X}",
                                               forward=lambda s: 
                                                   datetime.strptime(s, '%X'))

# Collapsible gas timer
with ui.expansion("Gas Timer", icon='masks').classes('border border-gray-500'):
    with ui.row():
        gas_on_btn = ui.button("Gas on", color='green')
        gas_off_btn = ui.button("Gas off", color='red')
        app.storage.client['gas_time'] = timedelta()
        bcon_elapsed_label = ui.label("00:00:00").\
            classes("text-2xl font-bold").\
            bind_text_from(app.storage.client, 'gas_time',
                           backward=lambda td: str(td).split(".")[0])
        # TODO: this makes me nervous iterating the time manaully, I don't know
        # how strict the timer is. Could change to iterate based on system
        # clock like the main timer

        gas_callback = lambda: app.storage.client.update(
            {'gas_time':
             app.storage.client['gas_time'] + timedelta(seconds=1)})
        gas_timer = ui.timer(1, gas_callback)
        gas_timer.deactivate()

        gas_on_btn.on_click(lambda: gas_timer.activate())
        gas_off_btn.on_click(lambda: gas_timer.deactivate())


# Additional info card
# TODO: this card doesn't cope with resizing very well, probably better to flex
with ui.card().classes("max-w-300 flex-initial grid grid-cols-4 grid-row-3"):
    ui.textarea(label="Comments").classes("min-w-100 col-span-2 row-span-2")\
        .bind_value(app.storage.client, 'comment')

    cnt_select = ui.select(app.storage.general['contourers'], label="Contoured by",
              new_value_mode='add').\
        classes("col-span-2 col-start-3 w-40 justify-self-end").\
        on('new-value', _update_select_with_storage).\
        bind_value(app.storage.client, 'contourer')
    settings_update.subscribe(lambda: cnt_select.set_options(app.storage.general['contourers']))

    ui.checkbox("ATP of ATS").classes("row-start-3").\
        bind_value(app.storage.client, 'ATP_of_ATS')

    ui.checkbox("Replanned").classes("row-start-3").\
        tooltip("Plan was remade on additional image").\
        bind_value(app.storage.client, 'rpln')

    abnormal_switch = ui.switch("Abnormal Timings").\
        props('keep-color color=red').\
        classes("col-span-2 col-start-3 row-start-2 justify-self-end").\
        tooltip("Use for fractions with abnormal timings eg. machine "
                "breakdown").\
        bind_value(app.storage.client, 'abnormal')

    ui.button("Reset", icon="replay", on_click=_reset).classes("row-start-3").\
        bind_enabled_from(timer, 'active', backward=lambda e: not e)
    ui.button("Record", icon="file_copy", on_click=_on_record_click).\
        classes("row-start-3").\
        bind_enabled_from(timer, 'active', backward=lambda e: not e)

ui.colors(primary='#005EB8', dark_page='#212121')

ui.run(title="MRL Timings",
       dark=True,
       favicon='⏱️')
