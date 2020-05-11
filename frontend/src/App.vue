<template>
  <div class="app">
    <div class="api-action-display" v-if="isLoading">
      <div class="lds-ellipsis">
        <div></div>
        <div></div>
        <div></div>
        <div></div>
      </div>
    </div>
    <AppHeader fixed>
      <SidebarToggler class="d-lg-none" display="md" mobile/>
      <!-- <b-link class="navbar-brand" to="#"> -->
      <!-- <img class="navbar-brand-full" width="89" height="25" alt="Logo"> -->
      <!-- <img class="navbar-brand-minimized" width="30" height="30" alt="MobileLogo"> -->
      <!-- </b-link> -->
      <SidebarToggler class="d-md-down-none" display="lg"/>
      <h3>
        <span>{{list}}</span>
      </h3>

      <b-navbar-nav class="ml-auto">
        <Header/>
      </b-navbar-nav>
      <!--<AsideToggler class="d-lg-none" mobile />-->
    </AppHeader>
    <div class="app-body">
      <AppSidebar fixed>
        <router-link :to="{ name: 'Dashboard'}">
            <img class="logo" src="/img/logo.png" />
        </router-link>

        <SidebarHeader/>
        <SidebarForm/>
        <SidebarNav :navItems="nav"></SidebarNav>
        <SidebarFooter/>
        <SidebarMinimizer/>
      </AppSidebar>

      <main class="main">
        <div class="container-fluid">
          <router-view></router-view>
        </div>

        <!-- Confirm Modal -->
        <b-modal
          id="confirm-modal"
          centered
          no-close-on-backdrop
          hide-header-close
          hide-header
          :visible="$store.state.confirmModal.isVisible"
          @ok="$store.state.confirmModal.okCallback"
          @cancel="$store.state.confirmModal.cancelCallback"
          @hide="$store.state.confirmModal.hideCallBack"
        >
          <p class="my-2">
            <b>{{$store.state.confirmModal.title}}</b>
          </p>
          <p
            class="my-4"
            v-if="$store.state.confirmModal.description"
          >{{$store.state.confirmModal.description}}</p>
        </b-modal>
      </main>
    </div>
    <InactivityDetector v-if="env !== 'development'"></InactivityDetector>
  </div>
</template>

<script>

import * as Sentry from '@sentry/browser'
import {
  Header as AppHeader, SidebarToggler, Sidebar as AppSidebar, SidebarFooter, SidebarForm, SidebarHeader, SidebarMinimizer, SidebarNav
} from '@coreui/vue'
import { getNav } from '@/_nav'
import Header from '@/components/common/Header'
import { api } from '@/components/common/services/api'
import auth from '@/components/common/mixins/auth'
import { setLanguage } from '@/components/common/services/languageService'
import InactivityDetector from '@/InactivityDetector'
import loadPollyfills from '@/helpers/polyfills'

export default {
  name: 'app',
  components: {
    AppHeader,
    AppSidebar,
    Header,
    SidebarForm,
    SidebarFooter,
    SidebarToggler,
    SidebarHeader,
    SidebarNav,
    SidebarMinimizer,
    InactivityDetector
  },

  mixins: [auth],

  data() {
    return {
      refCount: 0,
      isLoading: false,
      nav: getNav(this.$gettext),
      env: process.env.NODE_ENV
    }
  },

  computed: {
    name() {
      return this.$route.name
    },
    list() {
      return this.$store.getters.pageTitle
    }
  },
  methods: {
    setLoading(isLoading) {
      if (isLoading) {
        this.refCount += 1
        this.isLoading = true
      } else if (this.refCount > 0) {
        this.refCount -= 1
        this.isLoading = (this.refCount > 0)
      }
    }
  },
  watch: {
    '$language.current': {
      handler() {
        this.nav = getNav(this.$gettext)
      }
    },
    '$store.state.currentUser': {
      handler(newValue) {
        if (newValue) {
          setLanguage(newValue.language, this)
        }
      }
    }
  },
  created() {
    this.$store.dispatch('getMyCurrentUser')
      .then(() => {
        if (process.env.NODE_ENV !== 'development') {
          Sentry.configureScope((scope) => {
            const username = this.$store.state.currentUser ? this.$store.state.currentUser.username : undefined
            scope.setUser({ 'username': username })
          })
        }
      })
    loadPollyfills()
    api.interceptors.request.use((config) => {
      if (!config.hideLoader) {
        this.setLoading(true)
      }
      return config
    }, (error) => {
      this.setLoading(false)
      this.$store.dispatch('setAlert', {
        $gettext: this.$gettext,
        message: { ...error.response.data },
        variant: 'danger'
      })
      return Promise.reject(error)
    })

    api.interceptors.response.use((response) => {
      this.setLoading(false)
      return response
    }, (error) => {
      this.setLoading(false)
      this.$store.dispatch('setAlert', {
        $gettext: this.$gettext,
        message: { ...error.response.data },
        variant: 'danger'
      })
      if (error.response.status === 401) {
        this.logout('cookie')
      }

      return Promise.reject(error)
    })
  }
}
</script>

<style lang="scss">
// CoreUI Icons Set
@import "~@coreui/icons/css/coreui-icons.min.css";
/* Import Font Awesome Icons Set */
$fa-font-path: "~font-awesome/fonts/";
@import "~font-awesome/scss/font-awesome.scss";
/* Import Simple Line Icons Set */
$simple-line-font-path: "~simple-line-icons/fonts/";
@import "~simple-line-icons/scss/simple-line-icons.scss";
/* Import Flag Icons Set */
@import "~flag-icon-css/css/flag-icon.min.css";
/* Import Bootstrap Vue Styles */
@import "~bootstrap-vue/dist/bootstrap-vue.css";
// Import Main styles for this application
@import "assets/scss/style";

.lds-ellipsis {
  display: inline-block;
  position: relative;
  width: 64px;
  height: 64px;
}
.lds-ellipsis div {
  position: absolute;
  top: 27px;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: red;
  animation-timing-function: cubic-bezier(0, 1, 1, 0);
}
.lds-ellipsis div:nth-child(1) {
  left: 6px;
  background: yellow;
  animation: lds-ellipsis1 0.6s infinite;
}
.lds-ellipsis div:nth-child(2) {
  left: 6px;
  background: blue;
  animation: lds-ellipsis2 0.6s infinite;
}
.lds-ellipsis div:nth-child(3) {
  left: 26px;
  background: green;
  animation: lds-ellipsis2 0.6s infinite;
}
.lds-ellipsis div:nth-child(4) {
  left: 45px;
  animation: lds-ellipsis3 0.6s infinite;
}
@keyframes lds-ellipsis1 {
  0% {
    transform: scale(0);
  }
  100% {
    transform: scale(1);
  }
}
@keyframes lds-ellipsis3 {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(0);
  }
}
@keyframes lds-ellipsis2 {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(19px, 0);
  }
}

.api-action-display {
  position: fixed;
  // top: 50%;
  // left: 50%;
  // transform: translate(-50%, -50%);
  // z-index: 1000;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 99999;
    background: rgba(0,0,0,0.1);
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
