# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Copy over all directors into the party_roles/parties tables. Meant to run once in each environment
after the database has been migrated.
"""
from dotenv import load_dotenv, find_dotenv

from flask import Flask
from legal_api import db
from legal_api.config import get_named_config
from legal_api.models import Director, Party, PartyRole

import copy

load_dotenv(find_dotenv())

FLASK_APP = Flask(__name__)
FLASK_APP.config.from_object(get_named_config('production'))
db.init_app(FLASK_APP)

def copy_over_dirs():
    # add directors as party members
    select_string = 'select * from directors'
    directors = db.session.execute(select_string)

    for row in directors:
        director_id = row[0]
        first_name = row[1]
        middle_initial = row[2]
        last_name = row[3]
        title = row[4]
        appointment_date = row[5]
        cessation_date = row[6]
        business_id = row[7]
        address_id = row[8]
        mailing_address_id = row[9]

        # initialize member
        member = Party(
            first_name=first_name,
            middle_initial=middle_initial,
            last_name=last_name,
            title=title,
            address_id=address_id,
            mailing_address_id=mailing_address_id
        )
        db.session.add(member)
        db.session.commit()
        # initialize member role
        member_role = PartyRole(
            role=PartyRole.RoleTypes.DIRECTOR.value,
            appointment_date=appointment_date,
            cessation_date=cessation_date,
            business_id=business_id,
            party_id=member.id
        )
        db.session.add(member_role)
        db.session.commit()

with FLASK_APP.app_context():
    copy_over_dirs()