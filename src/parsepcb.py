import ezdxf
from ezdxf.addons.drawing import matplotlib

import os.path
import sys
import shutil
import unittest

PATH = os.path.dirname(os.getcwd())


class ParsePCB:
    """
        ParsePCB is used to extract the layers and entities from a DXF file,
        and passes them to the GUI.

        Attributes
        ----------
        file_path : str
            the path to the DXF file

        Methods
        -------
        __init__()
            Uses ezdxf.readfile() to extract modelspace and part of the layer to entities mappings

        extract_block_data()
            Extracts the remaining entities that are nested in DXF blocks

        get_layer_to_entity_types()
            Identifies unique entity types for each layer. Returns dictionary of layers
            to unique entity types, which will be useful information for the GUI

        render_layers()
            Use layer to entities dictionary to separate the layers and save them as PNG. Note that
            only lines and circles are extracted for each layer.

        get_layer_names()
            Getter function to get the names of the layers. They will be passed to the GUI to populate
            the layers dropdown spinner.

        """

    def __init__(self, file_path):
        try:
            # Read file using ezdxf and extract model space
            self.dxf_file_name = file_path
            self.dxf_file = ezdxf.readfile(file_path)
            self.msp = self.dxf_file.modelspace()

            # Use groupby() to get a dictionary (key, val) = (layer, entities)
            # Note that this does NOT get entities belonging to layers that are
            # stored in blocks and referenced using INSERT entities
            self.layers_to_entities = self.msp.groupby(dxfattrib="layer")
            self.layers = self.layers_to_entities.keys()
            self.rendered_layers = []

            # Prepare etc folder that will contain runtime data
            directory = 'etc'
            if os.path.exists(directory):
                shutil.rmtree(directory)
            os.makedirs(directory)

            # Call methods to extract data from DXF file and separate its layers
            self.render_board()
            self.extract_block_data()
            self.render_layers()

        except IOError:
            print(f"Cannot open {file_path} with ezdxf")
            raise IOError("Cannot open DXF file")
        except ezdxf.DXFStructureError:
            print(f"Cannot open {file_path} because of an issue with the contents of the file")
            raise IOError("Cannot open DXF file")

    def extract_block_data(self):
        """
            Extract entities from blocks, and extend the previously built dictionary by adding entities
            to layers
        """
        for block in self.dxf_file.blocks:
            for e in block:
                if (e.dxftype() == 'LINE' or e.dxftype() == 'CIRCLE' or e.dxftype() == 'ARC') \
                        and e.dxf.layer in self.layers:
                    self.layers_to_entities[e.dxf.layer].append(e)

    def get_layer_to_entity_types(self):
        """
            Iterate over dictionary to identify unique entities for each layer.
            Useful application of this method is to show unique layers before and
            after entities are extracted from blocks
        """
        layer_to_unique_entities = {}
        layer_to_overlooked_entities = {}
        for layer, entities in self.layers_to_entities.items():
            # Create entry for each layer
            layer_to_unique_entities[layer] = []
            layer_to_overlooked_entities[layer] = []

            # Loop over entities and identify unique entity types
            for entity in entities:
                entity_type = entity.dxftype().lower()
                if entity_type not in layer_to_unique_entities[layer]:
                    layer_to_unique_entities[layer].append(entity_type)

                # If entity type is not line, circle, or arc, and hasn't been encountered for that
                # layer, then we add it to the overlooked entities for that layer
                supported_entities = "line", "circle", "arc"
                if entity_type not in supported_entities \
                        and entity_type not in layer_to_overlooked_entities[layer]:
                    layer_to_overlooked_entities[layer].append(entity_type)

        # print(f"Printing layer_to_unique_entities dictionary \n{layer_to_unique_entities}:")
        return layer_to_unique_entities, layer_to_overlooked_entities

    def render_layers(self):
        """
            Use layer to entities dictionary to separate the layers and save them as PNG. Note that
            only lines and circles are extracted for each layer.

            QCR: Q - what to do with Hatch and data types that might be introduced from other boards?
        """
        layers_directory = 'etc/rendered_layers'
        os.makedirs(layers_directory)

        # Use entities of each layer to create a new ezdxf document and save as PNG
        for layer, entities in self.layers_to_entities.items():
            doc = ezdxf.new()
            msp = doc.modelspace()

            # Useful layer contains either lines or circles or both
            useful_layer = False

            for entity in entities:
                if entity.dxftype() == 'LINE':
                    msp.add_line(entity.dxf.start, entity.dxf.end)
                    useful_layer = True
                elif entity.dxftype() == 'CIRCLE':
                    msp.add_circle(entity.dxf.center, entity.dxf.radius)
                    useful_layer = True
                elif entity.dxftype() == 'ARC':
                    msp.add_arc(entity.dxf.center, entity.dxf.radius,
                                entity.dxf.start_angle, entity.dxf.end_angle)
                    useful_layer = True

            # Save the layer if it is useful
            if useful_layer:
                matplotlib.qsave(msp, f'{layers_directory}/{layer.lower()}.png')
                self.rendered_layers.append(layer)

    def render_board(self):
        matplotlib.qsave(self.msp, 'etc/PCB.png')

    def get_layer_names(self):
        """
            Getter function to get the names of the layers. They will be passed to the GUI to populate
            the layers dropdown spinner.
        """

        return self.layers, self.rendered_layers

    def get_layer_entities(self):
        """
            Get the layer to entities dictionary, which will be used to generate the 3D printable files.
        """

        return self.layers_to_entities


# TODO: Add unit tests for this class
class TestValidCases(unittest.TestCase):

    def test_board_dxf(self):
        self.dxf_file_name = PATH + '/board.dxf'
        self.parser = ParsePCB(self.dxf_file_name)

        # Case 1: Check if the correct file is imported
        self.assertEqual(self.parser.dxf_file_name, self.dxf_file_name)

        # Case 2: Confirm layer elements
        self.assertEqual(len(self.parser.get_layer_names()[0]), 16)
        self.assertEqual(self.parser.get_layer_names()[0],
                         ezdxf.readfile(self.dxf_file_name).modelspace().groupby(dxfattrib="layer").keys())

        # Case 3: Confirm rendered layer elements
        self.assertEqual(len(self.parser.get_layer_names()[1]), 14)
        layer_names_as_list = [layer_name.lower() for layer_name in self.parser.get_layer_names()[0]]
        for rendered_layer_name in self.parser.get_layer_names()[1]:
            self.assertTrue(rendered_layer_name in layer_names_as_list)

        # Case 4: Check if overlooked layers are excluded
        self.assertFalse(layer_names_as_list[1] in self.parser.get_layer_names())
        self.assertFalse(layer_names_as_list[9] in self.parser.get_layer_names())

        # Case 5: Locate the created png files
        self.assertTrue(os.path.exists(PATH + '/etc/PCB.png'))
        for rendered_layer_name in self.parser.get_layer_names()[1]:
            self.assertTrue(os.path.exists(os.path.exists(PATH + f'/etc/rendered_layers/{rendered_layer_name}.png')))

        # Case 6: Verify that unique and overlooked entities are correctly distinguished
        unique_entities_as_list = [entities for entities in self.parser.get_layer_to_entity_types()[0].values()]
        overlooked_entities_as_list = [entities for entities in self.parser.get_layer_to_entity_types()[1].values()]
        for unique_entities, overlooked_entities in zip(unique_entities_as_list, overlooked_entities_as_list):
            if 'arc' in unique_entities:
                self.assertFalse('arc' in overlooked_entities)
            if 'line' in unique_entities:
                self.assertFalse('line' in overlooked_entities)
            if 'circle' in unique_entities:
                self.assertFalse('circle' in overlooked_entities)
            if 'mtext' in unique_entities:
                self.assertTrue('mtext' in overlooked_entities)
            if 'insert' in unique_entities:
                self.assertTrue('insert' in overlooked_entities)
            if 'hatch' in unique_entities:
                self.assertTrue('hatch' in overlooked_entities)


class TestErrorCases(unittest.TestCase):

    # Missing 'SECTION' from 2nd line and 'HEAD' from 4th line
    def test_corrupted_file(self):
        with self.assertRaises(Exception):
            ParsePCB(PATH + '/board_corrupted.dxf')

    def test_file_not_found(self):
        with self.assertRaises(Exception):
            ParsePCB(PATH + '/DNE.dxf')

    def test_wrong_extension(self):
        with self.assertRaises(Exception):
            ParsePCB(PATH + '/board.dff')


if __name__ == "__main__":
    unittest.main()
