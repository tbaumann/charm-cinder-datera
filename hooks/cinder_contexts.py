from charmhelpers.core.hookenv import (
    config,
    service_name
)

from charmhelpers.contrib.openstack.context import (
    OSContextGenerator,
)


class DateraIncompleteConfiguration(Exception):
    pass


class DateraSubordinateContext(OSContextGenerator):
    interfaces = ['datera']

    _config_keys = [
        'san_ip',
        'san_login',
        'san_password',
    ]

    def __call__(self):
        ctxt = []
        missing = []
        for k in self._config_keys:
            if config(k):
                ctxt.append(("{}".format(k.replace('-', '_')),
                             config(k)))
            else:
                missing.append(k)
        if missing:
            raise DateraIncompleteConfiguration(
                'Missing configuration: {}.'.format(missing)
            )

        service = service_name()
        ctxt.append(('volume_backend_name', service))
        volume_driver = (
            'cinder.volume.drivers.datera.datera_iscsi.DateraDriver'),
        ctxt.append(('volume_driver', volume_driver))
        ctxt.append(('use_multipath_for_image_xfer', 'true'))
        return {
            "cinder": {
                "/etc/cinder/cinder.conf": {
                    "sections": {
                        service: ctxt,
                    }
                }
            }
        }
