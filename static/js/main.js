var map = L.map('mapid', { zoomControl: false }).setView([48.3794, 31.1656], 8); // Украина

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

map.invalidateSize();

L.control.zoom({
  position: 'bottomright'
}).addTo(map);

var markersLayer = L.layerGroup().addTo(map);
var infoContainer = document.getElementById('infoContainer');

var visibleMarkers = [];
var mapLoaded = false;

function createMarker(latitude, longitude, comment, placeId, user, created_at) {
  var marker = L.marker([latitude, longitude]).addTo(markersLayer);
  marker.comment = comment;
  marker.placeId = placeId;
  marker.user = user;
  marker.created_at = created_at;

  marker.on('click', function () {
    var popup = L.popup({ closeButton: false })
      .setLatLng(marker.getLatLng())
      .setContent('<div>' + comment + '</div>');

    if (userAuthenticated === "True") {
      popup = L.popup({ closeButton: false })
        .setLatLng(marker.getLatLng())
        .setContent('<form id="comment-form">' +
          '<input type="text" id="comment-input" value="' + comment + '">' +
          '<button type="submit">Обновить</button>' +
          '<button id="delete-button" type="button">Удалить</button>' +
          '</form>')
        .openOn(map);

      var commentForm = popup.getElement().querySelector('#comment-form');
      var commentInput = popup.getElement().querySelector('#comment-input');
      var deleteButton = popup.getElement().querySelector('#delete-button');

      commentForm.addEventListener('submit', function (event) {
        event.preventDefault();

        var updatedComment = commentInput.value;

        if (updatedComment) {
          var payload = new FormData();
          payload.append('comment', updatedComment);

          fetch('/update/' + placeId + '/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: payload
          }).then(function (response) {
            if (response.ok) {
              marker.comment = updatedComment;
              map.closePopup(popup);
              updateVisibleMarkers();
            } else {
              console.error('Ошибка обновления комментария');
            }
          }).catch(function (error) {
            console.error(error);
          });
        }
      });

      deleteButton.addEventListener('click', function () {
        fetch('/delete/' + placeId + '/', {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
        }).then(function (response) {
          if (response.ok) {
            markersLayer.removeLayer(marker);
            map.closePopup(popup);
            updateVisibleMarkers();
          } else {
            console.error('Ошибка удаления комментария');
          }
        }).catch(function (error) {
          console.error(error);
        });
      });
    } else {
      popup.openOn(map);
    }
  });

  return marker;
}

function createListItem(username, comment, timestamp) {
  var infoElement = document.createElement('div');
  infoElement.classList.add('comment-container');
  infoElement.setAttribute('data-comment', comment);

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

// Загружаем полигоны с помощью fetch
fetch('https://deepstatemap.live/api/history/1677196268/geojson')
  .then(function (response) {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error('Ошибка загрузки полигонов');
    }
  })
  .then(function (data) {
    // Фильтрация данных для отображения только полигонов
    const polygons = data.features.filter(feature => feature.geometry.type !== 'Point');

    // Создание нового GeoJSON объекта только с полигонами
    const geoJsonData = {
      type: 'FeatureCollection',
      features: polygons
    };

    L.geoJSON(geoJsonData, {
      style: function (feature) {
        return {
          color: feature.properties.stroke,
          fillColor: feature.properties.fill,
          weight: feature.properties['stroke-width'],
          fillOpacity: feature.properties['fill-opacity']
        };
      }
    }).addTo(map);
  })
  .catch(function (error) {
    console.error(error);
  });



console.log(places);
for (let place of places) {
  let marker = createMarker(place.fields.latitude, place.fields.longitude, place.fields.comment, place.pk, place.fields.user, place.fields.created_at);
  visibleMarkers.push(marker);
  createListItem(place.fields.user, place.fields.comment, place.fields.created_at);
}

map.on('load', function () {
  mapLoaded = true;
});

map.on('moveend', updateVisibleMarkers);
map.on('zoomend', function () {
  if (mapLoaded) {
    updateVisibleMarkers();
  }
});

function updateVisibleMarkers() {
  infoContainer.innerHTML = '';

  var bounds = map.getBounds();
  visibleMarkers = [];

  markersLayer.eachLayer(function (marker) {
    var latlng = marker.getLatLng();
    if (bounds.contains(latlng)) {
      visibleMarkers.push(marker);
    }
  });

  var uniqueComments = {};
  visibleMarkers.forEach(function (marker) {
    var comment = marker.comment;
    var user = marker.user;
    var created_at = marker.created_at;
    if (!uniqueComments[comment]) {
      uniqueComments[comment] = true;
      createListItem(user, comment, created_at);
    }
  });
}

map.on('click', function (e) {
  if (userAuthenticated === "True") {
    var popup = L.popup({ closeButton: false })
      .setLatLng(e.latlng)
      .setContent('<form id="comment-form">' +
        '<input type="text" id="comment-input" placeholder="Введите комментарий">' +
        '<button type="submit">Сохранить</button>' +
        '</form>')
      .openOn(map);

    var commentForm = popup.getElement().querySelector('#comment-form');
    var commentInput = popup.getElement().querySelector('#comment-input');

    commentForm.addEventListener('submit', function (event) {
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
        }).then(function (response) {
          if (response.ok) {
            response.json().then(function (data) {
              var marker = createMarker(data.latitude, data.longitude, data.comment, data.placeId, data.user, data.created_at);
              visibleMarkers.push(marker);
              createListItem(data.user, data.comment, data.created_at);
              map.closePopup(popup);
              updateVisibleMarkers();
            });
          } else {
            console.error('Ошибка сохранения комментария');
          }
        }).catch(function (error) {
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
