# Copyright 2014-2015 Canonical Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Basic cinder-datera functional test.
"""
import json

import amulet

from charmhelpers.contrib.openstack.amulet.deployment import (
    OpenStackAmuletDeployment
)

from charmhelpers.contrib.openstack.amulet.utils import (
    OpenStackAmuletUtils,
    DEBUG,
)

# Use DEBUG to turn on debug logging
u = OpenStackAmuletUtils(DEBUG)


class CinderDateraBasicDeployment(OpenStackAmuletDeployment):
    """Amulet tests on a basic heat deployment."""

    def __init__(self, series=None, openstack=None, source=None, stable=False):
        """Deploy the entire test environment."""
        super(CinderDateraBasicDeployment, self).__init__(series, openstack,
                                                          source, stable)
        self._add_services()
        self._add_relations()
        self._configure_services()
        self._deploy()

        u.log.info('Waiting on extended status checks...')
        exclude_services = ['nrpe']

        # Wait for deployment ready msgs, except exclusions
        self._auto_wait_for_status(exclude_services=exclude_services)

        self.d.sentry.wait()
        self._initialize_tests()

    def _add_services(self):
        """Add the services that we're testing, where cinder-datera is
        local, and the rest of the services are from lp branches that
        are compatible with the local charm (e.g. stable or next).
        """
        # Note: cinder-datera becomes a cinder subordinate unit.
        this_service = {'name': 'cinder-datera'}
        other_services = [
            {'name': 'percona-cluster'},
            {'name': 'keystone'},
            {'name': 'rabbitmq-server'},
            {'name': 'cinder'}
        ]
        super(CinderDateraBasicDeployment, self)._add_services(
            this_service, other_services, no_origin=['cinder-datera'])

    def _add_relations(self):
        """Add all of the relations for the services."""

        relations = {
            'cinder:storage-backend': 'cinder-datera:storage-backend',
            'keystone:shared-db': 'percona-cluster:shared-db',
            'cinder:shared-db': 'percona-cluster:shared-db',
            'cinder:identity-service': 'keystone:identity-service',
            'cinder:amqp': 'rabbitmq-server:amqp',
        }
        super(CinderDateraBasicDeployment, self)._add_relations(relations)

    def _configure_services(self):
        """Configure all of the services."""
        keystone_config = {
            'admin-password': 'openstack',
            'admin-token': 'ubuntutesting'
        }
        pxc_config = {
            'innodb-buffer-pool-size': '256M',
            'max-connections': 1000,
        }
        cinder_config = {
            'block-device': 'None',
            'glance-api-version': '2'
        }
        cinder_datera_config = {
            'san_ip': '172.19.1.222',
            'san_login': 'admin',
            'san_password': 'password'
        }
        configs = {
            'keystone': keystone_config,
            'percona-cluster': pxc_config,
            'cinder': cinder_config,
            'cinder-datera': cinder_datera_config
        }
        super(CinderDateraBasicDeployment,
              self)._configure_services(configs)

    def _initialize_tests(self):
        """Perform final initialization before tests get run."""
        # Access the sentries for inspecting service units
        self.pxc_sentry = self.d.sentry['percona-cluster'][0]
        self.keystone_sentry = self.d.sentry['keystone'][0]
        self.rabbitmq_sentry = self.d.sentry['rabbitmq-server'][0]
        self.cinder_sentry = self.d.sentry['cinder'][0]
        self.cinder_datera_sentry = self.d.sentry['cinder-datera'][0]
        u.log.debug('openstack release val: {}'.format(
            self._get_openstack_release()))
        u.log.debug('openstack release str: {}'.format(
            self._get_openstack_release_string()))

        # Authenticate admin with keystone
        self.keystone_session, self.keystone = u.get_default_keystone_session(
            self.keystone_sentry,
            openstack_release=self._get_openstack_release())

        # Authenticate admin with cinder endpoint
        if self._get_openstack_release() >= self.xenial_pike:
            api_version = 2
        else:
            api_version = 1

        # Authenticate admin with keystone
        self.keystone = u.authenticate_keystone_admin(self.keystone_sentry,
                                                      user='admin',
                                                      password='openstack',
                                                      tenant='admin')
        # Authenticate admin with cinder endpoint
        self.cinder = u.authenticate_cinder_admin(self.keystone, api_version)

    def test_102_services(self):
        """Verify the expected services are running on the service units."""
        if self._get_openstack_release() >= self.xenial_ocata:
            cinder_services = ['apache2',
                               'cinder-scheduler',
                               'cinder-volume']
        else:
            cinder_services = ['cinder-api',
                               'cinder-scheduler',
                               'cinder-volume']
        services = {
            self.cinder_sentry: cinder_services,
        }

        ret = u.validate_services_by_name(services)
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

    def test_110_users(self):
        """Verify expected users."""
        u.log.debug('Checking keystone users...')
        expected = [
            {'name': 'cinder_cinderv2',
             'enabled': True,
             'tenantId': u.not_null,
             'id': u.not_null,
             'email': 'juju@localhost'},
            {'name': 'admin',
             'enabled': True,
             'tenantId': u.not_null,
             'id': u.not_null,
             'email': 'juju@localhost'}
        ]
        actual = self.keystone.users.list()
        ret = u.validate_user_data(expected, actual)
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

    def test_112_service_catalog(self):
        """Verify that the service catalog endpoint data"""
        u.log.debug('Checking keystone service catalog...')
        u.log.debug('Checking keystone service catalog...')
        endpoint_vol = {'adminURL': u.valid_url,
                        'region': 'RegionOne',
                        'publicURL': u.valid_url,
                        'internalURL': u.valid_url}
        endpoint_id = {'adminURL': u.valid_url,
                       'region': 'RegionOne',
                       'publicURL': u.valid_url,
                       'internalURL': u.valid_url}
        if self._get_openstack_release() >= self.trusty_icehouse:
            endpoint_vol['id'] = u.not_null
            endpoint_id['id'] = u.not_null

        if self._get_openstack_release() >= self.xenial_pike:
            # Pike and later
            expected = {'identity': [endpoint_id],
                        'volumev2': [endpoint_id]}
        else:
            # Ocata and prior
            expected = {'identity': [endpoint_id],
                        'volume': [endpoint_id]}
        actual = self.keystone.service_catalog.get_endpoints()

        ret = u.validate_svc_catalog_endpoint_data(
            expected,
            actual,
            openstack_release=self._get_openstack_release())
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

    def test_114_cinder_endpoint(self):
        """Verify the cinder endpoint data."""
        u.log.debug('Checking cinder endpoint...')
        endpoints = self.keystone.endpoints.list()
        admin_port = internal_port = public_port = '8776'
        if self._get_openstack_release() >= self.xenial_queens:
            expected = {
                'id': u.not_null,
                'region': 'RegionOne',
                'region_id': 'RegionOne',
                'url': u.valid_url,
                'interface': u.not_null,
                'service_id': u.not_null}
            ret = u.validate_v3_endpoint_data(
                endpoints,
                admin_port,
                internal_port,
                public_port,
                expected,
                6)
        else:
            expected = {
                'id': u.not_null,
                'region': 'RegionOne',
                'adminurl': u.valid_url,
                'internalurl': u.valid_url,
                'publicurl': u.valid_url,
                'service_id': u.not_null}
            ret = u.validate_v2_endpoint_data(
                endpoints,
                admin_port,
                internal_port,
                public_port,
                expected)
        if ret:
            amulet.raise_status(amulet.FAIL,
                                msg='cinder endpoint: {}'.format(ret))

    def test_202_cinderdatera_cinder_backend_relation(self):
        u.log.debug('Checking cinder-datera:storage-backend to '
                    'cinder:storage-backend relation data...')
        unit = self.cinder_datera_sentry
        relation = ['storage-backend', 'cinder:storage-backend']

        sub = {"cinder":
               {"/etc/cinder/cinder.conf":
                {"sections":
                 {"cinder-datera": [
                     ["san_ip", "172.19.1.222"],
                     ["san_login", "admin"],
                     ["san_password", "password"],
                     ["volume_backend_name", "cinder-datera"],
                     ["volume_driver",
                      "cinder.volume.drivers.datera."
                      "datera_iscsi.DateraDriver"],
                     ["use_multipath_for_image_xfer", "true"],
                 ]}}}}

        expected = {
            'subordinate_configuration': json.dumps(sub),
            'private-address': u.valid_ip,
            'backend_name': 'cinder-datera',
            'egress-subnets': lambda x: True,
            'ingress-address': u.valid_ip,
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error(
                'cinder cinder-datera storage-backend', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_203_cinder_cinderdatera_backend_relation(self):
        u.log.debug('Checking cinder:storage-backend to '
                    'cinder-datera:storage-backend relation data...')
        unit = self.cinder_sentry
        relation = ['storage-backend', 'cinder-datera:storage-backend']

        expected = {
            'private-address': u.valid_ip,
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error(
                'cinder cinder-datera storage-backend', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_204_mysql_cinder_db_relation(self):
        """Verify the mysql:glance shared-db relation data"""
        u.log.debug('Checking mysql:cinder db relation data...')
        unit = self.pxc_sentry
        relation = ['shared-db', 'cinder:shared-db']
        expected = {
            'private-address': u.valid_ip,
            'db_host': u.valid_ip
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error('mysql shared-db', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_205_cinder_mysql_db_relation(self):
        """Verify the cinder:mysql shared-db relation data"""
        u.log.debug('Checking cinder:mysql db relation data...')
        unit = self.cinder_sentry
        relation = ['shared-db', 'percona-cluster:shared-db']
        expected = {
            'private-address': u.valid_ip,
            'hostname': u.valid_ip,
            'username': 'cinder',
            'database': 'cinder'
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error('cinder shared-db', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_206_keystone_cinder_id_relation(self):
        """Verify the keystone:cinder identity-service relation data"""
        u.log.debug('Checking keystone:cinder id relation data...')
        unit = self.keystone_sentry
        relation = ['identity-service',
                    'cinder:identity-service']
        expected = {
            'service_protocol': 'http',
            'service_tenant': 'services',
            'admin_token': 'ubuntutesting',
            'service_password': u.not_null,
            'service_port': '5000',
            'auth_port': '35357',
            'auth_protocol': 'http',
            'private-address': u.valid_ip,
            'auth_host': u.valid_ip,
            'service_username': 'cinder_cinderv2',
            'service_tenant_id': u.not_null,
            'service_host': u.valid_ip
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error('identity-service cinder', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_207_cinder_keystone_id_relation(self):
        """Verify the cinder:keystone identity-service relation data"""
        u.log.debug('Checking cinder:keystone id relation data...')
        unit = self.cinder_sentry
        relation = ['identity-service',
                    'keystone:identity-service']
        expected = {
            'private-address': u.valid_ip
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error('cinder identity-service', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_208_rabbitmq_cinder_amqp_relation(self):
        """Verify the rabbitmq-server:cinder amqp relation data"""
        u.log.debug('Checking rmq:cinder amqp relation data...')
        unit = self.rabbitmq_sentry
        relation = ['amqp', 'cinder:amqp']
        expected = {
            'private-address': u.valid_ip,
            'password': u.not_null,
            'hostname': u.valid_ip
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error('amqp cinder', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_209_cinder_rabbitmq_amqp_relation(self):
        """Verify the cinder:rabbitmq-server amqp relation data"""
        u.log.debug('Checking cinder:rmq amqp relation data...')
        unit = self.cinder_sentry
        relation = ['amqp', 'rabbitmq-server:amqp']
        expected = {
            'private-address': u.valid_ip,
            'vhost': 'openstack',
            'username': u.not_null
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            msg = u.relation_error('cinder amqp', ret)
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_300_cinder_config(self):
        """Verify the data in the cinder.conf file."""
        u.log.debug('Checking cinder config file data...')
        unit = self.cinder_sentry
        conf = '/etc/cinder/cinder.conf'
        unit_mq = self.rabbitmq_sentry
        rel_mq_ci = unit_mq.relation('amqp', 'cinder:amqp')

        dat_backend = 'cinder-datera'
        expected = {
            'DEFAULT': {
                'debug': 'False',
                'verbose': 'False',
                'auth_strategy': 'keystone',
                'enabled_backends': dat_backend
            },
            dat_backend: {
                'san_ip': '172.19.1.222',
                'san_login': 'admin',
                'san_password': 'password',
                'volume_backend_name': dat_backend,
                'volume_driver': (
                    'cinder.volume.drivers.datera.datera_iscsi.DateraDriver')
            }
        }

        expected_rmq = {
            'rabbit_userid': 'cinder',
            'rabbit_virtual_host': 'openstack',
            'rabbit_password': rel_mq_ci['password'],
            'rabbit_host': rel_mq_ci['hostname'],
        }

        if self._get_openstack_release() >= self.trusty_kilo:
            # Kilo or later
            expected['oslo_messaging_rabbit'] = expected_rmq
        else:
            # Juno or earlier
            expected['DEFAULT'].update(expected_rmq)

        for section, pairs in expected.iteritems():
            ret = u.validate_config_data(unit, conf, section, pairs)
            if ret:
                message = "cinder config error: {}".format(ret)
                amulet.raise_status(amulet.FAIL, msg=message)

    def test_400_cinder_api_connection(self):
        """Simple api call to check service is up and responding"""
        u.log.debug('Checking basic cinder api functionality...')
        check = list(self.cinder.volumes.list())
        u.log.debug('Cinder api check (volumes.list): {}'.format(check))
        assert(check == [])

    def test_402_create_delete_volume(self):
        """Create a cinder volume and delete it."""
        u.log.debug('Creating, checking and deleting cinder volume...')
        vol_new = u.create_cinder_volume(self.cinder)
        vol_id = vol_new.id
        u.delete_resource(self.cinder.volumes, vol_id, msg="cinder volume")
