# Datera Storage Backend for Cinder

This charm provides an Datera storage backend for use with the Cinder
charm.

## Configuration

The cinder-datera charm has the following mandatory configuration.

1. To access the Datera array:
 - san\_ip
 - san\_login
 - san\_password

Add this configuration in the config.yaml file before deploying the charm.

## Usage

    juju deploy cinder
    juju deploy cinder-datera
    juju config cinder-datera san_ip=1.1.1.1 san_login=mylogin san_password=mypass
    juju add-relation cinder-datera cinder

## Local Usage

    juju deploy cinder
    git clone http://github.com/Datera/charm-cinder-datera
    charm build ./charm-cinder-datera/ -o .
    juju deploy ./builds/cinder-datera
    juju config cinder-datera san_ip=1.1.1.1 san_login=mylogin san_password=mypass
    juju add-relation cinder-datera cinder

## Other Config Options

- install\_type
  - description: What kind of installation media will be provided
  - choices: github, archive-url, archive-local
  - default: github
- install\_url
  - description: The URL to use when performing a github or archive-url install
  - default: http://github.com/Datera/cinder-driver
- install\_archive\_path
  - description: The location locally where a cinder-driver archive is provided for archive-url installs
  - default: ""
- install\_tag:
  - description: The git tag to use when downloading from github
  - default: master

If none of the above options are provided, the juju installer will try to
download the source from Datera's github and use the master branch for
deployment.

# Contact Information

Matt Smith <mss@datera.io>
