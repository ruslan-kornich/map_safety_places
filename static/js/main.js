var map = L.map('mapid').setView([48.3794, 31.1656], 6); // Украина

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

var markersLayer = L.layerGroup().addTo(map);
var infoContainer = document.getElementById('infoContainer');

function createMarker(latitude, longitude, comment, placeId) {
    var marker = L.marker([latitude, longitude]).addTo(markersLayer);
    marker.bindPopup('<div class="comment">' + comment + '</div>' +
        (userAuthenticated === "True" ?
            '<form id="comment-form">' +
            '<input type="text" id="comment-input" value="' + comment + '">' +
            '<button type="submit">Обновить</button>' +
            '<button id="delete-button" type="button">Удалить</button>' +
            '</form>' : ''));

    marker.on('popupopen', function() {
        if (userAuthenticated === "True") {
            var commentForm = document.getElementById('comment-form');
            var commentInput = document.getElementById('comment-input');
            var deleteButton = document.getElementById('delete-button');

            commentForm.addEventListener('submit', function(event) {
                event.preventDefault();

                var comment = commentInput.value;

                if (comment) {
                    var payload = new FormData();
                    payload.append('comment', comment);

                    fetch('/update/' + placeId + '/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCookie('csrftoken') },
                        body: payload
                    }).then(function(response) {
                        if (response.ok) {
                            marker.getPopup().setContent('<div class="comment">' + comment + '</div>' +
                                '<form id="comment-form">' +
                                '<input type="text" id="comment-input" value="' + comment + '">' +
                                '<button type="submit">Обновить</button>' +
                                '<button id="delete-button" type="button">Удалить</button>' +
                                '</form>');
                            map.closePopup();
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
                        map.closePopup();
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



function createListItem(comment) {
    // Добавляем точку в список точек
    var infoElement = document.createElement('p');
    infoElement.innerHTML = comment;
    infoContainer.appendChild(infoElement);
}

var visibleMarkers = []; // Массив видимых маркеров
var mapLoaded = false; // Флаг загрузки карты

for (let place of places) {
    console.log(place.fields);  // измените эту строку
    let marker = createMarker(place.fields.latitude, place.fields.longitude, place.fields.comment, place.pk);
    visibleMarkers.push(marker);
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

    // Если пользователь аутентифицирован, обновляем информацию о точках в боковом окне
    if (userAuthenticated) {
        // Создаем объект для хранения уникальных комментариев
        var uniqueComments = {};

        visibleMarkers.forEach(function(marker) {
            var comment = marker.getPopup().getContent();

            // Добавляем комментарий в объект только если он еще не существует
            if (!uniqueComments[comment]) {
                uniqueComments[comment] = true;
                createListItem(comment);
            }
        });
    } else {
        // Добавляем точки в список точек только для неаутентифицированных пользователей
        visibleMarkers.forEach(function(marker) {
            var comment = marker.getPopup().getContent();
            createListItem(comment);
        });
    }
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
                            var marker = createMarker(data.latitude, data.longitude, data.comment);
                            visibleMarkers.push(marker); // Добавляем маркер в массив видимых маркеров
                            createListItem(data.comment);
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
