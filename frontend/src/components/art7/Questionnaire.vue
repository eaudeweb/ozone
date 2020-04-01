<template>
  <div v-if="info">
    <form class="form-sections table-wrapper">
        <div class="form-fields" v-for="field in info.form_fields" :key="field.name">
          <div class="field-wrapper">
            <label>{{field.label}}</label>
            <fieldGenerator
              :fieldInfo="{index:field.name, tabName: info.name, field:field.name}"
              :disabled="!canChangeQuestionnaire"
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
          :disabled="isRemarkReadOnly(comment_key)"
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
import PermissionsMixin from '@/components/common/mixins/PermissionsMixin'

export default {
  mixins: [PermissionsMixin],
  name: 'Tab1',
  props: {
    info: Object
  },
  data() {
    return {
      labels: getCommonLabels(this.$gettext)
    }
  },
  computed: {
    onlySelectedValue() {
      return Object.keys(this.info.form_fields).map(field => this.info.form_fields[field].selected)
    }
  },
  components: { fieldGenerator },
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
