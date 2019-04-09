import 'core-js/es6'
import VueCookies from 'vue-cookies'
import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
import 'vue-multiselect/dist/vue-multiselect.min.css'

import store from '@/store/index'
import * as Sentry from '@sentry/browser'
import App from './App'
import router from './router'
import { initLanguages } from '@/components/common/services/languageService'

if (process.env.NODE_ENV !== 'development') {
  Sentry.init({
    dsn: `https://${process.env.VUE_APP_SENTRY_DSN}@sentry.io/1374535`,
    environment: process.env.VUE_APP_SENTRY_ENV,
    release: process.env.VUE_APP_SENTRY_RELEASE,
    integrations: [new Sentry.Integrations.Vue({ Vue })]
  })
}

Vue.use(VueCookies)

Vue.config.productionTip = false

Vue.use(BootstrapVue)

initLanguages(Vue)

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
