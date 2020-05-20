<template>
  <b-btn
    :disabled="$store.getters.getFilesUploadInProgress"
    @click="enterEditMode()"
    id="edit-button"
    v-show="canEnableEditMode && !editModeEnabled"
    variant="outline-primary"
  >
    <span v-translate>Edit</span>
  </b-btn>
</template>

<script>

import FilesMixin from '@/components/common/mixins/FilesMixin'

export default {
  mixins: [FilesMixin],
  props: {
    submission: String
  },
  data() {
    return {}
  },
  methods: {
    enterEditMode() {
      this.$store.commit('updateEditMode', true)
      this.$router.push({ name: this.$route.name, query: { submission: this.submission, edit_mode: true } })
    }
  }
}
</script>
