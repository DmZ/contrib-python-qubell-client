# Copyright (c) 2013 Qubell Inc., http://qubell.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__email__ = "vkhomenko@qubell.com"

from qubell.api.private import exceptions
from qubell.api.private.common import QubellEntityList
from qubell.api.provider.router import ROUTER as router

class Zones(QubellEntityList):
    def __init__(self, organization):
        # TODO: That should be done by parent
        QubellEntityList.__init__(self, organization)

    def _generate_object_list(self):
        for zone in self.organization.list_zones_json():
            self.object_list.append(Zone(self.auth, self.organization, id=zone['id']))

class Zone(object):
    def __init__(self, auth, organization, id):
        self.auth = auth
        self.zoneId = id
        self.organizationId = organization.organizationId
        self.organization = organization
        my = self.json()
        self.name = my['name']

    def __getattr__(self, key):
        resp = self.json()
        if resp.has_key(key):
            return resp[key]
        raise exceptions.NotFoundError('Cannot get zone property %s' % key)


    def json(self):
        resp = router.get_zones(org_id=self.organizationId)
        zone = [x for x in resp.json() if x['id'] == self.zoneId]
        if len(zone)>0:
            return zone[0]