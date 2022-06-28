import math
import os
import shutil

import cadquery as cq

from src.parsepcb import ParsePCB


def create_output_directory():
    directory = 'STEP_files'
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)


class GenerateSteps:
    """
            GenerateSteps uses the mapping of layers to their entities stored in a dictionary to
            iterate over the entities of each layer, and build a STEP print path file using cadQuery

            Attributes
            ----------
            layer_to_entities : dict
                Maps layers to their entities. Uses layers as keys, and entity list of a given layer as value for a key

            pcb_height: float
                Height of the PCB (inches)
                TODO: determine default value

            pcb_width: float
                Width of the PCB (inches)
                TODO: determine default value

            layer_thickness: float
                Thickness of the layer (inches)
                TODO: determine default value

            conductive_trace_dimensions: tuple (width, height, thickness)
                Dimensions of conductive traces (inches)
                TODO: determine default value

            Methods
            -------
            __init__()
                Process attributes and initialize the WorkPlanes for each layer


            """

    def __init__(self, selected_layer_to_entities, selected_layer_to_options, pcb_width, pcb_height, layer_thickness,
                 conductive_trace_width, conductive_trace_thickness):
        print("~~~ Generating STEP files ~~~")
        print("-----------------------------\n")
        # Get the dictionary that maps layers to their entities
        self.selected_layer_to_entities = selected_layer_to_entities
        self.selected_layers = self.selected_layer_to_entities.keys()

        self.selected_layer_to_options = selected_layer_to_options

        # Store dimensions (width x height x thickness)
        self.layer_dimensions = [pcb_width, pcb_height, layer_thickness]

        self.trace_dimensions = [conductive_trace_width, conductive_trace_thickness]

        self.supported_dxf_entity_types = ['LINE', 'CIRCLE', 'ARC']

        # Dictionary to layers to their WorkPlane
        self.layer_to_workplane = {}

        create_output_directory()
        # call the methods
        self.generate_STEP_workplanes()
        self.render_STEPs()
        # TODO: call method to add lines

    # Render the STEP files
    def render_STEPs(self):
        for selected_layer, workplane in self.layer_to_workplane.items():
            if workplane:
                print(f"Rendering {selected_layer.lower()}.step")
                cq.exporters.export(workplane, f"STEP_files/{selected_layer.lower()}.step")

    def generate_STEP_workplanes(self):
        for selected_layer in self.selected_layers:
            if self.selected_layer_to_options[selected_layer] == "Conductive Traces only":
                self.layer_to_workplane[selected_layer] = self.add_lines(selected_layer,
                                                                         self.selected_layer_to_entities[
                                                                             selected_layer], False)

            elif self.selected_layer_to_options[selected_layer] == "Conductive Traces AND Vias AND Plane":
                r = self.add_holes(selected_layer, self.selected_layer_to_entities[selected_layer])
                traces = self.add_lines(selected_layer, self.selected_layer_to_entities[selected_layer], True)
                self.layer_to_workplane[selected_layer] = r.union(traces)

    def add_holes(self, selected_layer, selected_layer_entities):

        print(f"Processing {selected_layer}'s circles and arcs")

        # Dictionary that maps radii to the holes of that radius
        radius_to_holes = {}

        for entity in selected_layer_entities:
            seen_radii = list(radius_to_holes.keys())
            if entity.dxftype() in self.supported_dxf_entity_types and entity.dxftype() != 'LINE':
                if 0 < entity.dxf.center[0] < self.layer_dimensions[0] and 0 < entity.dxf.center[1] < \
                        self.layer_dimensions[1]:
                    if entity.dxf.radius not in seen_radii:
                        radius_to_holes[entity.dxf.radius] = []
                    radius_to_holes[entity.dxf.radius].append((round(
                        entity.dxf.center[0] - self.layer_dimensions[0] / 2, 4), round(
                        entity.dxf.center[1] - self.layer_dimensions[1] / 2, 4)))

        r = cq.Workplane("XY").box(self.layer_dimensions[0], self.layer_dimensions[1], self.layer_dimensions[2])
        r = r.faces(">Z").workplane()
        i = 0
        last_point = (0, 0)
        for radius, holes in radius_to_holes.items():
            for hole in holes:
                r = r.center(hole[0] - last_point[0], hole[1] - last_point[1])
                r = r.circle(radius)
                r = r.cutThruAll()

                last_point = hole
                i += 1

        return r

    # TODO: Work in progress
    def add_lines(self, selected_layer, selected_layer_entities, extrude_from_layer):
        print(f"Processing {selected_layer}'s lines")

        if extrude_from_layer:
            # Increment trace thickness by layer thickness
            trace_thickness = self.trace_dimensions[1] + self.layer_dimensions[2]
        else:
            trace_thickness = self.trace_dimensions[1]

        compatible_lines = []
        base = cq.Workplane("XY")

        for entity in selected_layer_entities:
            if entity.dxftype() == 'LINE':
                line = [(entity.dxf.start[0], entity.dxf.start[1]), (entity.dxf.end[0], entity.dxf.end[1])]
                (x_start, y_start), (x_end, y_end) = line

                if x_start == x_end:
                    (leX_start, leY_start) = (x_start + self.trace_dimensions[0] ** (6 / 11), y_start)
                    (reX_start, reY_start) = (x_start - self.trace_dimensions[0] ** (6 / 11), y_start)

                    (leX_end, leY_end) = (x_end + self.trace_dimensions[0] ** (6 / 11), y_end)
                    (reX_end, reY_end) = (x_end - self.trace_dimensions[0] ** (6 / 11), y_end)

                elif y_start == y_end:
                    (leX_start, leY_start) = (x_start, y_start - self.trace_dimensions[0] ** (6 / 11))
                    (reX_start, reY_start) = (x_start, y_start + self.trace_dimensions[0] ** (6 / 11))

                    (leX_end, leY_end) = (x_end, y_end - self.trace_dimensions[0] ** (6 / 11))
                    (reX_end, reY_end) = (x_end, y_end + self.trace_dimensions[0] ** (6 / 11))

                elif ((x_start < x_end) and (y_start < y_end)) or ((x_start > x_end) and (y_start > y_end)):
                    (leX_start, leY_start) = (
                        x_start - (math.sqrt(self.trace_dimensions[0]) / 2),
                        y_start + (math.sqrt(self.trace_dimensions[0]) / 2))
                    (reX_start, reY_start) = (
                        x_start + (math.sqrt(self.trace_dimensions[0]) / 2),
                        y_start - (math.sqrt(self.trace_dimensions[0]) / 2))

                    (leX_end, leY_end) = (x_end - (math.sqrt(self.trace_dimensions[0]) / 2),
                                          y_end + (math.sqrt(self.trace_dimensions[0]) / 2))
                    (reX_end, reY_end) = (x_end + (math.sqrt(self.trace_dimensions[0]) / 2),
                                          y_end - (math.sqrt(self.trace_dimensions[0]) / 2))

                elif ((x_start < x_end) and (y_start > y_end)) or ((x_start > x_end) and (y_start < y_end)):
                    (leX_start, leY_start) = (
                        x_start - (math.sqrt(self.trace_dimensions[0]) / 2),
                        y_start - (math.sqrt(self.trace_dimensions[0]) / 2))
                    (reX_start, reY_start) = (
                        x_start + (math.sqrt(self.trace_dimensions[0]) / 2),
                        y_start + (math.sqrt(self.trace_dimensions[0]) / 2))

                    (leX_end, leY_end) = (x_end - (math.sqrt(self.trace_dimensions[0]) / 2),
                                          y_end - (math.sqrt(self.trace_dimensions[0]) / 2))
                    (reX_end, reY_end) = (x_end + (math.sqrt(self.trace_dimensions[0]) / 2),
                                          y_end + (math.sqrt(self.trace_dimensions[0]) / 2))

                conductive_trace = (cq.Workplane("XY").moveTo(leX_start - self.layer_dimensions[0] / 2,
                                                              leY_start - self.layer_dimensions[1] / 2).
                                    lineTo(leX_end - self.layer_dimensions[0] / 2,
                                           leY_end - self.layer_dimensions[1] / 2).lineTo(
                    reX_end - self.layer_dimensions[0] / 2, reY_end - self.layer_dimensions[1] / 2).
                                    lineTo(reX_start - self.layer_dimensions[0] / 2,
                                           reY_start - self.layer_dimensions[1] / 2).lineTo(
                    leX_start - self.layer_dimensions[0] / 2, leY_start - self.layer_dimensions[1] / 2).
                                    close())
                conductive_trace = conductive_trace.extrude(trace_thickness)
                base = base.union(conductive_trace)

        return base
