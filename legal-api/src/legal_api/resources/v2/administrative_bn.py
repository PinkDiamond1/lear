# Copyright © 2022 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API endpoints for managing an Administrative BN resource."""
import uuid
from http import HTTPStatus

from flask import Blueprint, current_app
from flask_cors import cross_origin
from sentry_sdk import capture_message

from legal_api.models import Business, UserRoles
from legal_api.services import queue
from legal_api.utils.auth import jwt
from legal_api.utils.datetime import datetime


bp = Blueprint('ADMINISTRATIVE_BN', __name__, url_prefix='/api/v2/admin/bn')


@bp.route('<string:identifier>', methods=['POST'])
@bp.route('<string:identifier>/<string:business_number>', methods=['POST'])
@cross_origin(origin='*')
@jwt.has_one_of_roles([UserRoles.admin_edit])
def create_bn_request(identifier: str, business_number: str = None):
    """Create a bn request."""
    business = Business.find_by_identifier(identifier)
    if business is None:
        return ({'message': 'A valid business is required.'}, HTTPStatus.BAD_REQUEST)

    publish_entity_event(business, request_name='BN15', business_number=business_number)
    return {'message': 'BN request queued.'}, HTTPStatus.CREATED


def publish_entity_event(business: Business,
                         request_name: str = None,
                         message_id: str = None,
                         business_number: str = None):
    """Publish the admin message on to the NATS events subject."""
    try:
        payload = {
            'specversion': '1.x-wip',
            'type': 'bc.registry.admin.bn',
            'source': ''.join([current_app.config.get('LEGAL_API_BASE_URL'), '/', business.identifier]),
            'id': message_id or str(uuid.uuid4()),
            'time': datetime.utcnow().isoformat(),
            'datacontenttype': 'application/json',
            'identifier': business.identifier,
            'data': {
                'header': {
                    'request': request_name,
                    'businessNumber': business_number
                },
                'business': {'identifier': business.identifier}
            }
        }
        subject = current_app.config.get('NATS_ENTITY_EVENT_SUBJECT')
        queue.publish_json(payload, subject)
    except Exception as err:  # pylint: disable=broad-except; we don't want to fail out the filing, so ignore all.
        capture_message('Queue Publish Admin Event Error: business.id=' + str(business.id) + str(err), level='error')
        current_app.logger.error('Queue Publish Event Error: business.id=%s', business.id, exc_info=True)
        raise err
