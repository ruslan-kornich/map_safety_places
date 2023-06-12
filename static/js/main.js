var map = L.map('mapid').setView([48.3794, 31.1656], 8); // Украина

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

var markersLayer = L.layerGroup().addTo(map);
var infoContainer = document.getElementById('infoContainer');

// ...

function createMarker(latitude, longitude, comment, placeId, user, created_at) {
    var marker = L.marker([latitude, longitude]).addTo(markersLayer);
    marker.comment = comment;
    marker.user = user;
    marker.created_at = created_at;

    marker.on('click', function () {
        if (userAuthenticated === "True") {
            var popup = L.popup({ closeButton: false })
                .setLatLng(marker.getLatLng())
                .setContent('<form id="comment-form">' +
                    '<input type="text" id="comment-input" value="' + comment + '">' +
                    '<button type="submit">Обновить</button>' +
                    '<button id="delete-button" type="button">Удалить</button>' +
                    '</form>')
                .openOn(map);

            var commentForm = document.getElementById('comment-form');
            var commentInput = document.getElementById('comment-input');
            var deleteButton = document.getElementById('delete-button');

            commentForm.addEventListener('submit', function(event) {
                event.preventDefault();

                var updatedComment = commentInput.value;

                if (updatedComment) {
                    var payload = new FormData();
                    payload.append('comment', updatedComment);

                    fetch('/update/' + placeId + '/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCookie('csrftoken') },
                        body: payload
                    }).then(function(response) {
                        if (response.ok) {
                            marker.comment = updatedComment;
                            map.closePopup(popup);
                        } else {
                            console.error('Ошибка обновления комментария');
                        }
                    }).catch(function(error) {
                        console.error(error);
                    });
                }
            });

            deleteButton.addEventListener('click', function() {
    fetch('/delete/' + placeId + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
    }).then(function(response) {
        if (response.ok) {
            markersLayer.removeLayer(marker);
            map.closePopup(popup);
        } else {
            console.error('Ошибка удаления комментария');
        }
    }).catch(function(error) {
        console.error(error);
    });
});
        }
    });

    return marker; // Возвращаем созданный маркер
}

// ...


function createListItem(username, comment, timestamp) {
  var infoElement = document.createElement('div');
  infoElement.classList.add('comment-container');

  var avatarElement = document.createElement('div');
  avatarElement.classList.add('comment-avatar');
  infoElement.appendChild(avatarElement);

  var contentElement = document.createElement('div');
  contentElement.classList.add('comment-content');
  infoElement.appendChild(contentElement);

  var usernameElement = document.createElement('div');
  usernameElement.textContent = username;
  usernameElement.classList.add('comment-username');
  contentElement.appendChild(usernameElement);

  var commentElement = document.createElement('div');
  commentElement.textContent = comment;
  commentElement.classList.add('comment-text');
  contentElement.appendChild(commentElement);

  var timestampElement = document.createElement('div');
  var timestampDate = new Date(timestamp);
  var timeString = timestampDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  var dateString = timestampDate.toLocaleDateString();
  timestampElement.textContent = timeString + '   ' + dateString;
  timestampElement.classList.add('comment-timestamp');
  contentElement.appendChild(timestampElement);

  infoContainer.appendChild(infoElement);
}





var visibleMarkers = [];
var mapLoaded = false;

console.log(places); // Вывод содержимого объекта places в консоль
for (let place of places) {
    let marker = createMarker(place.fields.latitude, place.fields.longitude, place.fields.comment, place.pk, place.fields.user, place.fields.created_at);
    visibleMarkers.push(marker);

    createListItem(place.fields.user, place.fields.comment, place.fields.created_at);
}

map.on('load', function() {
    mapLoaded = true; // Устанавливаем флаг загрузки карты
});

map.on('moveend', updateVisibleMarkers);
map.on('zoomend', function() {
    if (mapLoaded) {
        updateVisibleMarkers();
    }
});

function updateVisibleMarkers() {
    // Очищаем список точек перед обновлением
    infoContainer.innerHTML = '';

    // Получаем границы видимой области карты
    var bounds = map.getBounds();
    visibleMarkers = [];

    // Фильтруем точки, оставляя только те, которые находятся в пределах видимой области
    markersLayer.eachLayer(function(marker) {
        var latlng = marker.getLatLng();
        if (bounds.contains(latlng)) {
            visibleMarkers.push(marker);
        }
    });

    // Используем данные из объекта маркера для отображения в боковом меню
    var uniqueComments = {};
    visibleMarkers.forEach(function(marker) {
        var comment = marker.comment;
        var user = marker.user;
        var created_at = marker.created_at;
        if (!uniqueComments[comment]) {
            uniqueComments[comment] = true;
            createListItem(user, comment, created_at);
        }
    });
}

map.on('click', function(e) {
    if (userAuthenticated === "True") {
        var popup = L.popup({ closeButton: false })
            .setLatLng(e.latlng)
            .setContent('<form id="comment-form">' +
                '<input type="text" id="comment-input" placeholder="Введите комментарий">' +
                '<button type="submit">Сохранить</button>' +
                '</form>')
            .openOn(map);

        var commentForm = document.getElementById('comment-form');
        var commentInput = document.getElementById('comment-input');

        commentForm.addEventListener('submit', function(event) {
            event.preventDefault();

            var latitude = e.latlng.lat.toFixed(6);
            var longitude = e.latlng.lng.toFixed(6);
            var comment = commentInput.value;

            if (comment) {
                var payload = new FormData();
                payload.append('latitude', latitude);
                payload.append('longitude', longitude);
                payload.append('comment', comment);

                fetch('/create/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: payload
                }).then(function(response) {
                    if (response.ok) {
                        response.json().then(function(data) {
                            var marker = createMarker(data.latitude, data.longitude, data.comment, data.user, data.created_at);
                            visibleMarkers.push(marker); // Добавляем маркер в массив видимых маркеров
                            createListItem(data.user, data.comment, data.created_at);
                            map.closePopup(popup);

                            // Обновляем список точек
                            updateVisibleMarkers();
                        });
                    } else {
                        console.error('Ошибка сохранения комментария');
                    }
                }).catch(function(error) {
                    console.error(error);
                });
            }
        });
    }
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}