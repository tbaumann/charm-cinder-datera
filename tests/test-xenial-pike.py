#!/usr/bin/env python
#
# Copyright 2016 Canonical Ltd
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

"""Amulet tests on a basic cinder-datera deployment on xenial-pike."""

from basic_deployment import CinderDateraBasicDeployment

if __name__ == '__main__':
    github_deployment = CinderDateraBasicDeployment(
        series='xenial',
        openstack='cloud:xenial-pike',
        source='cloud:xenial-updates/pike')
    github_deployment.run_tests()

    archive_deployment = CinderDateraBasicDeployment(
        series='xenial',
        openstack='cloud:xenial-pike',
        source='cloud:xenial-updates/pike',
        install_type='archive-url')
    archive_deployment.run_tests()
