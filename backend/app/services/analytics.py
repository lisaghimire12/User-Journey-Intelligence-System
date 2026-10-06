from collections import Counter
from backend.app.models.models import Event,Session,Journey
def rebuild(db):
    events=db.query(Event).order_by(Event.session_id,Event.timestamp,Event.sequence_number).all()
    groups={}
    for e in events: groups.setdefault(e.session_id,[]).append(e)
    db.query(Session).delete(); db.query(Journey).delete()
    for sid,evs in groups.items():
        pages=[e.page for e in evs]; names=[e.event_name for e in evs]
        start,end=evs[0].timestamp,evs[-1].timestamp
        converted="purchase" in names
        db.add(Session(session_id=sid,anonymous_user_id=evs[0].anonymous_user_id,start_time=start,end_time=end,event_count=len(evs),converted=converted,source=evs[0].source))
        counts=Counter(pages); repeated=sum(max(0,n-1) for n in counts.values())
        loops=sum(1 for i in range(1,len(pages)) if pages[i]==pages[i-1])
        abandonment=None if converted else ("checkout" if "begin_checkout" in names else "cart" if "add_to_cart" in names else "product" if "view_item" in names else "discovery")
        db.add(Journey(session_id=sid,sequence=names,journey_length=len(names),duration_seconds=(end-start).total_seconds(),unique_pages=len(set(pages)),repeated_pages=repeated,loop_count=loops,entry_page=pages[0],exit_page=pages[-1],converted=converted,abandonment_stage=abandonment))
    db.commit()
    return len(groups)
