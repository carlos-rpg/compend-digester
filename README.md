# compend-digester
Useful tools to make Compend 2000 data files easier to work with.

## WHAT IS IT?
This repository contains a collection of handy functions that enhance the outputs of 
[Compend 2000](http://www.phoenix-tribology.com/at6/leaflet/c2000), which is a data adquisition software provided by 
[Phoenix Tribology Ltd.](http://www.phoenix-tribology.com/) alongside with their tribological test machinery.

The data files that Compend 2000 yield are sometimes not ready enough to be dealt with, especially those that feature 
high speed data (HSD) adquisition. This repository aims to solve that problem by providing tools that make analyzing those
files easier.

## WHAT DOES IT DO?
A typical tribological test with Compend 2000 creates a set of tab separated values (TSV) files that follow this structure:

* _test_.TSV
* _test_-h001.TSV
* _test_-h002.TSV
* _test_-h003.TSV
* etc...

Where _test_ is a name provided by the machine operator. If high speed data adquisition is not enabled, the program creates only
_test_.TSV with the "normal speed data" that is limited to 10 measurements/second.

Whith the help of the functions in this repository, you can make *test*.TSV ready to be analyzed with Excel, pandas, R, matlab, etc.

You can also concatenate all HSD files into one single file that will also feature important data columns that may be missing
such as cycle count, which makes further analysis of dynamic coefficient of friction much easier.

## WHAT MACHINES DOES IT SUPPORT?
The current version suports the following rigs:

* [TE 38 long stroke low load reciprocating rig](http://www.phoenix-tribology.com/at2/leaflet/te38)

In the future, more rigs will be supported:
* [Pin on disk friction machine 1469 upgrade](http://www.phoenix-tribology.com/Upgrades)
* [TE 88 multi-station friction & wear test machine](http://www.phoenix-tribology.com/at2/leaflet/te88)

## HOW CAN I USE IT?
Currently this program lacks any sort of graphical user interface, therefore is meant to be use on a terminal.

My recommendation is to use one of the scientific distributions of Python available for all platforms:
* [Anaconda](https://www.anaconda.com/)
* [Enthought Canopy](https://www.enthought.com/product/canopy/)
* [Python(x, y)](https://python-xy.github.io/)

Load or import the module that corresponds to your rig (make sure that all files you download are in the same folder), and change
the current working directory where your Compend 2000 files are.

Look for the functions that start with "digest" inside the module you have loaded or imported. Every function is documented and explains
what it does.

## WHAT WILL IT BE IN THE FUTURE?
I will add new features such as methods to study the dynamic/static coefficient of friction vs time, or coefficient of friction vs position
on the wear track.

I may also add plotting capabilities with MatPlotLib.

I would also like to add support to more machines, but I need access to the machines or someone who has access. If you wish to see 
your rig supported send me a message.

## DISCLAIMER
Please, keep in mind that this software comes with no guarantee whatsoever. I will not take responsibility for any bad results that it
might give.

Please, always remember to perform a sanity check on the results.
