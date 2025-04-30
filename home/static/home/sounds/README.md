# Notification Sounds

This directory should contain sound files for notifications.

## Required Files

1. `notification.mp3` - A short sound (0.5-1 second) for new notifications

## Recommended Sound Characteristics

- Short duration (0.5-1 second)
- Not too jarring or loud
- Distinctive enough to be recognized
- Appropriate for a professional environment

## How to Add Sound Files

You can download free notification sounds from various sources:

1. [Notification Sounds](https://notificationsounds.com/) - Free notification sounds
2. [Freesound](https://freesound.org/) - Creative Commons licensed sounds
3. [Mixkit](https://mixkit.co/free-sound-effects/notification/) - Free notification sound effects

After downloading, rename the file to `notification.mp3` and place it in this directory.

## Usage in Code

The notification sound is automatically played when a new notification is received, if the user has enabled notification sounds in their preferences.

```javascript
// Example of how the sound is played
function playNotificationSound() {
    const audioElement = document.getElementById('notification-sound');
    if (audioElement) {
        audioElement.currentTime = 0;
        audioElement.play();
    }
}
```

## User Preferences

Users can enable or disable notification sounds in their preferences. The setting is stored in localStorage:

```javascript
// Check if notification sounds are enabled
const soundsEnabled = localStorage.getItem('notification_sounds_enabled') !== 'false';
```

By default, notification sounds are enabled.
