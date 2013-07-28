try:
    import tkinter
except ImportError:
    import Tkinter as tkinter
# hsmpy is Hierarchical State Machine implementation for Python
# it's used here to implement GUI logic
import quadpy
from hsmpy import HSM, State, T, Initial, Internal, EventBus, Event


# tool aliases
Selection_tool, Drawing_tool = ('Select', 'Draw')

# eventbus will be used for all events
# Tkinter events will also be routed through it
eb = EventBus()


# HSM events
class Tool_Changed(Event): pass
class Mouse_Event(Event):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.data = (x, y)
class Canvas_Up(Mouse_Event): pass
class Canvas_Down(Mouse_Event): pass
class Canvas_Move(Mouse_Event): pass


# create Tkinter GUI
root = tkinter.Tk()
canvas = tkinter.Canvas(highlightthickness=0)  # background='white' TODO
canvas.pack(fill='both', expand=True, padx=6, pady=6)

frame = tkinter.Frame()
labels = []
for i, tool in enumerate([Selection_tool, Drawing_tool]):
    lbl = tkinter.Label(frame, text=tool, width=8, relief='raised')
    wtf = tool

    def get_closure(for_tool):
        return lambda _: eb.dispatch(Tool_Changed(for_tool))
    lbl.bind('<Button-1>', get_closure(tool))
    lbl.pack(padx=6, pady=6 * (i % 2))
    labels.append(lbl)
frame.pack(side='left', fill='y', expand=True, pady=6)

canvas.bind('<Button-1>', lambda e: eb.dispatch(Canvas_Down(e.x, e.y)))
canvas.bind('<B1-Motion>', lambda e: eb.dispatch(Canvas_Move(e.x, e.y)))
canvas.bind('<ButtonRelease-1>', lambda e: eb.dispatch(Canvas_Up(e.x, e.y)))


# this will hold the drawn elements
#elements = []
quad = quadpy.Node(0, 0, 300, 300, max_depth=6)


# HSM state and transition actions:

def update_chosen_tool(evt, hsm):
    for lbl in labels:
        print evt.data, lbl['text'], evt.data == lbl['text']
        lbl['relief'] = 'sunken' if evt.data == lbl['text'] else 'raised'
    hsm.data.canvas_tool = evt.data


def initialize_rectangle(evt, hsm):
    x, y = evt.data
    hsm.data.canvas_start_coords = (x, y)
    bounds = (x, y, x + 1, y + 1)
    rect = canvas.create_rectangle(bounds)
    hsm.data.canvas_temp_rect = rect
    #rect.bounds = bounds
    #rect.qt_parent = None
    #quad.insert(rect)


# TODO make this be done automatically by quadpy
def fix_bounds(x_min, y_min, x_max, y_max):
    if x_max < x_min:
        x_min, x_max = x_max, x_min
    if y_max < y_min:
        y_min, y_max = y_max, y_min
    return (x_min, y_min, x_max, y_max)


def draw_rectangle(evt, hsm):
    bounds = fix_bounds(*(hsm.data.canvas_start_coords + evt.data))
    rect = hsm.data.canvas_temp_rect
    # update coordinates
    canvas.coords(rect, bounds)
    #rect.bounds = bounds
    #quad.reinsert(rect)


def is_over_element(evt, hsm):
    elems = hsm.data.quadtree.get_children_under_point(evt.x, evt.y)
    return len(elems) > 0


def is_not_over_element(evt, hsm):
    return not is_over_element(evt, hsm)


def drag_selection_marquee(evt, hsm):
    pass


states = {
    'app': State({
        'select_tool_chosen': State({
            'hovering': State({
                'hovering_over_background': State(),
                'hovering_over_element': State(),
            }),
            'dragging_marquee': State(),
            'moving_elements': State(),
        }),
        'draw_tool_chosen': State({
            'wait_for_draw': State(),
            'drawing': State(),
        })
    })
}

trans = {
    'app': {
        Initial: T('draw_tool_chosen'),
    },
    'select_tool_chosen': {
        Initial: T('hovering'),
        Tool_Changed: T('draw_tool_chosen', action=update_chosen_tool),
        # TODO move to 'app' state
    },
    ####
    'hovering': {
        Initial: T('hovering_over_background'),
    },
    'hovering_over_background': {
        Canvas_Move: T('hovering_over_element', guard=is_over_element),
        Canvas_Down: T('dragging_marquee'),
    },
    'hovering_over_element': {
        Canvas_Move: T('hovering_over_background', guard=is_not_over_element),
        Canvas_Down: T('moving_elements'),
    },
    'dragging_marquee': {
        Canvas_Move: Internal(action=drag_selection_marquee),
        Canvas_Up: T('hovering_over_element'),
    },
    'moving_elements': {
        #Canvas_Move: Internal(action=move_elements),
        Canvas_Up: T('hovering_over_element'),
    },
    ###
    'draw_tool_chosen': {
        Initial: T('wait_for_draw'),
        Tool_Changed: T('select_tool_chosen', action=update_chosen_tool),
        # TODO move to 'app' state
    },
    'wait_for_draw': {
        Canvas_Down: T('drawing', action=initialize_rectangle),
    },
    'drawing': {
        Canvas_Move: Internal(action=draw_rectangle),
        Canvas_Up: T('draw_tool_chosen'),
    },
}


hsm = HSM(states, trans)
hsm.start(eb)

root.mainloop()