Version 1.2.0 of VinylRipperHelper is scheduled to have the following improvements.

 - Command line parameters
   Include the tracklist HTML file to parse, -tg for track gap time in seconds, -li for lead-in time in seconds, and -pf for the output filename prefix
 - When the input parameters are used, the interactive mode of VRH is disabled

So for example, running (python) vinylRipperHelper_v1.2.0.py <filename.html> -tg 5 -li 0 
will execute VRH to completion and generate the label and tags files with no 
prompting for user information.
