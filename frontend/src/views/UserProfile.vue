<template>
  <div class="row justify-content-center">
    <b-card class="col-md-6" v-if="userProfile">
      <b-input-group class="mb-2" :prepend="$gettext('First name')">
        <input :readonly="readonly" class="form-control" v-model="userProfile.first_name">
      </b-input-group>
      <b-input-group class="mb-2" :prepend="$gettext('Last name')">
        <input :readonly="readonly" class="form-control" v-model="userProfile.last_name">
      </b-input-group>
      <b-input-group class="mb-2" :prepend="$gettext('Email')">
        <input :readonly="readonly" class="form-control" v-model="userProfile.email">
      </b-input-group>
      <b-input-group class="mb-2" :prepend="$gettext('Language')">
        <multiselect
          trackBy="value"
          label="text"
          :disabled="readonly"
          :hide-selected="false"
          v-model="userProfile.language"
          :options="availableLanguages"
        />
      </b-input-group>
      <b-input-group class="mb-2">
        <span v-translate>User name:</span>&nbsp;
        <b>
          <span>{{userProfile.username}}</span>
        </b>
      </b-input-group>
      <b-input-group class="mb-2" v-if="!userProfile.is_secretariat">
        <span v-translate>Party:</span>&nbsp;
        <b>
          <span>{{userProfile.party_name}}</span>
        </b>
      </b-input-group>
      <b-input-group class="mb-2">
        <span v-translate>Role:</span>&nbsp;
        <b>
          <span v-translate v-if="userProfile.is_secretariat">Secretariat</span>
          <span v-translate v-else>Party</span>
          &nbsp;
          <span v-translate v-if="userProfile.is_read_only">read-only</span>
        </b>
      </b-input-group>
      <b-input-group class="mb-2">
        <b-button v-if="readonly" class="mr-2" variant="primary" @click="edit()">
          <span>{{ $gettext('Edit') }}</span>
        </b-button>
        <b-button v-if="!readonly" class="mr-2" variant="primary" @click="save()">
          <span>{{ $gettext('Save') }}</span>
        </b-button>
        <b-button v-if="!readonly" class="mr-2" variant="danger" @click="cancel()">
          <span>{{ $gettext('Cancel') }}</span>
        </b-button>
      </b-input-group>
    </b-card>
  </div>
</template>

<script>
import Multiselect from '@/components/common/ModifiedMultiselect'

export default {
  components: {
    Multiselect
  },
  data() {
    return {
      userProfile: null,
      readonly: true
    }
  },
  async created() {
    this.$store.commit('updateBreadcrumbs', this.$gettext('User profile'))
    if (!this.$store.state.currentUser) {
      await this.$store.dispatch('getMyCurrentUser')
    }
    this.userProfile = {
      ...this.$store.state.currentUser
    }
    if (!this.userProfile.language) {
      this.userProfile.language = this.$language.current
    }
  },

  computed: {
    availableLanguages() {
      return Object.keys(this.$language.available)
        .map(key => ({ text: this.$language.available[key], value: key }))
    }
  },
  methods: {
    edit() {
      this.readonly = false
    },
    save() {
      this.$store.dispatch('updateCurrentUser', { user: this.userProfile, $gettext: this.$gettext })
      this.readonly = true
    },
    cancel() {
      this.userProfile = {
        ...this.$store.state.currentUser
      }
      this.readonly = true
    }
  }
}
</script>
