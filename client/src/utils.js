import { ref } from 'vue';

export function showNotification(notification, msg, type = "success", duration = 2000) {
  if (notification._timeoutId) {
    clearTimeout(notification._timeoutId);
    notification._timeoutId = null;
  }
  
  notification.message = msg;
  notification.type = type;
  notification.visible = true;

  notification._timeoutId = setTimeout(() => {
    notification.visible = false;
    notification._timeoutId = null;
  }, duration);
}
