# -*- coding: utf-8 -*-
# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import contextlib

import mock
from oslo_log import log as logging

from designate.tests import TestCase
from designate.notification_handler.nova import NovaFixedHandler
from designate.tests.test_notification_handler import \
    NotificationHandlerMixin

LOG = logging.getLogger(__name__)


class NovaFixedHandlerTest(TestCase, NotificationHandlerMixin):
    def setUp(self):
        super(NovaFixedHandlerTest, self).setUp()

        domain = self.create_domain()
        self.domain_id = domain['id']
        self.config(domain_id=domain['id'], group='handler:nova_fixed')
        self.config(format=['%(host)s.%(domain)s',
                            '%(host)s.foo.%(domain)s'],
                    group='handler:nova_fixed')

        self.plugin = NovaFixedHandler()

    def test_instance_create_end(self):
        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {'domain_id': self.domain_id}

        # Ensure we start with 2 records
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)
        # Should only be SOA and NS records
        self.assertEqual(2, len(records))

        self.plugin.process_notification(
            self.admin_context, event_type, fixture['payload'])

        # Ensure we now have exactly 1 more record
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

    def test_instance_create_end_utf8(self):
        self.config(format=['%(display_name)s.%(domain)s'],
                    group='handler:nova_fixed')

        event_type = 'compute.instance.create.end'
        fixture = self.get_notification_fixture('nova', event_type)

        # Set the instance display_name to a string containing UTF8.
        fixture['payload']['display_name'] = u'Test↟Instance'

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {'domain_id': self.domain_id}

        # Ensure we start with 2 records
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        # Should only be SOA and NS recordsets
        self.assertEqual(2, len(recordsets))

        self.plugin.process_notification(
            self.admin_context, event_type, fixture['payload'])

        # Ensure we now have exactly 1 more recordset
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual(3, len(recordsets))

        # Ensure the created record was correctly converted per IDN rules.
        criterion['type'] = 'A'
        recordsets = self.central_service.find_recordsets(
            self.admin_context, criterion)

        self.assertEqual('xn--testinstance-q83g.example.com.',
                         recordsets[0].name)

    def test_instance_delete_start(self):
        # Prepare for the test
        start_event_type = 'compute.instance.create.end'
        start_fixture = self.get_notification_fixture('nova', start_event_type)

        self.plugin.process_notification(self.admin_context,
                                         start_event_type,
                                         start_fixture['payload'])

        # Now - Onto the real test
        event_type = 'compute.instance.delete.start'
        fixture = self.get_notification_fixture('nova', event_type)

        self.assertIn(event_type, self.plugin.get_event_types())

        criterion = {'domain_id': self.domain_id}

        # Ensure we start with at least 1 record, plus NS and SOA
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(4, len(records))

        self.plugin.process_notification(
            self.admin_context, event_type, fixture['payload'])

        # Simulate the record having been deleted on the backend
        domain_serial = self.central_service.get_domain(
            self.admin_context, self.domain_id).serial
        self.central_service.update_status(
            self.admin_context, self.domain_id, "SUCCESS", domain_serial)

        # Ensure we now have exactly 0 records, plus NS and SOA
        records = self.central_service.find_records(self.admin_context,
                                                    criterion)

        self.assertEqual(2, len(records))

    def test_label_in_format(self):
        event_type = 'compute.instance.create.end'
        self.config(format=['%(label)s.example.com'],
                    group='handler:nova_fixed')
        fixture = self.get_notification_fixture('nova', event_type)
        with contextlib.nested(
                mock.patch.object(self.plugin, '_find_or_create_recordset'),
                mock.patch.object(
                    self.plugin.central_api, 'create_record')) as (
                finder, creator):
            finder.return_value = {'id': 'fakeid'}
            self.plugin.process_notification(
                self.admin_context, event_type, fixture['payload'])
            finder.assert_called_once_with(
                mock.ANY, type='A', domain_id=self.domain_id,
                name='private.example.com')
