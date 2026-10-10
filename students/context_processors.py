from django.db.models import Q
from .models import Notification

def notifications_context(request):
    """
    Global Context Processor that provides the student's real-time notifications
    and unread count to every template inheriting from base.html.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'notifications_list': [],
            'unread_notifications_count': 0,
            'has_unread_tasks': False,
        }

    user = request.user
    
    # Notifications available to this user: Global OR specifically directed to them
    user_notifications = list(
        Notification.objects.filter(
            Q(is_global=True) | Q(recipient=user)
        ).select_related('recipient').order_by('-created_at')[:20]
    )

    # Get set of IDs read by this user
    read_ids = set(user.read_notifications.values_list('id', flat=True))

    unread_count = 0
    has_tasks = False
    task_types = {'exam', 'assignment', 'live_class', 'course', 'lesson', 'document'}

    for notif in user_notifications:
        is_read = (notif.id in read_ids)
        notif.is_read_by_user = is_read
        if not is_read:
            unread_count += 1
            if notif.notification_type in task_types:
                has_tasks = True

    pending_support_count = 0
    if user.is_staff or user.is_superuser:
        try:
            from .models import SupportTicket
            pending_support_count = SupportTicket.objects.filter(status='pending').count()
        except Exception:
            pass

    return {
        'notifications_list': user_notifications,
        'unread_notifications_count': unread_count,
        'has_unread_tasks': has_tasks,
        'pending_support_count': pending_support_count,
    }
