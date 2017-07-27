# -*- encoding: utf-8 -*-
##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    @author: Nathan Flückiger, Emanuel Cino
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,# -*-
#    coding: utf-8 -*-
##############################################################################

{'name': 'Geospatial support for compassion projects',
 'version': '10.0',
 'category': 'GeoBI',
 'author': "Fluckiger Nathan",
 'depends': [
     'base',
     'base_geoengine',
     'child_compassion',

 ],
 'external_dependencies': {
    'python': ['shapely']},
 'data': [
     'views/project_compassion_geoengine_view.xml'
 ],
 'installable': True,
 'application': True,
 'active': False,
 }
