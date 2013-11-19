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
__version__ = "1.0.1"
__email__ = "vkhomenko@qubell.com"

from time import sleep

from qubellclient.tests import base
from qubellclient.private.manifest import Manifest
from qubellclient.private.instance import Instance
from qubellclient.tests.base import attr
import os


class ThreeLevelHierarchicalAppTest(base.BaseTestCasePrivate):


    @classmethod
    def setUpClass(cls):
        super(ThreeLevelHierarchicalAppTest, cls).setUpClass()

    # Create applications for tests
        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), "child.yml"))
        cls.last_child = cls.organization.application(name="%s-test-3lhierapp-last_child" % cls.prefix, manifest=mnf)

        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), "middle_child.yml"))
        mnf.patch('application/components/last_child/configuration/__locator.application-id', cls.last_child.applicationId)
        cls.middle_child = cls.organization.application(name="%s-test-3lhierapp-middle-child" % cls.prefix, manifest=mnf)

        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), "super_parent.yml"))
        mnf.patch('application/components/middle_child/configuration/__locator.application-id', cls.middle_child.applicationId)
        cls.parent = cls.organization.application(name="%s-test-3lhierapp-super-parent" % cls.prefix, manifest=mnf)


    @classmethod
    def tearDownClass(cls):
        super(ThreeLevelHierarchicalAppTest, cls).tearDownClass()

        cls.parent.delete()
        cls.middle_child.delete()
        cls.last_child.delete()

    def tearDown(self):
        super(ThreeLevelHierarchicalAppTest, self).tearDown()
        #self.environment.clean()


    @attr('smoke')
    def test_launch_basic_non_shared_3level_hierapp(self):
        """ Launch hierarchical app with childs as not shared instance. Check that launching parent launches all childs instance.
        """

        parent_instance = self.parent.launch(destroyInterval=300000)
        self.assertTrue(parent_instance, "%s-%s: Parent instance failed to launch" % (self.prefix, self._testMethodName))
        self.assertTrue(parent_instance.ready(),"%s-%s: Parent instance not in 'running' state after timeout" % (self.prefix, self._testMethodName))

        self.assertTrue(parent_instance.submodules) # Check we have submodules started
        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')

        middle_instance = Instance(self.context, id=parent_instance.submodules[0]['id']) # initialize middle instance (we can only get id from parent)
        self.assertTrue(middle_instance.submodules) # Check middle instance start it's dependency
        self.assertEqual(middle_instance.submodules[0]['status'], 'Running')

        self.assertTrue(parent_instance.delete(), "%s-%s: Parent instance failed to destroy" % (self.prefix, self._testMethodName))
        self.assertTrue(parent_instance.destroyed(), "%s-%s: Parent instance not in 'destroyed' state after timeout" % (self.prefix, self._testMethodName))

        self.assertFalse(middle_instance.status) # Check submodule does not exists



    # BUG HERE
    def test_launch_3level_hierapp_shared_last_child(self):
        """ Launch 3-level hierarchical app with last child as shared instance.
        """

    # Create shared last child
        last_child_instance = self.last_child.launch(destroyInterval=600000)
        self.assertTrue(last_child_instance)
        self.assertTrue(last_child_instance.ready())

        last_child_revision = self.last_child.create_revision(name='%s-shared_last_child' % self._testMethodName, instance=last_child_instance)

        params = ''.join('%s: %s\n' % (last_child_revision.revisionId.split('-')[0], last_child_instance.instanceId))

        shared_service = self.organization.service(name='%s-ThreeLevelHierarchicalAppTest-last-child' % self.prefix,
                                                          type='builtin:shared_instances_catalog',
                                                          parameters={'configuration.shared-instances': params})
        self.environment.serviceAdd(shared_service)

        parameters = {
             	'top_parent_in.last_child_input': 'UPD by test Hello from TOP parent to last child',
  		        'top_parent_in.middle_child_input': 'UPD by test Hello from TOP parent to middle child',
                'middle_child': {
                    'parameters': {
                        'last_child': {
                            'revisionId': last_child_revision.revisionId
            }}}}


        parent_instance = self.parent.launch(destroyInterval=300000, parameters=parameters)
        self.assertTrue(parent_instance, "%s-%s: Parent instance failed to launch" % (self.prefix, self._testMethodName))
        self.assertTrue(parent_instance.ready(),"%s-%s: Parent instance not in 'running' state after timeout" % (self.prefix, self._testMethodName))

        self.assertTrue(parent_instance.submodules) # Check we have submodules started
        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')

        middle_instance = Instance(self.context, id=parent_instance.submodules[0]['id']) # initialize middle instance (we can only get id from parent)
        self.assertTrue(middle_instance.submodules) # Check middle instance start it's dependency
        self.assertEqual(middle_instance.submodules[0]['status'], 'Running')
        self.assertEqual(middle_instance.submodules[0]['id'], last_child_instance.instanceId, "Last child used is not shared one")  # Check we use shared last instance

        self.assertTrue(parent_instance.delete(), "%s-%s: Parent instance failed to destroy" % (self.prefix, self._testMethodName))
        self.assertTrue(parent_instance.destroyed(), "%s-%s: Parent instance not in 'destroyed' state after timeout" % (self.prefix, self._testMethodName))

    # Remove created services and instance
        self.environment.serviceRemove(shared_service)
        shared_service.delete()
        self.assertTrue(last_child_instance.delete(), "%s-%s: Last child instance failed to destroy" % (self.prefix, self._testMethodName))
        self.assertTrue(last_child_instance.destroyed(), "%s-%s: Last child instance not in 'destroyed' state after timeout" % (self.prefix, self._testMethodName))


    def test_launch_3level_hierapp_shared_middle_child(self):
        """ Launch 3-level hierarchical app with middle child as shared instance.
        We create basic hierapp, set it as shared and then use it in another hierapp :)
        """

    # Create shared middle child
        middle_child_instance = self.middle_child.launch(destroyInterval=600000)
        self.assertTrue(middle_child_instance)
        self.assertTrue(middle_child_instance.ready())

        middle_child_revision = self.middle_child.create_revision(name='%s-shared_middle_child' % self._testMethodName, instance=middle_child_instance)

        params = ''.join('%s: %s\n' % (middle_child_revision.revisionId.split('-')[0], middle_child_instance.instanceId))

        shared_service = self.organization.service(name='%s-ThreeLevelHierarchicalAppTest-middle_child' % self.prefix,
                                                          type='builtin:shared_instances_catalog',
                                                          parameters={'configuration.shared-instances': params})
        self.environment.serviceAdd(shared_service)

        parameters = {
                "middle_child": {
                    "revisionId": middle_child_revision.revisionId
            }}


        parent_instance = self.parent.launch(destroyInterval=00000, parameters=parameters)

        self.assertTrue(parent_instance, "%s-%s: Parent instance failed to launch" % (self.prefix, self._testMethodName))
        self.assertTrue(parent_instance.ready(),"%s-%s: Parent instance not in 'running' state after timeout" % (self.prefix, self._testMethodName))

        self.assertTrue(parent_instance.submodules) # Check we have submodules started
        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')

        self.assertEqual(parent_instance.submodules[0]['id'], middle_child_instance.instanceId, "Last child used is not shared one")  # Check we use shared last instance

        self.assertTrue(parent_instance.delete(), "%s-%s: Parent instance failed to destroy" % (self.prefix, self._testMethodName))
        self.assertTrue(parent_instance.destroyed(), "%s-%s: Parent instance not in 'destroyed' state after timeout" % (self.prefix, self._testMethodName))

        self.assertEqual(middle_child_instance.status, 'Running') # Check shared still alive

    # Remove created services and instance
        self.environment.serviceRemove(shared_service)
        shared_service.delete()
        self.assertTrue(middle_child_instance.delete(), "%s-%s: Middle child instance failed to destroy" % (self.prefix, self._testMethodName))
        self.assertTrue(middle_child_instance.destroyed(), "%s-%s: Middle child instance not in 'destroyed' state after timeout" % (self.prefix, self._testMethodName))

