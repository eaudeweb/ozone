import { post, fetch, api, getCookie, remove } from './api.js';


export function removeLoginToken() {
  return new Promise((resolve, reject) => {
    remove(`/auth-token/${getCookie('authToken')}`)
      .then((response) => {
        delete api.defaults.headers.authorization;
        resolve();
      })
      .catch((error) => {
        reject(error);
      });
  })
}

export function getLoginToken(username, password) {
  return new Promise((resolve, reject) => {
    post('/auth-token/', { 'username': 'admin', 'password': 'admin1234' })
      .then((response) => {
        api.defaults.headers.authorization = 'token ' + response.data.token;
        resolve(response);
      })
      .catch((error) => {
        reject(error);
      });
  });
}

// export function fetchUserProfile() {
//   return fetch(`workspace-profile/`);
// }
