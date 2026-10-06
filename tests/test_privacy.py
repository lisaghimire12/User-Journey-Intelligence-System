from datetime import datetime
from backend.app.privacy.privacy import minimize_event
def test_pseudonymization_and_minimization():
    x=minimize_event({"event_name":"view_item","anonymous_user_id":"raw","session_id":"raw2","page":"Product","timestamp":datetime.utcnow(),"sequence_number":1,"metadata":{"email":"x","variant":"8"}})
    assert x["anonymous_user_id"]!="raw"
    assert "email" not in x["metadata"]
