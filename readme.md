# Conversion of PCB layouts to STEP files

_This repository contains the software developed for NASA Goddard by Team Techies, composed of Virginia Tech students_

This project converts PCB layouts to Print Path files of the STEP format. The software leverages CAD python libraries and a graphical user interface to get users to configure the PCB layers and provide input on parameters necessary to generate the STEP files.

## Install and run
Begin by cloning this repository to your local machine. <br /><br />
This project requires anaconda. To download and install anaconda, please visit this [link](https://www.anaconda.com/products/distribution)<br /><br />
Once you have anaconda installed, you can install all the dependencies by running the following lines of code (ENV_NAME_HERE is the name of your environment) <br /><br />
```conda create --name ENV_NAME_HERE python=3.9```
<br /> <br />
```conda activate ENV_NAME_HERE```
<br /> <br />
```conda install -c conda-forge ezdxf```
<br /> <br />
```conda install -c cadquery -c conda-forge cadquery=master```
<br /> <br />
```conda install -c conda-forge kivy```
<br /> <br />
```conda install -c conda-forge matplotlib```
<br /> <br />

To run the software, you will need to execute main.py which will open up the graphical user interface. You will not need to run any other files besides main.py

## How to use the project
Once you are able to install and run the software, you can follow the following steps to generate print path files: <br /><br/>
1. Browse for a PCB layout using the file browser of the GUI (*.dxf currently supported)
2. For a given layer you wish to convert to a print path file, select one of the two following configurations:
    * Generate print path files for conductive traces only
    * Generate print path files for conductive traces and generate a plane that will contain any vias found in that layer
3. Make sure to click the "Confirm" button on the layers that you want to convert to print path files. Otherwise they will be discarded.
4. Once you are done configuring your layers, you can click on the button to generate STEP files. It will open a popup which will prompt you to provide pcb width, height, thickness (of each layer), conductive trace width, and conductive trace thickness. Note that all units are assumed to be in inches. Providing this data to the popup will trigger the generation of the print path files, which will be stored in a new directory named ```STEP_files```

### List of libraries
1. ezdxf
2. cadquery
3. kivy
4. matplotlib

### Credits
Enzo Saba, Mia Blitt, Kavin Chaisawangwong, Justice Lin, and Sam Everett contributed to this project as part of their Major Design Experience (MDE) at Virginia Tech.<br/> They worked under the supervision of Beth Paquette and Chris Green from NASA Goddard, Dr. Talty and Dr. Ransbottom from the Virginia Tech ECE department. 

### License
This software is under MIT license to encourage developers to contribute to our work, as well as enable anyone looking to get into the additive manufacturing of electronics.
