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

# Contact Information

Matt Smith <mss@datera.io>
