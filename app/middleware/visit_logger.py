from flask import request, make_response
from app import db
from app.models import VisitLog
import uuid
from datetime import datetime


def init_visit_logger(app):
    @app.before_request
    def log_visit():
        if request.endpoint and request.endpoint not in ['static', 'favicon']:
            try:
                visit = VisitLog(
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string[:200],
                    page_url=request.url[:100],
                    referrer=request.referrer[:100] if request.referrer else None,
                    timestamp=datetime.utcnow()
                )
                db.session.add(visit)
                db.session.commit()
            except Exception as e:
                app.logger.error(f"Error logging visit: {str(e)}")
                db.session.rollback()

        if not request.cookies.get('visitor_id'):
            response = make_response()
            response.set_cookie(
                'visitor_id',
                value=str(uuid.uuid4()),
                max_age=30 * 24 * 60 * 60,
                httponly=True
            )
            return response