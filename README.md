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
  - default: v2018.11.14.0

If none of the above options are provided, the juju installer will try to
download the source from Datera's github and use the v2018.11.14.0 tag for
deployment.

# Contact Information

Matt Smith <mss@datera.io>
