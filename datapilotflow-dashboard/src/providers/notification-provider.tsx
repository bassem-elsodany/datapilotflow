import { Notification as NotificationType } from '@/api/entities/notifications';
import { apiEndpoints, apiUtils } from '@/config';
import { useAuth } from '@/hooks';
import {
  useDeleteNotification,
  useDismissNotification,
  useMarkAllNotificationsAsRead,
  useMarkNotificationAsRead
} from '@/hooks/api';
import { notifications as mantineNotifications } from '@mantine/notifications';
import React, { createContext, useContext, useEffect, useRef, useState } from 'react';

interface NotificationContextType {
  notifications: NotificationType[];
  unreadCount: number;
  isLoading: boolean;
  markAsRead: (notificationId: string) => void;
  dismiss: (notificationId: string) => void;
  delete: (notificationId: string) => void;
  markAllAsRead: () => void;
  refresh: () => void;
  showNotification: (title: string, message: string, type?: 'success' | 'error' | 'info') => void;
  hasNewNotifications: boolean;
  isWebSocketConnected: boolean;
}

export const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  // WebSocket-only state - no HTTP polling
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [hasNewNotifications, setHasNewNotifications] = useState(false);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const markAsReadMutation = useMarkNotificationAsRead();
  const dismissMutation = useDismissNotification();
  const deleteMutation = useDeleteNotification();
  const markAllAsReadMutation = useMarkAllNotificationsAsRead();

  // WebSocket connection management
  const connectWebSocket = () => {
    if (!isAuthenticated) return;

    const token = localStorage.getItem('jwt_token');
    if (!token) return;

    const wsUrl = apiUtils.buildWebSocketUrl(apiEndpoints.notifications.websocket.general, token);

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        // console.log('🔌 Notification WebSocket connected');
        setIsWebSocketConnected(true);

        // Subscribe to notifications
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: 'subscribe' }));
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // console.log('📨 Notification WebSocket message:', data);

          switch (data.type) {
            case 'notification':
              handleNotificationMessage(data);
              break;
            case 'status':
              handleStatusMessage(data);
              break;
            case 'pong':
              // Keep connection alive
              break;
            default:
            // console.log('Unknown WebSocket message type:', data.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        // console.log('🔌 Notification WebSocket disconnected:', event.code, event.reason);
        setIsWebSocketConnected(false);

        // Check if it's an authentication error
        if (event.code === 4001) {
          // console.log('🔐 Authentication error - token may be invalid');
          // Show notification to user
          mantineNotifications.show({
            title: 'Authentication Required',
            message: 'Please log out and log back in to enable real-time notifications',
            color: 'orange',
            autoClose: 5000,
          });
          // Don't reconnect for auth errors - user needs to log out and back in
          return;
        }

        // Reconnect if not a normal closure
        if (event.code !== 1000 && isAuthenticated) {
          // console.log('🔄 Attempting to reconnect in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ Notification WebSocket error:', error);
        setIsWebSocketConnected(false);
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setIsWebSocketConnected(false);
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User logout');
      wsRef.current = null;
    }

    setIsWebSocketConnected(false);
  };

  const handleNotificationMessage = (data: any) => {
    switch (data.action) {
      case 'new':
        // New notification received
        // console.log('🆕 New notification received:', data.data);

        // Add new notification to state
        const newNotification = {
          ...data.data,
          notification_id: data.data.id,
          created_at: data.data.created_at || new Date().toISOString(),
          status: 'pending',
          read_at: null,
          dismissed_at: null
        };

        setNotifications(prev => [newNotification, ...prev]);
        setUnreadCount(prev => prev + 1);
        setHasNewNotifications(true);

        // Show toast notification only if we have meaningful content
        const title = data.data.title?.trim();
        const message = data.data.message?.trim();

        if (title && message) {
          mantineNotifications.show({
            title: title,
            message: message,
            color: 'blue',
            autoClose: 3000,
          });
        } else {
          console.warn('Received notification with empty title or message:', data.data);
        }

        // Play notification sound
        playNotificationSound();
        break;

      default:
      // console.log('Unknown notification action:', data.action);
    }
  };

  const handleStatusMessage = (data: any) => {
    switch (data.action) {
      case 'subscribed':
        // console.log('✅ Subscribed to notifications');
        break;
      case 'unsubscribed':
        // console.log('❌ Unsubscribed from notifications');
        break;
      default:
      // console.log('Unknown status action:', data.action);
    }
  };

  const playNotificationSound = () => {
    try {
      // Try to use browser's notification sound
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('New Notification', {
          body: 'You have a new notification',
          silent: false,
        });
      } else {
        // Fallback: try to play a simple beep sound
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);

        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
      }
    } catch (error) {
      // console.log('Audio notification not supported:', error);
    }
  };

  // Debug logging
  useEffect(() => {
    // console.log('🔔 Notification state:', {
    //   isAuthenticated,
    //   unreadCount,
    //   hasNewNotifications,
    //   notificationsCount: notifications.length,
    //   isWebSocketConnected,
    //   wsUrl: isAuthenticated ? apiUtils.buildWebSocketUrl(apiEndpoints.notifications.websocket.general) : 'N/A'
    // });
  }, [isAuthenticated, unreadCount, hasNewNotifications, notifications.length, isWebSocketConnected]);

  // Clear new notification indicator after 5 seconds
  useEffect(() => {
    if (hasNewNotifications) {
      const timer = setTimeout(() => {
        setHasNewNotifications(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [hasNewNotifications]);

  // WebSocket connection management
  useEffect(() => {
    if (isAuthenticated) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isAuthenticated]);

  const markAsRead = (notificationId: string) => {
    if (!isAuthenticated) return;

    // Update local state immediately for better UX
    setNotifications(prev =>
      prev.map(notif =>
        notif.notification_id === notificationId
          ? { ...notif, status: 'completed', read_at: new Date().toISOString() }
          : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));

    // Use HTTP for user actions
    markAsReadMutation.mutate({
      variables: { success: true, message: 'Notification marked as read' },
      route: { notification_id: notificationId }
    });
  };

  const dismiss = (notificationId: string) => {
    if (!isAuthenticated) return;

    // Update local state immediately for better UX
    setNotifications(prev =>
      prev.map(notif =>
        notif.notification_id === notificationId
          ? { ...notif, status: 'cancelled', dismissed_at: new Date().toISOString() }
          : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));

    // Use HTTP for user actions
    dismissMutation.mutate({
      variables: { success: true, message: 'Notification dismissed' },
      route: { notification_id: notificationId }
    });
  };

  const deleteNotification = (notificationId: string) => {
    if (!isAuthenticated) return;

    // Update local state immediately for better UX
    setNotifications(prev => prev.filter(notif => notif.notification_id !== notificationId));
    setUnreadCount(prev => Math.max(0, prev - 1));

    // Use HTTP for user actions
    deleteMutation.mutate({
      model: {},
      route: { notification_id: notificationId }
    });
  };

  const markAllAsRead = () => {
    if (!isAuthenticated) return;

    // Update local state immediately for better UX
    setNotifications(prev =>
      prev.map(notif => ({ ...notif, status: 'completed', read_at: new Date().toISOString() }))
    );
    setUnreadCount(0);

    // Use HTTP for user actions
    markAllAsReadMutation.mutate({
      variables: { success: true, message: 'All notifications marked as read' }
    });
  };

  const refresh = async () => {
    // Load notifications from server when user opens the drawer
    if (!isAuthenticated) return;

    setIsLoading(true);
    try {
      const response = await fetch(apiUtils.buildApiUrl('/notifications'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.notifications?.filter((n: any) => !n.read_at && !n.dismissed_at).length || 0);
      } else {
        console.error('Failed to load notifications');
      }
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const openNotificationsDrawer = async () => {
    setIsDrawerOpen(true);
    await refresh(); // Load notifications when drawer opens
  };

  const closeNotificationsDrawer = () => {
    setIsDrawerOpen(false);
  };

  const showNotification = (title: string, message: string, type: 'success' | 'error' | 'info' = 'info') => {
    mantineNotifications.show({
      title,
      message,
      color: type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue',
      autoClose: type === 'error' ? 5000 : 3000,
    });
  };

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    dismiss,
    delete: deleteNotification,
    markAllAsRead,
    refresh,
    showNotification,
    hasNewNotifications,
    isWebSocketConnected,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}
