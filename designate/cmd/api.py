# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

from designate.common import keystone
from designate import hookpoints
from designate import service
from designate import utils
from designate import version
from designate.api import service as api_service


CONF = cfg.CONF
CONF.import_opt('workers', 'designate.api', group='service:api')
CONF.import_opt('threads', 'designate.api', group='service:api')
cfg.CONF.import_group('keystone_authtoken', 'keystonemiddleware.auth_token')
keystone.register_keystone_opts(CONF)


def main():
    utils.read_config('designate', sys.argv)
    logging.setup(CONF, 'designate')
    gmr.TextGuruMeditation.setup_autorun(version)

    hookpoints.log_hook_setup()

    server = api_service.Service(threads=CONF['service:api'].threads)
    service.serve(server, workers=CONF['service:api'].workers)
    server.heartbeat_emitter.start()
    service.wait()
