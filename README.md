This repository contains files used for the automated extraction and processing of pawn art, maps, and text from tabletop RPG pdfs for use with Foundry VTT. Currently, image-title pair extraction from pawn packs (Paizo Inc., Pathfinder 2e) using a combination of PyMuPDF (fitz) and opencv has been developed. Pawn packs are PDFs contain artwork used to represent various characters with corresponding names overlayed on top in a loose grid. 

Additional development is underway to automate map extraction and set up. Specifically, the coordinates of tags corresponding to points of interest on maps are extracted to allow for the import of scene details found in the pdf text. Additionally, opencv-based edge detection methods are employed to determine the coordinates of walls for automatic drawing.

Export_Functions.py contains various functions used in Export_Pawns.py to determine the location of images and the corresponding image text within the PDF. In short, page text and image references are isolated while the center of image and text boxes are compared. Text, which is used to name the corresponding image files, are matched to their corresponding image based on the distances between image and text centers. For instances of layered images, image components are layered on a new temporary page, merged, and exported. Finally, for instances of images with black or white backgrounds (rather than transparent backgrounds), opencv is utilized to determine the edge of images, replacing all background pixels with transparent pixels. 

This process was confirmed to work with the following pawn packs:
Beginner Box
Fist of the Ruby Phoenix
NPC Pawns
Player Pawns
Traps and Treasures
