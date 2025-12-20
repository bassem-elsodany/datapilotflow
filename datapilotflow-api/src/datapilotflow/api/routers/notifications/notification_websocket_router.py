"""
Notification WebSocket Router - Real-time Notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from loguru import logger
import json
import asyncio

from datapilotflow.api.routers.auth.auth_router import validate_jwt_token
from datapilotflow.services.notification.notification_websocket_service import NotificationWebSocketService
from datapilotflow.config import settings

router = APIRouter(prefix="/ws/notifications", tags=["Notifications WebSocket"])
# Use singleton instance
websocket_service = NotificationWebSocketService()


@router.websocket("")
async def notification_websocket(websocket: WebSocket, token: str = Query(None)):
    """WebSocket endpoint for real-time notification delivery."""
    logger.debug("Notification WebSocket connection attempt")
    
    if not token:
        logger.error("No token provided for WebSocket connection")
        await websocket.close(code=4001, reason="Missing authentication token")
        return
    
    logger.debug(f"Token received: {token[:20]}...")
    
    try:
        logger.debug(f"Attempting to validate token for WebSocket connection")
        current_user = validate_jwt_token(token)
        logger.debug(f"Token validation result: {current_user is not None}")
        
        if not current_user:
            logger.error("Token validation failed - no user returned")
            await websocket.close(code=4001, reason="Invalid authentication token - please log out and log back in")
            return
        
        logger.debug(f"WebSocket authentication successful for user: {current_user.username}")
        
        await websocket.accept()
        logger.debug(f"Notification WebSocket connected for user: {current_user.username}")
        
        await websocket_service.connect_user(current_user.username, websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                
                if action == "subscribe":
                    await websocket_service.subscribe_user(current_user.username)
                    await websocket.send_json({
                        "type": "status", "action": "subscribed",
                        "message": "Successfully subscribed to notifications"
                    })
                
                elif action == "unsubscribe":
                    await websocket_service.unsubscribe_user(current_user.username)
                    await websocket.send_json({
                        "type": "status", "action": "unsubscribed",
                        "message": "Successfully unsubscribed from notifications"
                    })
                

                
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
                
                else:
                    await websocket.send_json({
                        "type": "error", "message": f"Unknown action: {action}"
                    })
                    
        except WebSocketDisconnect:
            logger.debug("Notification WebSocket client disconnected")
        finally:
            await websocket_service.disconnect_user(current_user.username)
            
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal server error")


@router.websocket("/{session_id}")
async def session_notification_websocket(websocket: WebSocket, session_id: str, token: str = Query(None)):
    """WebSocket endpoint for session-specific notifications."""
    logger.debug(f"Session notification WebSocket connection for session {session_id}")
    
    if not token:
        logger.error("No token provided for session WebSocket connection")
        await websocket.close(code=4001, reason="Missing authentication token")
        return
    
    logger.debug(f"Session token received: {token[:20]}...")
    
    try:
        current_user = validate_jwt_token(token)
        logger.debug(f"Session token validation result: {current_user is not None}")
        
        if not current_user:
            logger.error("Session token validation failed - no user returned")
            await websocket.close(code=4001, reason="Invalid authentication token - please log out and log back in")
            return
        
        await websocket.accept()
        await websocket_service.connect_user_to_session(current_user.username, session_id, websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                
                if action == "subscribe":
                    await websocket_service.subscribe_user_to_session(current_user.username, session_id)
                    await websocket.send_json({
                        "type": "status", "action": "subscribed", "session_id": session_id
                    })
                
                elif action == "get_notifications":
                    notifications = await websocket_service.get_session_notifications(
                        current_user.username, session_id
                    )
                    await websocket.send_json({
                        "type": "notifications", "action": "session",
                        "session_id": session_id, "data": notifications
                    })
                
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
                
                else:
                    await websocket.send_json({
                        "type": "error", "message": f"Unknown action: {action}"
                    })
                    
        except WebSocketDisconnect:
            logger.debug("Session notification WebSocket client disconnected")
        finally:
            await websocket_service.disconnect_user_from_session(current_user.username, session_id)
            
    except Exception as e:
        logger.error(f"Session notification WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal server error")
