## Welsh Embryo Stager

Stage an embryo in the age range `E14` - `E15` by drawing a spline on a photographic image.

### Install and run

- Install miniconda (if needed) from [here](https://docs.conda.io/en/latest/miniconda.html).

- Install [`vedo`](https://vedo.embl.es/) <br>
`pip install vedo==2022.1.0`

- Copy the repository locally eg. <br>
`git clone https://github.com/marcomusy/welsh_embryo_stager.git`

`cd welsh_embryo_stager`

- Run the program <br>
`python stager.py pics/E14.5_L3-03_HL2.5X.jpg`
<br>
Draw a spline by clicking points on your image

![](https://user-images.githubusercontent.com/32848391/158235171-80618fb1-ae35-4a30-8279-4dabdd35a92d.png)


can also read and stage a text file directly with:<br>
`python stager.py pics/E14.5_L3-03_HL2.5X_LHL.txt`

5. Press `q` when finished, an output window will show up with the age of the embryo

![](https://user-images.githubusercontent.com/32848391/158235205-438510d4-6707-4e37-b9bb-17f6516244a1.png)


### Description

Use shape descriptors to calibrate the age over a dataset of about 190 embryos.
The algorithm gives reliable estimates only in the range `E14` to `E15`.
User should check that finger peaks and valleys (marked in green and red)
on the left plot are correctly identified.

The error estimation is completely heuristic and should be taken as a rough indication.


