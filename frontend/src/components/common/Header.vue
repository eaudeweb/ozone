<template>
  <b-row>
    <HeaderDropdown v-if="$store.state.currentUser" class="mr-3" right>
      <template slot="header">
        {{currentUserName}}
        <span class="cog"></span>
        &nbsp;
        &nbsp;
        &nbsp;
        <span
          v-if="currentCountryIso"
          :class="`header-flag flag-icon flag-icon-${currentCountryIso}`"
        ></span>
        <span
          v-if="currentCountryIso"
          style="vertical-align: -1px"
        >
          {{this.$language.available[this.$language.current]}}
        </span>
      </template>
      <template slot="dropdown">
        <b-dropdown-header tag="div" class="text-center">
          <strong>
            <span v-translate>Account</span>
          </strong>
        </b-dropdown-header>
        <b-dropdown-item v-if="isAdmin" :href="`${apiBase}/admin/`">
          <i class="fa fa-user-plus"></i>
          <span v-translate>Admin</span>
        </b-dropdown-item>
        <b-dropdown-item @click="goToUserProfile">
          <i class="fa fa-user"/>
          <span v-translate>User profile</span>
        </b-dropdown-item>
        <b-dropdown-item :href="`${apiBase}/admin/password_change/`">
          <i class="fa fa-unlock"/>
          <span v-translate>Reset password</span>
        </b-dropdown-item>
        <b-dropdown-item :href="`${apiBase}/docs/`">
          <i class="fa fa-question"/>
          <span v-translate>Help</span>
        </b-dropdown-item>
        <b-dropdown-item @click="logout" id="logout_button">
          <i class="fa fa-lock"/>
          <span v-if="$store.state.currentUser.impersonated_by" v-translate>Release</span>
          <span v-else v-translate>Logout</span>
        </b-dropdown-item>
        <!-- <b-dropdown-divider /> -->
      </template>
    </HeaderDropdown>
  </b-row>
</template>

<script>
import authMixin from '@/components/common/mixins/auth'
import { HeaderDropdown } from '@coreui/vue'
import { apiBase } from '@/components/common/services/api'

export default {
  mixins: [authMixin],
  components: {
    HeaderDropdown
  },
  data() {
    return {
      apiBase
    }
  },
  computed: {
    currentUserName() {
      if (!this.$store.state.currentUser.impersonated_by) {
        return this.$store.state.currentUser.username
      }
      return `${this.$store.state.currentUser.impersonated_by} (as ${this.$store.state.currentUser.username})`
    },
    isAdmin() {
      return this.$store.state.currentUser.is_secretariat
    },
    currentCountryIso() {
      return this.$store.getters.currentCountryIso
    }
  },
  methods: {
    goToUserProfile() {
      this.$router.push({ name: 'UserProfile' })
    }
  }
}
</script>
