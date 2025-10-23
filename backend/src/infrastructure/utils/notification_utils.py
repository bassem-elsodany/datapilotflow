"""
Notification Utilities

This module provides utility functions for firing notifications for specific events
throughout the SkillPilot application using an event-driven architecture with RabbitMQ.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import asyncio

from src.domain.notification import (
    NotificationCreate, NotificationType, NotificationPriority, NotificationStatus
)
from src.services.notification.dao.notification_service import NotificationService
from src.services.notification.notification_event_service import (
    fire_session_created_event,
    fire_session_deleted_event,
    fire_interview_started_event,
    fire_resume_analysis_completed_event,
    fire_job_analysis_completed_event,
    fire_error_event,
    fire_job_deleted_event,
    fire_resume_deleted_event
)

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manager for firing notifications for specific events using event-driven architecture"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    async def fire_session_created_notification(
        self, 
        user_id: str, 
        session_id: str, 
        session_name: str,
        job_title: Optional[str] = None
    ) -> bool:
        """Fire notification when a new interview session is created"""
        try:
            await fire_session_created_event(user_id, session_id, session_name, job_title)
            logger.info(f"Fired session created event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing session created notification: {e}")
            return False
    
    async def fire_session_deleted_notification(
        self, 
        user_id: str, 
        session_id: str, 
        session_name: str
    ) -> bool:
        """Fire notification when an interview session is deleted"""
        try:
            await fire_session_deleted_event(user_id, session_id, session_name)
            logger.info(f"Fired session deleted event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing session deleted notification: {e}")
            return False
    
    async def fire_interview_started_notification(
        self, 
        user_id: str, 
        session_id: str, 
        session_name: str,
        candidate_name: Optional[str] = None
    ) -> bool:
        """Fire notification when an interview is started"""
        try:
            await fire_interview_started_event(user_id, session_id, session_name, candidate_name)
            logger.info(f"Fired interview started event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing interview started notification: {e}")
            return False
    
    async def fire_resume_analysis_completed_notification(
        self, 
        user_id: str, 
        session_id: str, 
        candidate_name: str,
        analysis_summary: Optional[str] = None
    ) -> bool:
        """Fire notification when resume analysis is completed"""
        try:
            await fire_resume_analysis_completed_event(user_id, session_id, candidate_name, analysis_summary)
            logger.info(f"Fired resume analysis completed event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing resume analysis completed notification: {e}")
            return False
    
    async def fire_job_analysis_completed_notification(
        self, 
        user_id: str, 
        session_id: str, 
        job_title: str,
        company_name: Optional[str] = None
    ) -> bool:
        """Fire notification when job analysis is completed"""
        try:
            await fire_job_analysis_completed_event(user_id, session_id, job_title, company_name)
            logger.info(f"Fired job analysis completed event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing job analysis completed notification: {e}")
            return False
    
    async def fire_error_notification(
        self, 
        user_id: str, 
        session_id: Optional[str], 
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Fire notification for errors"""
        try:
            await fire_error_event(user_id, session_id, error_type, error_message, context)
            logger.info(f"Fired error event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing error notification: {e}")
            return False

    async def fire_job_deleted_notification(
        self, 
        user_id: str, 
        job_title: str,
        job_id: str
    ) -> bool:
        """Fire notification when a job description is deleted"""
        try:
            await fire_job_deleted_event(user_id, job_title, job_id)
            logger.info(f"Fired job deleted event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing job deleted notification: {e}")
            return False

    async def fire_resume_deleted_notification(
        self, 
        user_id: str, 
        candidate_name: str,
        candidate_id: str
    ) -> bool:
        """Fire notification when a resume is deleted"""
        try:
            await fire_resume_deleted_event(user_id, candidate_name, candidate_id)
            logger.info(f"Fired resume deleted event for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error firing resume deleted notification: {e}")
            return False


# Global notification manager instance
notification_manager = NotificationManager()


# Convenience functions for easy access
async def fire_interview_created_notification(user_id: str, interview_id: str, interview_name: str, job_title: Optional[str] = None) -> bool:
    """Fire notification when a new interview is created"""
    return await notification_manager.fire_session_created_notification(user_id, interview_id, interview_name, job_title)

async def fire_interview_deleted_notification(user_id: str, interview_id: str, interview_name: str) -> bool:
    """Fire notification when an interview is deleted"""
    return await notification_manager.fire_session_deleted_notification(user_id, interview_id, interview_name)

async def fire_interview_started_notification(user_id: str, interview_id: str, interview_name: str, candidate_name: Optional[str] = None) -> bool:
    """Fire notification when an interview is started"""
    return await notification_manager.fire_interview_started_notification(user_id, interview_id, interview_name, candidate_name)

async def fire_resume_analysis_completed_notification(user_id: str, interview_id: str, candidate_name: str, analysis_summary: Optional[str] = None) -> bool:
    """Fire notification when resume analysis is completed"""
    return await notification_manager.fire_resume_analysis_completed_notification(user_id, interview_id, candidate_name, analysis_summary)

async def fire_job_analysis_completed_notification(user_id: str, interview_id: str, job_title: str, company_name: Optional[str] = None) -> bool:
    """Fire notification when job analysis is completed"""
    return await notification_manager.fire_job_analysis_completed_notification(user_id, interview_id, job_title, company_name)

async def fire_error_notification(user_id: str, interview_id: Optional[str], error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Fire notification for errors"""
    return await notification_manager.fire_error_notification(user_id, interview_id, error_type, error_message, context)

async def fire_job_deleted_notification(user_id: str, job_title: str, job_id: str) -> bool:
    """Fire notification when a job description is deleted"""
    return await notification_manager.fire_job_deleted_notification(user_id, job_title, job_id)

async def fire_resume_deleted_notification(user_id: str, candidate_name: str, candidate_id: str) -> bool:
    """Fire notification when a resume is deleted"""
    return await notification_manager.fire_resume_deleted_notification(user_id, candidate_name, candidate_id)
