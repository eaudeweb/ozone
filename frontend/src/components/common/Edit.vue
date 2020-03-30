<template>
  <b-btn
    :disabled="$store.getters.getFilesUploadInProgress"
    @click="enterEditMode()"
    id="edit-button"
    v-show="$store.getters.can_edit_data && !$store.getters.edit_mode"
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
      this.$router.push({ name: this.$route.name, query: { submission: this.submission, edit_mode: true }, params: { obligation_type: this.obligation_type } })
      this.$store.commit('updateEditMode', true)
    }
  }
}
</script>
