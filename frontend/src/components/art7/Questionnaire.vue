<template>
  <div v-if="info">
    <form class="form-sections table-wrapper">
        <div class="form-fields" v-for="field in info.form_fields" :key="field.name">
          <div class="field-wrapper">
            <label>{{field.label}}</label>
            <fieldGenerator
              :fieldInfo="{index:field.name, tabName: info.name, field:field.name}"
              :disabled="!$store.getters.edit_mode"
              :field="field"
            />
          </div>
        </div>
    </form>
    <div id="tab-comments" class="table-wrapper">
      <div
        v-for="(comment, comment_key) in info.comments"
        :key="comment_key"
        class="comments-input"
      >
        <label>
          <span>{{labels[comment_key]}}</span>
        </label>
        <!-- addComment(state, { data, tab, field }) { -->
        <textarea
          @change="$store.commit('addComment', {data: $event.target.value, tab:info.name, field: comment_key})"
          :disabled="getCommentFieldPermission(comment_key) || !$store.getters.edit_mode"
          class="form-control"
          :value="comment.selected"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<script>

import fieldGenerator from '@/components/common/form-components/fieldGenerator'
import { getCommonLabels } from '@/components/common/dataDefinitions/labels'

export default {
  name: 'Tab1',

  props: {
    info: Object
  },

  computed: {
    onlySelectedValue() {
      return Object.keys(this.info.form_fields).map(field => this.info.form_fields[field].selected)
    }
  },

  components: { fieldGenerator },

  methods: {
    getCommentFieldPermission(fieldName) {
      let type = fieldName.split('_')
      type = type[type.length - 1]
      if (type === 'party') {
        return !this.$store.getters.can_change_remarks_party
      }
      if (['secretariat', 'os'].includes(type)) {
        return !this.$store.getters.can_change_remarks_secretariat
      }
    }
  },

  data() {
    return {
      labels: getCommonLabels(this.$gettext)
    }
  },

  watch: {
    'onlySelectedValue': {
      handler(old_val, new_val) {
        if (this.info.status !== 'edited' && JSON.stringify(old_val) !== JSON.stringify(new_val)) {
          this.$store.commit('setTabStatus', {
            tab: 'questionaire_questions',
            value: 'edited'
          })
        }
      }
    }
  }
}
</script>
