#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""support generic records

Revision ID: 6039683b85d7
Revises: 9099de8ae11c
Create Date: 2024-11-24 14:19:51.523038

"""
from alembic import op
from designate.storage.sqlalchemy.types import DNSRecordTypes


# revision identifiers, used by Alembic.
revision = '6039683b85d7'
down_revision = '9099de8ae11c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("recordsets") as batch_op:
        batch_op.alter_column('type', nullable=True, type_=DNSRecordTypes)
