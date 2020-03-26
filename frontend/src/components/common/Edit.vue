<template>
  <b-btn
    :disabled="$store.getters.getFilesUploadInProgress"
    @click="$store.commit('updateEditMode', true)"
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

  data() {
    return {}
  },

}
</script>
