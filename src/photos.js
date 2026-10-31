import * as THREE from 'three';

const gallery = document.getElementById('photo-gallery');
const list = document.getElementById('photo-list');
const counter = document.getElementById('photo-count');
const toggle = document.getElementById('photo-toggle');
const pinLayer = document.getElementById('photo-pins');
const big = document.getElementById('photo-viewer');
const image = document.getElementById('photo-viewer-image');
const title = document.getElementById('photo-viewer-title');
const credit = document.getElementById('photo-viewer-credit');
const source = document.getElementById('photo-viewer-source');
const close = document.getElementById('photo-close');
let photos = [];
let markers = [];
let map;
let opened = false;
let active = -1;
const tmp = new THREE.Vector3();

function showPhoto(index) {
  const p = photos[index];
  if (!p) return;
  active = index;
  image.src = p.image;
  image.alt = 'Trabzon gerçek fotoğrafı: ' + p.title;
  image.onerror = () => {
    image.removeAttribute('src');
    image.alt = 'Fotoğraf yüklenemedi. Kaynak bağlantısını açarak inceleyebilirsiniz.';
  };
  title.textContent = p.title;
  credit.textContent = 'Fotoğraf: ' + p.author + ' · ' + p.license
    + (p.geotagged ? ' · Wikimedia konum etiketi' : ' · Kesin çekim koordinatı belirtilmemiş');
  source.href = p.url;
  source.textContent = 'Orijinal Wikimedia fotoğrafı ve lisansını aç';
  big.hidden = false;
  markerHighlight();
}

function markerHighlight() {
  markers.forEach(({button, index}) => button.classList.toggle('selected', index === active));
}

function makeElement(tag, cls, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text !== undefined) el.textContent = text;
  return el;
}

function renderGallery() {
  list.replaceChildren();
  markers.forEach(x => x.button.remove());
  markers = [];
  photos.forEach((p, index) => {
    const entry = makeElement('button', 'photo-entry');
    entry.type = 'button';
    const thumb = makeElement('img', 'photo-entry-image');
    thumb.src = p.image; thumb.loading = index < 3 ? 'eager' : 'lazy';
    thumb.referrerPolicy = 'no-referrer'; thumb.alt = p.title;
    const meta = makeElement('span', 'photo-entry-caption');
    meta.append(makeElement('strong', '', p.title),
       makeElement('small', '', p.author + ' · ' + p.license));
    entry.append(thumb, meta);
    entry.addEventListener('click', () => showPhoto(index));
    list.append(entry);

    if (p.geotagged && Number.isFinite(p.lat) && Number.isFinite(p.lon)) {
      const button = makeElement('button', 'photo-pin', '📷');
      button.type = 'button';
      button.title = 'Gerçek fotoğraf: ' + p.title;
      button.setAttribute('aria-label', button.title);
      button.addEventListener('click', () => showPhoto(index));
      pinLayer.append(button);
      markers.push({button, index, photo:p});
    }
  });
  counter.textContent = photos.length + ' gerçek fotoğraf · ' +
    markers.length + ' konum etiketli';
}

function setGallery(show) {
  opened = show;
  gallery.hidden = !show;
  toggle.setAttribute('aria-expanded', String(show));
  toggle.textContent = show ? 'Fotoğraf panelini kapat' : 'Gerçek fotoğraflar (' + photos.length + ')';
}

toggle.addEventListener('click', () => setGallery(!opened));
close.addEventListener('click', () => {big.hidden = true;active = -1;markerHighlight();});
big.addEventListener('click', e => {if (e.target === big) close.click();});
window.addEventListener('keydown', e=>{if (e.key === 'Escape')close.click();});

function positionMarkers() {
  map = window.isometricTrabzon || map;
  if (!map || !markers.length) return;
  const w = map.renderer.domElement.clientWidth, h=map.renderer.domElement.clientHeight;
  for (const {photo:p, button} of markers) {
    const xy = map.point(p.lon, p.lat);
    tmp.set(xy.x, map.heightAt(p.lon, p.lat) + 20, xy.y).project(map.camera);
    const visible = tmp.z >= -1 && tmp.z <= 1 &&
      tmp.x >= -1.05 && tmp.x <= 1.05 && tmp.y >= -1.05 && tmp.y <= 1.05;
    button.hidden = !visible;
    if (visible) button.style.transform =
      'translate(-50%, -50%) translate(' + Math.round((tmp.x+1)*w/2) +
      'px,' + Math.round((1-tmp.y)*h/2) + 'px)';
  }
}
function frame(){positionMarkers();requestAnimationFrame(frame);}
requestAnimationFrame(frame);

async function loadPhotos() {
  try {
    const response = await fetch('./data/photos.json', {cache:'no-store'});
    if (!response.ok) throw Error('HTTP ' + response.status);
    const data=await response.json();
    photos=(data.photos || []).filter(p=>p.image?.startsWith('https://') &&
      p.url?.startsWith('https://commons.wikimedia.org/') && p.license && p.author);
    renderGallery();
    if (photos.length > 0) {
      setGallery(window.innerWidth > 900);
    } else {
      counter.textContent = 'Fotoğraf verisi bulunamadı';
    }
  } catch (e) {
    counter.textContent = 'Fotoğraf kataloğu yüklenemedi';
    console.warn('Trabzon photos',e);
  }
}
loadPhotos();
