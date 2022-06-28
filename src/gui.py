from kivy import Config
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager


from src.parsepcb import ParsePCB
from src.generatesteps import GenerateSteps

# Import GUI configurations from gui.kv
# Builder.load_file('src/gui.kv')

# Disable multi-touch emulation (right-click shows red dot on GUI)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


def stringify_entity_list(entity_list):
    """
        Convert a list into a string containing the comma-separated items of the list
    """
    entity_str = ""
    for entity in entity_list:
        entity_str += entity + ", "

    return entity_str


class GuiLayout(Widget):
    """
            GuiLayout is the main layout of the GUI, that allows users to browse for a
            DXF file and visually inspect that file and its layers.

            Methods
            -------
            __init__()
                Initialize spinner and data that will be manipulated

            spinner_clicked()
                This method is called from the .kv file, and uses the name of the layer selected
                from the dropdown to load the image of that layer onto the canvas

            selected()
                Loading the GUI will show a file browser, and once a file is selected it will be
                passed to this method. It will call ParsePCB using the file path, and remove the file
                browser widget, and add the image widget that will by default show the generated image of
                the PCB.

            index_clicked()
                Assigns an index to the current layer (current layer is empty until a layer is selected
                for the first time).
                If the layer was previously discarded, it will be removed from the discarded list
                and added to the dictionary that maps layer to index.

            discard_layer()
                Called when the "Discard Layer" button is clicked, and adds the current layer
                to the discarded layers list if it is not already there

            print_to_console()
                Use the StackLayout defined in the .kv file to modify the values of the labels using the
                string passed to the method. This effectively emulates a console.

            """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize variables
        self.parser = None
        self.img = Image(size_hint_x=1.3)
        self.two = False
        self.console_lines = [
            " ~> Welcome! This software was developed by Virginia Tech students under the supervision of NASA Goddard,",
            " ~> with the goal of building a simple, complete, and loveable solution to converting CAD drawings",
            " ~> of PCB layouts to STEP files that contain 3D-printable layers of the PCB.",
            " ~> To begin, simply click on a dxf file using the file explorer, go through the layers of that design,",
            " ~> and either discard or assign an index to the layers. Click Generate STEP(s), and get that fancy 3D printer to work!"]
        self.generate_step_parameters = [-1, -1, -1, -1, -1]

        # TODO: color code text based on error status
        self.ids.console_1.text = self.console_lines[0]
        self.ids.console_2.text = self.console_lines[1]
        self.ids.console_3.text = self.console_lines[2]
        self.ids.console_4.text = self.console_lines[3]
        self.ids.console_5.text = self.console_lines[4]


        self.selected_layers_to_entities = {}
        self.selected_layers_to_options = {}

    def selected(self, filename):

        """
            Loading the GUI will show a file browser, and once a file is selected it will be
            passed to this method. It will call ParsePCB using the file path, and remove the file
            browser widget, and add the image widget that will by default show the generated image of
            the PCB.
        """
        self.filePop.dismiss()
        if filename[0].endswith('.dxf'):
            try:
                self.ids.console_1.text = ""
                self.ids.console_2.text = ""
                self.ids.console_3.text = ""
                self.ids.console_4.text = ""
                self.ids.console_5.text = ""
                self.print_to_console(f"[0] START: Loading {filename[0]}")
                self.print_to_console("[1] PROCESS: Parsing file using ParsePCB")
                self.parser = ParsePCB(filename[0])
                self.print_to_console(
                    f"[2] SUCCESS: Parsed {filename[0]}")
                self.two = False

            except IOError:
                self.print_to_console("[2] ERROR: Could not parse DXF file")
        else:
            self.print_to_console("[0] ERROR: Currently, only DXF files are supported (*.dxf).")

    def print_to_console(self, string):

        self.console_lines.pop(0)
        self.console_lines.append(f" ~> {string}")

        self.ids.console_1.text, self.ids.console_2.text, self.ids.console_3.text, \
        self.ids.console_4.text, self.ids.console_5.text = self.console_lines

    def get_configured_layers(self):
        selected_layers = self.layerPop.selected_layers
        self.selected_layers_to_entities = self.layerPop.layer_to_entities
        self.selected_layers_to_options = self.layerPop.layer_to_options

        all_layers = list(self.selected_layers_to_entities.keys())

        for layer in all_layers:
            if layer not in selected_layers:
                self.selected_layers_to_entities.pop(layer)

        return self.selected_layers_to_entities, self.selected_layers_to_options

    def can_generate_steps(self):
        # You can generate STEP(s) as long as you have at least one layer selected
        if self.two:
            self.print_to_console("[4] SUCCESS: Opening config panel for generating STEP(s)")
            self.popup = Popup(title='Enter parameter values to proceed', size_hint=(None, None), size=(400, 500))

            layer_thickness_label = Label(text="Layer thickness (default 0.04 inches)")
            with layer_thickness_label.canvas:
                layer_thickness_label.font_size = 16
                layer_thickness_label.font_name = "imgs/font.otf"
                layer_thickness_label.size_hint_y = 0.1

            layer_thickness_input = TextInput(text="0.04", multiline=False)
            layer_thickness_input.bind(on_text_validate=self.layer_thickness_input_event)
            with layer_thickness_input.canvas:
                self.ids['thick'] = layer_thickness_input
                layer_thickness_input.font_size = 16
                layer_thickness_input.font_name = "imgs/font.otf"
                layer_thickness_input.size_hint_y = 0.1
                layer_thickness_input.height = 30

            ###########
            width_label = Label(text="Width of PCB (inches)")
            with width_label.canvas:
                width_label.font_size = 16
                width_label.font_name = "imgs/font.otf"
                width_label.size_hint_y = 0.1

            width_input = TextInput(text="", multiline=False)
            width_input.bind(on_text_validate=self.width_input_event)
            with width_input.canvas:
                self.ids['width'] = width_input
                width_input.font_size = 16
                width_input.font_name = "imgs/font.otf"
                width_input.size_hint_y = 0.1
                width_input.height = 30

            ######
            height_label = Label(text="Height of PCB (inches)")
            with height_label.canvas:
                height_label.font_size = 16
                height_label.font_name = "imgs/font.otf"
                height_label.size_hint_y = 0.1

            height_input = TextInput(text="", multiline=False)
            height_input.bind(on_text_validate=self.height_input_event)
            with height_input.canvas:
                self.ids['height'] = height_input
                height_input.font_size = 16
                height_input.font_name = "imgs/font.otf"
                height_input.size_hint_y = 0.1
                height_input.height = 30

            ######
            conductive_trace_width_label = Label(text="Width of Conductive Traces (inches)")
            with conductive_trace_width_label.canvas:
                conductive_trace_width_label.font_size = 16
                conductive_trace_width_label.font_name = "imgs/font.otf"
                conductive_trace_width_label.size_hint_y = 0.1

            conductive_trace_width_input = TextInput(text="0.01", multiline=False)
            conductive_trace_width_input.bind(on_text_validate=self.conductive_trace_width_event)
            with conductive_trace_width_input.canvas:
                self.ids['conductive_trace_width'] = conductive_trace_width_input
                conductive_trace_width_input.font_size = 16
                conductive_trace_width_input.font_name = "imgs/font.otf"
                conductive_trace_width_input.size_hint_y = 0.1
                conductive_trace_width_input.height = 30

            ######
            conductive_trace_thickness_label = Label(text="Thickness of Conductive Traces (inches)")
            with conductive_trace_thickness_label.canvas:
                conductive_trace_thickness_label.font_size = 16
                conductive_trace_thickness_label.font_name = "imgs/font.otf"
                conductive_trace_thickness_label.size_hint_y = 0.1

            conductive_trace_thickness_input = TextInput(text="0.01", multiline=False)
            conductive_trace_thickness_input.bind(on_text_validate=self.conductive_trace_thickness_event)
            with conductive_trace_thickness_input.canvas:
                self.ids['conductive_trace_thickness'] = conductive_trace_thickness_input
                conductive_trace_thickness_input.font_size = 16
                conductive_trace_thickness_input.font_name = "imgs/font.otf"
                conductive_trace_thickness_input.size_hint_y = 0.1
                conductive_trace_thickness_input.height = 30

            button = Button(text="Generate STEP(s)")
            button.bind(on_press=self.generate_steps)
            with button.canvas:
                button.font_size = 16
                button.font_name = "imgs/font.otf"
                button.size_hint_y = 0.1

            vertical_box = BoxLayout(orientation="vertical")
            vertical_box.add_widget(layer_thickness_label)
            vertical_box.add_widget(layer_thickness_input)
            vertical_box.add_widget(width_label)
            vertical_box.add_widget(width_input)
            vertical_box.add_widget(height_label)
            vertical_box.add_widget(height_input)
            vertical_box.add_widget(conductive_trace_width_label)
            vertical_box.add_widget(conductive_trace_width_input)
            vertical_box.add_widget(conductive_trace_thickness_label)
            vertical_box.add_widget(conductive_trace_thickness_input)
            vertical_box.add_widget(Widget(size_hint_y=0.1))
            vertical_box.add_widget(button)

            self.popup.add_widget(vertical_box)
            self.popup.open()
        else:
            self.print_to_console("[4] ERROR: No layers selected. Please assign an index to a layer and try again")

    def layer_thickness_input_event(self, value):
        # Acceptable values are assumed to be between 0 and 1 cm
        if 0 < float(value.text) < 2:
            self.generate_step_parameters[0] = float(value.text)
            self.print_to_console(f"[4] INFO: Selected layer thickness of {value.text} inches")

    def width_input_event(self, value):
        if float(value.text) > 0:
            self.generate_step_parameters[1] = float(value.text)
            self.print_to_console(f"[4] INFO: Selected PCB width of {value.text} inches")

    def height_input_event(self, value):
        if float(value.text) > 0:
            self.generate_step_parameters[2] = float(value.text)
            self.print_to_console(f"[4] INFO: Selected PCB height of {value.text} inches")

    def conductive_trace_width_event(self, value):
        if float(value.text) > 0:
            self.generate_step_parameters[3] = float(value.text)
            self.print_to_console(f"[4] INFO: Selected trace width of {value.text} inches")

    def conductive_trace_thickness_event(self, value):
        if float(value.text) > 0:
            self.generate_step_parameters[4] = float(value.text)
            self.print_to_console(f"[4] INFO: Selected trace thickness of {value.text} inches")

    def generate_steps(self, obj):
        try:
            t = float(self.ids.thick.text)
            if 0<t<2:
                self.generate_step_parameters[0] = t
                self.print_to_console(f"[4] INFO: Selected PCB thickness of {self.ids.thick.text} inches")
            w = float(self.ids.width.text)
            if w > 0:
                self.generate_step_parameters[1] = w
                self.print_to_console(f"[4] INFO: Selected PCB width of {self.ids.width.text} inches")
            h = float(self.ids.height.text)
            if h > 0:
                self.generate_step_parameters[2] = h
                self.print_to_console(f"[4] INFO: Selected PCB height of {self.ids.height.text} inches")
            trace_w = float(self.ids.conductive_trace_width.text)
            if trace_w > 0:
                self.generate_step_parameters[3] = trace_w
                self.print_to_console(f"[4] INFO: Selected trace width of {self.ids.conductive_trace_width.text} inches")
            trace_t = float(self.ids.conductive_trace_thickness.text)
            if trace_t > 0:
                self.generate_step_parameters[4] = trace_t
                self.print_to_console(f"[4] INFO: Selected trace thickness of {self.ids.conductive_trace_thickness.text} inches")
        except ValueError:
            pass
        # Call methods to generate step files
        if len(self.generate_step_parameters) == 5 and -1 not in self.generate_step_parameters:
            self.print_to_console("[4] SUCCESS: Parameters are loaded and generation of STEP files is starting")
            layer_to_entities, layer_to_options = self.get_configured_layers()
            GenerateSteps(layer_to_entities, layer_to_options, self.generate_step_parameters[1],
                          self.generate_step_parameters[2], self.generate_step_parameters[0],
                          self.generate_step_parameters[3] * 0.005, self.generate_step_parameters[4])
            self.popup.dismiss()



        else:
            if self.generate_step_parameters[0] == -1:
                self.ids.thick.background_color = [1,0,0]
            if self.generate_step_parameters[1] == -1:
                self.ids.width.background_color = [1,0,0]
            if self.generate_step_parameters[2] == -1:
                self.ids.height.background_color = [1,0,0]
            if self.generate_step_parameters[3] == -1:
                self.ids.conductive_trace_width.background_color = [1,0,0]
            if self.generate_step_parameters[4] == -1:
                self.ids.conductive_trace_thickness.background_color = [1,0,0]
            self.print_to_console("[4] ERROR: Please enter all parameters")
        

    def layer_sel(self):
        if self.parser is not None and self.two is False:
            self.layerPop = LayerPop(self, title='Select Layers')
            self.layerPop.open()
            self.two = True
        elif self.two:
            self.layerPop.open()
        else:
            self.print_to_console("[0] ERROR: No DXF File Selected")

    def file_pop(self):
        self.filePop = FilePop(self, title='Select File')
        self.filePop.open()

    def dismiss_popup(self):
        self._popup.dismiss()


class LayerPop(Popup):
    def __init__(self, obj, **kwargs):
        super(LayerPop, self).__init__(**kwargs)
        self.obj = obj
        self.parser = obj.parser
        self.layer_options_val = "Conductive Traces only"
        self.img = Image(size_hint_x=1)
        self.rendered_layers = []
        self.layer_to_unique_entities = {}
        self.layer_to_overlooked_entities = {}
        self.current_layer = ""
        self.selected_layers = []
        self.discarded_layers = []
        self.layer_to_entities = {}
        self.layer_to_options = {}
        _, self.rendered_layers = self.parser.get_layer_names()
        self.ids.spin_id.values = self.rendered_layers
        
        self.img.source = f"etc/PCB.png"
        self.img.allow_stretch = True
        self.ids.pic.add_widget(self.img)
        self.layer_to_unique_entities, self.layer_to_overlooked_entities = \
            self.parser.get_layer_to_entity_types()
        self.layer_to_entities = self.parser.get_layer_entities()
        self.ids.spin_id.background_color = (113 / 255, 149 / 255, 222 / 255, 1)

        self.layer_buttons_show = False
        self.ids.top_buttons.remove_widget(self.ids.layer_options)
        self.ids.top_buttons.remove_widget(self.ids.confirm_button)
        self.ids.top_buttons.remove_widget(self.ids.discard_layer_button)
        self.ids.main_canvas.remove_widget(self.ids.entities_info)

    def cancel(self):
        self.dismiss()

    def layer_options_clicked(self, value):
        if self.current_layer:
            self.layer_options_val = value

    def discard_layer(self):
        """
            Called when the "Discard Layer" button is clicked, and adds the current layer
            to the discarded layers list if it is not already there
        """
        if self.current_layer and self.current_layer not in self.discarded_layers:
            self.discarded_layers.append(self.current_layer)
            self.ids.spin_id.values.remove(self.current_layer)
            self.ids.pic.remove_widget(self.img)
            self.ids.spin_id.text = "Select a Layer"
            self.ids.layer_options.text = "Conductive Traces only"
            self.ids.entities_found.text = "Select a Layer"
            self.ids.entities_overlooked.text = "Select a Layer"
            self.obj.print_to_console(f"[3] INFO: Discarded layer {self.current_layer}")
            self.spinner_clicked("PCB Layout")

    def spinner_clicked(self, value):
        """
            Called when a layer is selected from the left toolbar.
            Entities found and entities overlooked are loaded into labels after being stringified.
            Display 404 image if layer was not rendered (because it did not contain line, circle, or arc entities)
        """
        if value in self.rendered_layers:
            self.current_layer = value
            self.ids.pic.remove_widget(self.img)
            self.img = Image(size_hint_x=1, size_hint_y=0.9)
            self.img.source = f"etc/rendered_layers/{value.lower()}.png"
            self.img.allow_stretch = True
            self.ids.pic.add_widget(self.img)
            self.ids.pic.size_hint = (2, 1)

            if not self.layer_buttons_show:
                self.ids.top_buttons.add_widget(self.ids.layer_options)
                self.ids.top_buttons.add_widget(self.ids.confirm_button)
                self.ids.top_buttons.add_widget(self.ids.discard_layer_button)
                self.ids.main_canvas.add_widget(self.ids.entities_info)
                self.layer_buttons_show = True

            self.ids.entities_found.text = stringify_entity_list(
                self.layer_to_unique_entities[value])
            self.ids.entities_overlooked.text = stringify_entity_list(
                self.layer_to_overlooked_entities[value])


        elif value == "PCB Layout":
            self.current_layer = "PCB Layout"
            self.ids.pic.remove_widget(self.img)
            self.img = Image(size_hint_x=1, size_hint_y=0.9)
            self.img.source = f"etc/PCB.png"
            self.img.allow_stretch = True
            self.ids.pic.add_widget(self.img)

            self.layer_buttons_show = False
            self.ids.top_buttons.remove_widget(self.ids.layer_options)
            self.ids.top_buttons.remove_widget(self.ids.confirm_button)
            self.ids.top_buttons.remove_widget(self.ids.discard_layer_button)
            self.ids.main_canvas.remove_widget(self.ids.entities_info)

        elif value != "Select a Layer":
            self.ids.pic.remove_widget(self.img)
            self.img = Image(size_hint_x=1, size_hint_y=0.9)
            self.img.source = "imgs/filenotfound.png"
            self.img.allow_stretch = True
            self.ids.pic.add_widget(self.img)
            self.ids.entities_found.text = "Layer did not contain useful entities"
            self.ids.entities_overlooked.text = "Layer did not contain useful entities"

    def confirm(self):
        if self.current_layer:
            self.ids.spin_id.values.remove(self.current_layer)
            self.layer_to_options[self.current_layer] = self.layer_options_val
            self.selected_layers.append(self.current_layer)
            self.obj.print_to_console(f"[3] INFO: Assigned {self.layer_options_val} to layer {self.current_layer}")
            self.ids.spin_id.text = "Select a Layer"
            self.ids.layer_options.text = "Conductive Traces only"
            self.ids.pic.remove_widget(self.img)
            self.ids.entities_found.text = "Select a Layer"
            self.ids.entities_overlooked.text = "Select a Layer"
            self.spinner_clicked("PCB Layout")

        elif self.current_layer not in self.ids.spin_id.values:
            popup = Popup(title='Warning', size_hint=(None, None), size=(400, 300))
            warn = Label(text="Must Select a Layer First")
            with warn.canvas:
                warn.font_size = 24
                warn.font_name = "imgs/font.otf"
                warn.size_hint_y = 0.1

            vertical_box = BoxLayout(orientation="vertical")
            vertical_box.add_widget(warn)

            popup.add_widget(vertical_box)
            popup.open()


class FilePop(Popup):
    def __init__(self, obj, **kwargs):
        super(FilePop, self).__init__(**kwargs)
        self.obj = obj

    def cancel(self):
        self.dismiss()


class ScreenManagement(ScreenManager):
    pass


class GuiApp(App):
    """
        GuiApp instantiates the GuiLayout class and defines the title of the window.

        Methods
        -------
        build()
            Build the layout
    """

    def build(self):
        self.title = "PCB Layout to Print Path Files"

        return GuiLayout()

# TODO: Button to finish if all layers are discarded and proceed (explain in console if for example indexes are messed up)
# TODO: Button generate opens popup with options for thickness and stuff. drag slide bar
# TODO: add unit tests for this class
# TODO: log file for console print statements
