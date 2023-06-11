// ...

function createListItem(username, comment, timestamp) {
    var infoElement = document.createElement('div');
    infoElement.classList.add('comment-container'); // Добавляем класс "comment-container"

    var usernameElement = document.createElement('p');
    usernameElement.textContent = 'Пользователь: ' + username;
    usernameElement.classList.add('username');
    infoElement.appendChild(usernameElement);

    var commentElement = document.createElement('p');
    commentElement.textContent = 'Комментарий: ' + comment;
    infoElement.appendChild(commentElement);

    var timestampElement = document.createElement('p');
    timestampElement.textContent = 'Дата создания: ' + timestamp;
    timestampElement.classList.add('timestamp');
    infoElement.appendChild(timestampElement);

    infoContainer.appendChild(infoElement);
}

// ...

window.addEventListener('DOMContentLoaded', function() {
    places.forEach(function(place) {
        var username = place.user;
        var comment = place.comment;
        var timestamp = place.created_at;

        createListItem(username, comment, timestamp);
    });
});

// ...
