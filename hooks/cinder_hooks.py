#!/usr/bin/python
# Copyright 2018 Datera Inc
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

import sys
import json

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    service_name,
    relation_set,
    relation_ids,
)

from cinder_contexts import DateraSubordinateContext
from datera_utils import (
        install as _install,
        remove as _remove,
        dlog
)

hooks = Hooks()


@hooks.hook('config-changed',
            'upgrade-charm')
def upgrade_charm():
    for rid in relation_ids('storage-backend'):
        storage_backend(rid)


@hooks.hook('storage-backend-relation-joined',
            'storage-backend-relation-changed')
def storage_backend(rel_id=None):
    relation_set(
        relation_id=rel_id,
        backend_name=service_name(),
        subordinate_configuration=json.dumps(DateraSubordinateContext()())
    )


@hooks.hook('storage-backend-relation-departed')
def storage_backend_remove(rel_id=None):
    dlog("storage_backend_remove called")
    _remove()


@hooks.hook('start')
def install():
    dlog("Install called")
    _install()


@hooks.hook('stop')
def noop():
    dlog("noop (stop) called")
    pass


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        dlog('Unknown hook {} - skipping.'.format(e))
