# DesignStudio
A Pymol plug-in for Rosetta structure design and ligand MPNN sequence design

1. Dependency requirements
Need to install rosetta and pyrosetta, ligand_mpnn, pymol==3.X，python==3.X

2. Plugin installation
Download the project to your local computer, unzip it and open the directory.
In pymol, select the __init__.py file in the directory and install it.

3. User Guide
You can use rosetta for protein design and ligand_mpnn for sequence optimization.
The prepare page can obtain all the files for rosetta design (including .params; cleaned structure file; constraint file; pos file). Obtaining cst provides a method for automatic calculation and a method for downloading from the digital catalytic mechanism database built in this study (see below).
The match page can be used for match design, the design page can be used for enzyme design, and the ligand mpnn page can be used for sequence design.
The design page and mpnn page provide the function of result analysis.You can upload the designed score file or .fq file for analysis
![image](/picture/Plugin.png)
