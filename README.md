# Welsh Mouse Embryo Stager

Stage a mouse embryo in the age range `E14` -> `E15` by drawing a spline on a photographic image.

## Install and run

- Install miniconda (if needed) from [here](https://docs.conda.io/en/latest/miniconda.html).

- Install [`vedo`](https://vedo.embl.es/) and `scipy` by typing:
```bash
pip install vedo -U
conda install scipy
```

- Copy the repository locally
```bash
git clone https://github.com/marcomusy/welsh_embryo_stager.git
cd welsh_embryo_stager
```

- Run the program, eg.:
```bash
python stager.py pics/E14.5_L3-03_HL2.5X.jpg
```

- Draw a spline by clicking points on your image

![](https://user-images.githubusercontent.com/32848391/158235171-80618fb1-ae35-4a30-8279-4dabdd35a92d.png)


- Can also read and stage a text file directly with, eg.:
```bash
python stager.py pics/E14.5_L3-03_HL2.5X_LHL.txt
```

5. Press `q` when finished, an output window will show up with the age of the embryo

![](https://github.com/marcomusy/welsh_embryo_stager/assets/32848391/10acd68d-af42-486e-a4cf-86745801e837)

The above output image and a text file with clicked points are saved to directory `output/` for reference.

### Description

Use three shape descriptors to calibrate the age over a dataset of about 190 embryos.
The algorithm gives reliable estimates only in the range `E14` to `E15`,
**outside of this range results are not reliable.**
User should check that finger peaks and valleys (marked in green and red)
on the left plot are reasonably well identified.

The error estimation is completely heuristic and should be taken as a rough indication,
the red sphere represents the uncertainty in the parameter space.
You can interact with the 3D scene of the bottom-right plot.


### To generate a standalone executable
With `pyinstaller` do:
```bash
rm build dist __pycache__
pyinstaller stager.spec
```
This will create a `dist/stager.exe` file, which you can test with e.g.:
```bash
dist/stager.exe pics/E14.5_L3-03_HL2.5X.jpg
```



