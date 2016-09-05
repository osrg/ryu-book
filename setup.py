# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Setup script for Ryu-Book.
"""
import os

import setuptools
from setuptools.command.install import install


class RyuBookInstall(install):
    """
    Installer command for Ryu-Book.

    This command does not install anything, but creates a symbolic link
    pointing to Ryu installed directory.
    """

    def run(self):
        current_dir = os.path.dirname(__file__)
        ryu_symlink = os.path.join(current_dir, 'ryu')
        if os.path.islink(ryu_symlink):
            os.unlink(ryu_symlink)

        import ryu
        ryu_dir = os.path.dirname(ryu.__file__)
        os.symlink(ryu_dir, ryu_symlink)

        install.run(self)


setuptools.setup(name='Ryu-Book',
                 version='1.0',
                 description='RYU SDN Framework',
                 author='RYU project team',
                 author_email='ryu-devel@lists.sourceforge.net',
                 url='http://osrg.github.io/ryu/',
                 cmdclass={'install': RyuBookInstall})
