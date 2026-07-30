from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.study import StudyActivity
from app.schemas.study import StudyActivityCreate, StudyActivityUpdate, StudySummary


def add_study_activity(db: Session, user_id: int, data: StudyActivityCreate) -> StudyActivity:
    activity = StudyActivity(
        user_id=user_id,
        subject=data.subject,
        study_hours=data.study_hours,
        performance_score=data.performance_score or 80.0,
        task_completion_rate=data.task_completion_rate or 100.0,
        activity_date=data.activity_date,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_study_activities(
    db: Session,
    user_id: int,
    subject: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[StudyActivity]:
    query = db.query(StudyActivity).filter(StudyActivity.user_id == user_id)
    if subject:
        query = query.filter(StudyActivity.subject == subject)
    return query.order_by(StudyActivity.activity_date.desc()).offset(skip).limit(limit).all()


def get_study_activity_by_id(db: Session, activity_id: int, user_id: int) -> Optional[StudyActivity]:
    return db.query(StudyActivity).filter(
        StudyActivity.activity_id == activity_id,
        StudyActivity.user_id == user_id
    ).first()


def update_study_activity(
    db: Session,
    activity_id: int,
    user_id: int,
    data: StudyActivityUpdate,
) -> Optional[StudyActivity]:
    activity = get_study_activity_by_id(db, activity_id, user_id)
    if not activity:
        return None

    if data.subject is not None:
        activity.subject = data.subject
    if data.study_hours is not None:
        activity.study_hours = data.study_hours
    if data.performance_score is not None:
        activity.performance_score = data.performance_score
    if data.task_completion_rate is not None:
        activity.task_completion_rate = data.task_completion_rate
    if data.activity_date is not None:
        activity.activity_date = data.activity_date

    db.commit()
    db.refresh(activity)
    return activity


def delete_study_activity(db: Session, activity_id: int, user_id: int) -> bool:
    activity = get_study_activity_by_id(db, activity_id, user_id)
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True


def get_study_summary(db: Session, user_id: int) -> StudySummary:
    activities = db.query(StudyActivity).filter(StudyActivity.user_id == user_id).all()

    if not activities:
        return StudySummary(
            avg_focus_score=0.0,
            task_completion_rate=0.0,
            total_hours=0.0,
            peak_hours="09:00 - 12:00",
            subject_breakdown={},
        )

    tot_hours = sum(a.study_hours for a in activities)
    avg_focus = sum(a.performance_score or 0.0 for a in activities) / len(activities)
    avg_comp = sum(a.task_completion_rate for a in activities) / len(activities)

    subj_breakdown: Dict[str, float] = {}
    for a in activities:
        subj_breakdown[a.subject] = subj_breakdown.get(a.subject, 0.0) + a.study_hours

    return StudySummary(
        avg_focus_score=round(avg_focus, 1),
        task_completion_rate=round(avg_comp, 1),
        total_hours=round(tot_hours, 1),
        peak_hours="09:00 - 12:00 (Morning)",
        subject_breakdown={k: round(v, 1) for k, v in subj_breakdown.items()},
    )
