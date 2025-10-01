// static/js/save_preferences.js
export function savePreferences(preferences) {
    fetch('/api/save-preferences/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(preferences)
    })
    .then(response => response.json())
    .then(data => console.log('Preferences saved:', data))
    .catch(error => console.error('Error saving preferences:', error));
}
