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

import os
import logging as log

import testtools
import nose.plugins.attrib

from qubell.api.private.platform import QubellPlatform
from qubell.api.private.common import Auth

from qubell.api.private.manifest import Manifest
from qubell.api.tools import rand
from qubell.api.private.service import COBALT_SECURE_STORE_TYPE, WORKFLOW_SERVICE_TYPE, SHARED_INSTANCE_CATALOG_TYPE

log.getLogger().setLevel(log.DEBUG)

user = os.environ.get('QUBELL_USER')
password = os.environ.get('QUBELL_PASSWORD')
tenant = os.environ.get('QUBELL_TENANT')
org = os.environ.get('QUBELL_ORGANIZATION', 'selfcheck_organization_name')
prefix = os.environ.get('QUBELL_PREFIX')
zone = os.environ.get('QUBELL_ZONE', '')
new_env = os.environ.get('QUBELL_NEW')

if not user: log.error('No username provided. Set QUBELL_USER env')
if not password: log.error('No password provided. Set QUBELL_PASSWORD env')
if not tenant: log.error('No tenant url provided. Set QUBELL_TENANT env')
if not org: log.error('No organization name provided. Set QUBELL_ORGANIZATION env')

def attr(*args, **kwargs):
    """A decorator which applies the nose and testtools attr decorator
    """
    def decorator(f):
        f = testtools.testcase.attr(args)(f)
        if not 'skip' in args:
            return nose.plugins.attrib.attr(*args, **kwargs)(f)
        # TODO: Should do something if test is skipped
    return decorator



class BaseTestCase(testtools.TestCase):
    ## TODO: Main preparation should be here
    """ Here we prepare global env. (load config, etc)
    """

    @classmethod
    def setUpClass(cls):
        cls.prefix = prefix or rand()

    # Initialize platform and check access
        cls.platform = QubellPlatform.connect(tenant, user, password)

    # Set default manifest for app creation
        cls.manifest = Manifest(file=os.path.join(os.path.dirname(__file__), 'default.yml'), name='BaseTestManifest')

    # Initialize organization
        cls.organization = cls.platform.organization(name=org)

        if zone:
            z = [x for x in cls.organization.list_zones() if x['name'] == zone]
            if z:
                cls.organization.zoneId = z[0]['id']



    # Initialize environment
        if zone:
            cls.environment = cls.organization.environment(name='default', zone=cls.organization.zoneId)
            cls.environment.set_backend(cls.organization.zoneId)
        else:
            cls.environment = cls.organization.get_environment(name='default')

        cls.shared_service = cls.organization.get_or_create_service(name='BaseTestSharedService', type=SHARED_INSTANCE_CATALOG_TYPE, parameters={'configuration.shared-instances':{}})
        cls.wf_service = cls.organization.get_or_create_service(name='Default workflow service', type=WORKFLOW_SERVICE_TYPE)
        cls.key_service = cls.organization.get_or_create_service(name='Default credentials service', type=COBALT_SECURE_STORE_TYPE)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
    # Run before each test
        super(BaseTestCase, self).setUp()
        pass

    def tearDown(self):
    # Run after each test
        super(BaseTestCase, self).tearDown()
        pass

