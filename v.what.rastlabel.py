#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:       v.what.rastlabel
# AUTHOR(S):    Paulo van Breugel <paulo at ecodiv.org>
# PURPOSE:      Upload raster values and labels at positions of vector points
#               to the vector attribute table.
#
# COPYRIGHT: (C) 2016 by Paulo van Breugel and the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
##############################################################################

#%module
#% description: Uploads raster values and labels to vector point layer
#% keyword: vector
#% keyword: sampling
#% keyword: raster
#% keyword: position
#% keyword: querying
#% keyword: attribute table
#% keyword: surface information
#%end

#%option G_OPT_V_MAP
#% key: vector
#% description: Name vector points map for which to add raster values & labels
#% required: yes
#%end

#%option G_OPT_R_INPUTS
#% key: raster
#% description: Name of raster map(s) with labels to be queried
#% required: yes
#% multiple: yes
#%end

#%option G_OPT_R_INPUTS
#% key: raster2
#% description: Name of raster map(s) without labels to be queried
#% required: no
#% multiple: yes
#%end

#%option G_OPT_V_OUTPUT
#% description: Name of output point layer
#% key_desc: name
#% required: yes
#%end

# import libraries
import os
import sys
import grass.script as gs
import string
from grass.pygrass.modules import Module
from subprocess import PIPE
import tempfile

def main(options, flags):

    gisbase = os.getenv('GISBASE')
    if not gisbase:
        gs.fatal(_('$GISBASE not defined'))
        return 0

    # Variables
    RAST = options['raster']
    RAST = RAST.split(',')
    RASTL = [z.split('@')[0] for z in RAST]
    RASTL = [x.lower() for x in RASTL]
    RAST2 = options['raster2']
    RAST2 = RAST2.split(',')
    RASTL2 = [z.split('@')[0] for z in RAST2]
    RASTL2 = [x.lower() for x in RASTL2]
    VECT = options['vector']
    OUTP = options['output']

    # Create vector with column names
    CT = ['x double precision, y double precision, label integer']
    for i in xrange(len(RAST)):
        DT = gs.parse_command('r.info', flags='g', map=RAST[i],
                              quiet=True)['datatype']
        if DT == 'CELL':
            CT.append("ID_{0} integer, {0} varchar(255)".format(RASTL[i]))
        else:
            CT.append("ID_{0} double precision, {0} varchar(255)".
                      format(RASTL[i]))
    CNT = ','.join(CT)

    # Get raster points of raster layers with labels
    # Export point map to text file first and use that as input in r.what
    # TODO: the above is workaround to get vector cat value as label. Easier,
    # would be to use vector point map directly as input, but that does not
    # give label to link back to old vector layer
    PAT = Module('v.out.ascii', input=VECT, format='point', separator='space',
                 precision=12, stdout_=PIPE).outputs.stdout
    CAT = Module('r.what', flags='f', map=RAST, stdin_=PAT,
                 stdout_=PIPE).outputs.stdout
    CATV = CAT.replace('|*|', '||')
    Module('v.in.ascii', input='-', stdin_=CATV, output=OUTP, columns=CNT,
           separator='pipe', format='point', x=1, y=2, quiet=True)

    # Get raster points of raster layers without labels (optional)
    if options['raster2']:
        for j in xrange(len(RAST2)):
            DT = gs.parse_command('r.info', flags='g', map=RAST2[j],
                                  quiet=True)['datatype']
            if DT == 'CELL':
                CT = "{} integer".format(RASTL2[j])
            else:
                CT = "{} double precision".format(RASTL2[j])
            Module('v.db.addcolumn', map=OUTP, columns=CT)
            Module('v.what.rast', map=OUTP, raster=RAST2[j], column=RASTL2[j])

    # Write metadata
    opt2 = dict((k, v) for k, v in options.iteritems() if v)
    hist = ' '.join("{!s}={!r}".format(k, v) for (k, v) in opt2.iteritems())
    hist = "v.what.rastlabel {}".format(hist)
    Module('v.support', map=OUTP, comment="created with v.what.rastlabel",
           cmdhist=hist, flags='r', quiet=True)

if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
