#!/usr/bin/python

import sys
import json
import subprocess

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    service_name,
    relation_set,
    relation_ids,
    log
)

from cinder_contexts import DateraSubordinateContext
from charmhelpers.payload.execd import execd_preinstall

hooks = Hooks()

def juju_log(msg):
    log('[cinder-datera] %s' % msg)

@hooks.hook('install')
def install():
    execd_preinstall()


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


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        juju_log('Unknown hook {} - skipping.'.format(e))
