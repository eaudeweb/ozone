<template>
  <b-btn
    :disabled="$store.getters.getFilesUploadInProgress"
    @click="enterEditMode()"
    id="edit-button"
    v-show="canEnableEditMode && !$store.getters.edit_mode"
    variant="outline-primary"
  >
    <span v-translate>Edit</span>
  </b-btn>
</template>

<script>

import FilesMixin from '@/components/common/mixins/FilesMixin'
import PermissionsMixin from '@/components/common/mixins/PermissionsMixin'

export default {
  mixins: [FilesMixin, PermissionsMixin],
  props: {
    submission: String,
    obligation_type: {
      type: String,
      default: null
    }
  },
  data() {
    return {}
  },
  methods: {
    enterEditMode() {
      this.$store.commit('updateEditMode', true)
      this.$router.push({ name: this.$route.name, query: { submission: this.submission, edit_mode: true }, params: { obligation_type: this.obligation_type } })
    }
  }
}
</script>
