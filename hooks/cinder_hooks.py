#!/usr/bin/python

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
