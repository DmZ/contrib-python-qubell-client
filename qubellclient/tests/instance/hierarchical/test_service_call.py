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
from qubellclient.tests.base import attr
import os


class ServiceCallTestApp(base.BaseTestCasePrivate):

    @classmethod
    def setUpClass(cls):
        super(ServiceCallTestApp, cls).setUpClass()

    # Create applications for tests
        cls.parent = cls.organization.application(name="%s-test-servicecall-parent" % cls.prefix, manifest=cls.manifest)
        cls.child = cls.organization.application(name="%s-test-servicecall-child" % cls.prefix, manifest=cls.manifest)

    # Create non shared instance to use in tests
        mnf = Manifest(file=os.path.join(os.path.dirname(__file__), 'child.yml'))
        mnf.patch('application/components/child_app/configuration/configuration.workflows/launch/return/own/value', 'Service call child')
        cls.child.upload(mnf)
        cls.child_instance = cls.child.launch(destroyInterval=600000)
        assert cls.child_instance.ready()
        cls.child_revision = cls.child.revisionCreate(name='%s-tests-servicecall-shared' % cls.prefix, instance=cls.child_instance)

        params = ''.join('%s: %s' % (cls.child_revision.revisionId.split('-')[0], cls.child_instance.instanceId))
        cls.shared_service = cls.organization.service(name='%s-HierarchicalAppTest-instance' % cls.prefix,
                                                          type='builtin:shared_instances_catalog',
                                                          parameters=params)
        cls.environment.serviceAdd(cls.shared_service)

    @classmethod
    def tearDownClass(cls):
        super(ServiceCallTestApp, cls).tearDownClass()

    # Remove created services
        cls.environment.serviceRemove(cls.shared_service)
        cls.shared_service.delete()

        cls.parent.clean()
        cls.child.clean()

        cls.parent.delete()
        cls.child.delete()

    @attr('smoke')
    def test_servicecall_hierapp_with_shared_child(self):
        """ Launch hierarchical app with shared instance and execute service call on child.
        """

        pmnf = Manifest(file=os.path.join(os.path.dirname(__file__), "parent_servicecall.yml")) #Todo: resolve paths
        pmnf.patch('application/components/child/configuration/__locator.application-id', self.child.applicationId)
        self.parent.upload(pmnf)


        parameters = {
                "child": {
                    "revisionId": self.child_revision.revisionId
            }}

        parent_instance = self.parent.launch(destroyInterval=600000, parameters=parameters)
        self.assertTrue(parent_instance.ready(), "Parent instance failed to start")

        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')
        sub = parent_instance.submodules

        self.assertTrue(len([sid for sid in sub if sid['id'] == self.child_instance.instanceId]))  # Way i search for id

        # Instance ready. Execute workflow with servicecall

        parent_instance.runWorkflow(name='actions.child_servicecall')
        self.assertTrue(parent_instance.ready(), "Parent instance failed to execute servicall workflow")
        sleep(10)
        self.assertEqual('child Update launched', parent_instance.returnValues['parent_out.child_workflow_status'])



        # Shouldn't be able to remove child while parent use it and should return error
        # TODO: BUG
        #self.assertFalse(child_instance.destroy())

        self.assertTrue(parent_instance.destroy())

    def test_servicecall_hierapp(self):
        """ Launch hierarchical with non shared instance and execute service call on child.
        """

        pmnf = Manifest(file=os.path.join(os.path.dirname(__file__), "parent_servicecall.yml")) #Todo: resolve paths
        pmnf.patch('application/components/child/configuration/__locator.application-id', self.child.applicationId)
        self.parent.upload(pmnf)

        parent_instance = self.parent.launch(destroyInterval=600000)
        self.assertTrue(parent_instance.ready(), "Parent instance failed to start")

        self.assertEqual(parent_instance.submodules[0]['status'], 'Running')
        sub = parent_instance.submodules

        self.assertFalse(len([sid for sid in sub if sid['id'] == self.child_instance.instanceId]))  # Way i search for id

    # Instance ready. Execute workflow with servicecall

        parent_instance.runWorkflow(name='actions.child_servicecall')
        self.assertTrue(parent_instance.ready(), "Parent instance failed to execute servicall workflow")
        sleep(10)
        self.assertEqual('child Update launched', parent_instance.returnValues['parent_out.child_workflow_status'])



        # Shouldn't be able to remove child while parent use it and should return error
        # TODO: BUG
        #self.assertFalse(child_instance.destroy())

        self.assertTrue(parent_instance.destroy())