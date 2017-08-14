#!/bin/bash
#
#  Copyright 2001 - 2017 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

HISTORY_DIR="./history"
GALAXY=${1}
BORDER=${2:-0} # instead of resize, create black border this thick
if [[ -z ${GALAXY// } ]]; then
    echo "Needs parameter GALAXY (prefix of screenshot files)"
    exit 1
fi

# resize screenshots and rename them so it's consumable by ffmpeg
count=0
ls -1v "${HISTORY_DIR}/${GALAXY}"* | while read i; do
    ((count++))
    printf -v j "%04d" ${count}
    if (( $BORDER > 0 ));then
        convert "$i" -bordercolor Black -border ${BORDER}x${BORDER} "${HISTORY_DIR}/t_${GALAXY}.${j}.png"
    else
        convert "$i" -resize 1080x1080 -quality 100 "${HISTORY_DIR}/t_${GALAXY}.${j}.png"
    fi

done

# create video
ffmpeg -framerate 12 -i "${HISTORY_DIR}/t_${GALAXY}.%04d.png" -c: libx264 -profile:v high -crf 20 -pix_fmt yuv420p "${HISTORY_DIR}/${GALAXY}.mp4"
