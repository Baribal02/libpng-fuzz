#!/usr/bin/env python
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
"""Custom options for sqlite3."""
import os

import package


class Package(package.Package):  # pylint: disable=too-few-public-methods
  """sqlite3 package."""

  def __init__(self, apt_version):
    super(Package, self).__init__('sqlite3', apt_version)

  def pre_build(self, source_directory, _env, _custom_bin_dir):  # pylint: disable=no-self-use
    """Pre-build configuration for sqlite3."""
    os.system('sed -i "s/package ifneeded sqlite3//" %s/debian/rules' %
              source_directory)
