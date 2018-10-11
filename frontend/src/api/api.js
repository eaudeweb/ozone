/* eslint-disable */
import axios from 'axios';

const logRequests = process.env.NODE_ENV === 'development';

const BACKEND_HOST = 'localhost';
const BACKEND_PORT = 8000;

const apiURL = `http://${BACKEND_HOST}:${BACKEND_PORT}/api/`;

const api = axios.create({
  baseURL: apiURL,
  withCredentials: true,
});

api.defaults.xsrfHeaderName = "X-CSRFTOKEN";
api.defaults.xsrfCookieName = "csrftoken";

function checkAuth() {
  if (!api.defaults.headers['authorization'] && getCookie('authToken')) {
    api.defaults.headers.authorization = 'token ' + getCookie('authToken');
  }
}

function fetch(path) {
  logRequests && console.log(`fetching ${path}...`);
  checkAuth();
  return api.get(path);
}

function post(path, data) {
  logRequests && console.log(`posting ${path} with data ${data}...`);
  checkAuth();
  return api.post(path, data);
}

function update(path, data) {
  logRequests && console.log(`patching ${path} with data ${data}...`);
  checkAuth();
  return api.patch(path, data);
}

function remove(path) {
  logRequests && console.log(`removig ${path} ...`);
  checkAuth();
  return api.delete(path);
}

function getCookie(name) {
  let cookie = {};
  document.cookie.split(';').forEach(function (el) {
    let [k, v] = el.split('=');
    cookie[k.trim()] = v;
  })
  return cookie[name];
}

export { apiURL, filesURL, api, fetch, post, update, remove, getCookie };