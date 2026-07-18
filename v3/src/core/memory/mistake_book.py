import json, uuid, logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import MistakeBook as MistakeBookModel, MistakeNotification, MistakeNotification

logger = logging.getLogger(__name__)

EBBINGHAUS_INTERVALS = [0, 1, 2, 4, 7, 15, 30]

ERROR_CATEGORY_LABELS = {
    'concept_unclear': 'concept unclear',
    'careless': 'careless error',
    'wrong_approach': 'wrong approach',
    'incomplete': 'incomplete answer',
    'correct': 'correct',
}


class MistakeBook:
    '''Mistake book backed by MySQL via SQLAlchemy async'''

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def _session(self) -> AsyncSession:
        return self.session_factory()

    async def add_mistake(
        self,
        user_id: str,
        question: str,
        student_answer: str,
        reference_answer: str = '',
        error_category: str = 'concept_unclear',
        error_pattern: str = '',
        error_root_cause: str = '',
        knowledge_id: Optional[int] = None,
        knowledge_name: str = '',
        course_id: Optional[int] = None,
        diagnosis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = datetime.now()
        uid = int(user_id) if user_id else 0
        first_review = now + timedelta(days=EBBINGHAUS_INTERVALS[0])

        async with await self._session() as session:
            record = MistakeBookModel(
                user_id=uid,
                question=question,
                student_answer=student_answer,
                reference_answer=reference_answer,
                error_category=error_category,
                error_pattern=error_pattern,
                error_root_cause=error_root_cause,
                knowledge_id=knowledge_id,
                knowledge_name=knowledge_name,
                course_id=course_id,
                diagnosis=json.dumps(diagnosis, ensure_ascii=False) if isinstance(diagnosis, dict) else diagnosis,
                review_count=0,
                review_stage=0,
                next_review_at=first_review,
                mastered=0,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            result = self._to_dict(record)
            logger.info('Mistake added: user=%s, id=%s', user_id, record.id)
            return result

    async def get_mistake(self, mistake_id: int) -> Optional[Dict[str, Any]]:
        async with await self._session() as session:
            stmt = select(MistakeBookModel).where(
                MistakeBookModel.id == int(mistake_id),
                MistakeBookModel.deleted == 0,
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None

    async def delete_mistake(self, mistake_id: str) -> bool:
        async with await self._session() as session:
            stmt = (
                update(MistakeBookModel)
                .where(MistakeBookModel.id == int(mistake_id))
                .values(deleted=1)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def clear_all_mistakes(self, user_id: str) -> int:
        uid = int(user_id) if user_id else 0
        async with await self._session() as session:
            stmt = (
                update(MistakeBookModel)
                .where(MistakeBookModel.user_id == uid, MistakeBookModel.deleted == 0)
                .values(deleted=1)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount

    async def list_mistakes(
        self,
        user_id: str,
        course_id: Optional[int] = None,
        error_category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        uid = int(user_id) if user_id else 0
        async with await self._session() as session:
            conditions = [MistakeBookModel.user_id == uid, MistakeBookModel.deleted == 0]
            if course_id is not None:
                conditions.append(MistakeBookModel.course_id == course_id)
            if error_category:
                conditions.append(MistakeBookModel.error_category == error_category)
            stmt = (
                select(MistakeBookModel)
                .where(and_(*conditions))
                .order_by(MistakeBookModel.create_time.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [self._to_dict(r) for r in records]

    async def record_review(self, mistake_id: str, recalled: bool) -> Dict[str, Any]:
        mid = int(mistake_id)
        async with await self._session() as session:
            stmt = select(MistakeBookModel).where(
                MistakeBookModel.id == mid, MistakeBookModel.deleted == 0
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if not record:
                return {'success': False, 'error': 'not found'}
            new_count = record.review_count + 1
            new_stage = record.review_stage
            now = datetime.now()
            if recalled:
                new_stage = min(new_stage + 1, len(EBBINGHAUS_INTERVALS) - 1)
                if new_stage >= len(EBBINGHAUS_INTERVALS) - 1 and new_count >= 3:
                    record.mastered = 1
                    record.next_review_at = None
                else:
                    record.next_review_at = now + timedelta(days=EBBINGHAUS_INTERVALS[new_stage])
            else:
                new_stage = 0
                record.next_review_at = now + timedelta(days=EBBINGHAUS_INTERVALS[0])
            record.review_count = new_count
            record.review_stage = new_stage
            await session.commit()
            await session.refresh(record)
            return self._to_dict(record)

    async def get_due_reviews(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        uid = int(user_id) if user_id else 0
        now = datetime.now()
        async with await self._session() as session:
            stmt = (
                select(MistakeBookModel)
                .where(
                    MistakeBookModel.user_id == uid,
                    MistakeBookModel.deleted == 0,
                    MistakeBookModel.mastered == 0,
                    MistakeBookModel.review_stage == 0,
                )
                .order_by(MistakeBookModel.create_time.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [self._to_dict(r) for r in records]

    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        uid = int(user_id) if user_id else 0
        now = datetime.now()
        async with await self._session() as session:
            total_stmt = select(func.count()).select_from(MistakeBookModel).where(
                MistakeBookModel.user_id == uid, MistakeBookModel.deleted == 0
            )
            total = (await session.execute(total_stmt)).scalar() or 0
            due_stmt = select(func.count()).select_from(MistakeBookModel).where(
                MistakeBookModel.user_id == uid,
                MistakeBookModel.deleted == 0,
                MistakeBookModel.mastered == 0,
                MistakeBookModel.review_stage == 0,
            )
            due = (await session.execute(due_stmt)).scalar() or 0
            future = now + timedelta(days=7)
            upcoming_stmt = select(func.count()).select_from(MistakeBookModel).where(
                MistakeBookModel.user_id == uid,
                MistakeBookModel.deleted == 0,
                MistakeBookModel.mastered == 0,
                MistakeBookModel.review_stage > 0,
            )
            upcoming = (await session.execute(upcoming_stmt)).scalar() or 0
            patterns = await self.get_error_patterns(user_id)
            return {
                'total_mistakes': int(total),
                'due_reviews': int(due),
                'upcoming_reviews_7d': int(upcoming),
                'weak_points': patterns.get('weak_points', []),
                'primary_error_type': patterns.get('primary_error_type', ''),
                'by_category': patterns.get('by_category', {}),
            }

    async def get_error_patterns(self, user_id: str) -> Dict[str, Any]:
        uid = int(user_id) if user_id else 0
        async with await self._session() as session:
            stmt = (
                select(
                    MistakeBookModel.error_category,
                    func.count().label('cnt'),
                    func.group_concat(MistakeBookModel.knowledge_name.distinct()).label('topics'),
                )
                .where(MistakeBookModel.user_id == uid, MistakeBookModel.deleted == 0)
                .group_by(MistakeBookModel.error_category)
                .order_by(func.count().desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
        by_category = {}
        primary = ''
        max_cnt = 0
        weak_points = []
        for row in rows:
            cat = row.error_category or 'unknown'
            cnt = int(row.cnt)
            by_category[cat] = cnt
            if cnt > max_cnt:
                max_cnt = cnt
                primary = cat
            if row.topics:
                weak_points.extend([t.strip() for t in row.topics.split(',') if t.strip()])
        return {
            'primary_error_type': primary,
            'by_category': by_category,
            'weak_points': list(set(weak_points)),
        }

    async def generate_daily_review_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        due = await self.get_due_reviews(user_id, limit=50)
        notifications = []
        now = datetime.now()
        uid = int(user_id) if user_id else 0
        async with await self._session() as session:
            for m in due:
                stage = m.get('review_stage', 0)
                stage_desc = 'round {}'.format(stage + 1) if stage < len(EBBINGHAUS_INTERVALS) else 'final review'
                # Persist to DB
                notif = MistakeNotification(
                    user_id=uid,
                    mistake_id=int(m['id']),
                    type='review_due',
                    title='Review due',
                    message='[{}] {} review due'.format(m.get('knowledge_name', 'unknown'), stage_desc),
                    error_category=m.get('error_category', ''),
                    knowledge_name=m.get('knowledge_name', ''),
                    review_stage=stage,
                )
                session.add(notif)
                await session.flush()
                notifications.append({
                    'id': str(notif.id),
                    'user_id': user_id,
                    'mistake_id': m['id'],
                    'type': 'review_due',
                    'title': 'Review due',
                    'message': '[{}] {} review due'.format(m.get('knowledge_name', 'unknown'), stage_desc),
                    'error_category': m.get('error_category', ''),
                    'knowledge_name': m.get('knowledge_name', ''),
                    'review_stage': stage,
                    'created_at': now.isoformat(),
                })
            try:
                await session.commit()
            except Exception as e:
                logger.warning('Failed to persist notifications: %s', e)
        return notifications

    async def get_pending_notifications(self, user_id: str, limit: int = 10, mark_read: bool = False) -> List[Dict[str, Any]]:
        uid = int(user_id) if user_id else 0
        async with await self._session() as session:
            stmt = (
                select(MistakeNotification)
                .where(MistakeNotification.user_id == uid, MistakeNotification.is_read == 0)
                .order_by(MistakeNotification.create_time.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            notifications = []
            for r in records:
                notifications.append({
                    'id': str(r.id),
                    'user_id': str(r.user_id),
                    'mistake_id': str(r.mistake_id),
                    'type': r.type or 'review_due',
                    'title': r.title or '',
                    'message': r.message or '',
                    'error_category': r.error_category or '',
                    'knowledge_name': r.knowledge_name or '',
                    'review_stage': r.review_stage or 0,
                    'is_read': bool(r.is_read),
                    'created_at': r.create_time.isoformat() if r.create_time else '',
                })
            if mark_read and records:
                ids = [r.id for r in records]
                stmt_up = update(MistakeNotification).where(MistakeNotification.id.in_(ids)).values(is_read=1)
                await session.execute(stmt_up)
                await session.commit()
            return notifications

    async def clear_notifications(self, user_id: str) -> int:
        return 0

    @staticmethod
    def _to_dict(record: MistakeBookModel) -> Dict[str, Any]:
        diagnosis = record.diagnosis
        if isinstance(diagnosis, str):
            try:
                diagnosis = json.loads(diagnosis)
            except (json.JSONDecodeError, TypeError):
                diagnosis = {}
        return {
            'id': str(record.id),
            'user_id': str(record.user_id),
            'question': record.question or '',
            'student_answer': record.student_answer or '',
            'reference_answer': record.reference_answer or '',
            'error_category': record.error_category or 'concept_unclear',
            'error_pattern': record.error_pattern or '',
            'error_root_cause': record.error_root_cause or '',
            'knowledge_id': record.knowledge_id,
            'knowledge_name': record.knowledge_name or '',
            'course_id': record.course_id,
            'diagnosis': diagnosis,
            'review_count': record.review_count or 0,
            'review_stage': record.review_stage or 0,
            'next_review_at': record.next_review_at.isoformat() if record.next_review_at else None,
            'mastered': bool(record.mastered),
            'created_at': record.create_time.isoformat() if record.create_time else '',
        }
