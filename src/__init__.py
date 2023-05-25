#!/usr/bin/env python
# encoding: utf-8

###############################################################################
#                                                                             #
# Wartungspläne CLI Tool                                                      #
#                                                                             #
# __init__.py
###############################################################################
#                                                                             #
# Copyright (C) 2016-2022 science + computing ag                              #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or (at       #
# your option) any later version.                                             #
#                                                                             #
# This program is distributed in the hope that it will be useful, but         #
# WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU           #
# General Public License for more details.                                    #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

""" Constant module data. """


VERSION = (0, 2)

__version__ = '.'.join(map(str, VERSION))
__author__ = 'Felix Bauer'
__description__ = 'Handling of recurring (scheduled) events (todos) and ' \
                  'send reminders via email, potentially to a ticketing system'
__copyright__ = (
    'Copyright (C) 2016-2022 science + computing ag. All rights reserved.')
__license__ = 'GPLv3'
