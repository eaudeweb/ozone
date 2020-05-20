<template>
  <div>
    <!-- <div v-if="flag_approved_field === undefined"> -->
      <div
        class="mb-2"
        v-if="$store.state.current_submission.current_state === 'finalized' || $store.state.current_submission.flag_superseded"
      >
        <span
          class="color-green mr-3"
          v-if="$store.state.current_submission.current_state === 'finalized' && $store.state.form.tabs.flags && $store.state.current_submission.flag_valid && $store.state.form.tabs.flags.showValid"
        >
          <i class="fa fa-check-circle fa-sm mr-2"></i>
          <span v-translate>Valid</span>
        </span>
        <span
          class="color-red mr-3"
          v-if="$store.state.current_submission.current_state === 'finalized' && $store.state.form.tabs.flags && !$store.state.current_submission.flag_valid && $store.state.form.tabs.flags.showValid"
        >
          <i class="fa fa-exclamation-circle fa-sm mr-2"></i>
          <span v-translate>Not valid</span>
        </span>
        <span
          v-b-tooltip.hover
          :title="superseded_tooltip"
          class="color-red mb-2"
          v-if="$store.state.current_submission.flag_superseded"
        >
          <i class="fa fa-exclamation-circle fa-sm mr-2"></i>
          <span v-translate>Superseded</span>
          &nbsp;
          <i style="color: black" class="fa fa-info-circle fa-sm"></i>
        </span>
      </div>
    <!-- </div> -->
    <!-- <div v-else>
      <span
        class="color-green mr-3"
        v-if="$store.state.current_submission.current_state === 'finalized' && flag_approved_field.selected"
      >
        <i class="fa fa-check-circle fa-sm mr-2"></i>
        <span v-translate>Approved</span>
      </span>
      <span
        class="color-red mr-3"
        v-if="$store.state.current_submission.current_state === 'finalized' && !flag_approved_field.selected"
      >
        <i class="fa fa-window-close fa-sm mr-2"></i>
        <span v-translate>Not approved</span>
      </span>
    </div> -->
    <div class="mt-2">
      <span v-translate>Status</span>&#8239;
      <em>{{ labels[$store.state.current_submission.current_state] }}</em>
    </div>
    <div class="mt-2">
      <span v-translate>Version</span>&#8239;
      <em>{{$store.state.current_submission.version}}</em>
    </div>
    <div class="mt-2">
      <span v-translate>Created by</span>&#8239;
      <em>{{$store.state.current_submission.created_by + ' (' + ($store.state.current_submission.filled_by_secretariat ? $gettext('secretariat'): $gettext('party')) + ')'}}</em>&#8239;
      <span v-translate>at</span>&#8239;
      <em>{{dateFormat($store.state.current_submission.created_at)}}</em>
    </div>
    <div class="mt-2">
      <span v-translate>Last changed by</span>&#8239;
      <em>{{$store.state.current_submission.last_edited_by + ' (' + ($store.state.current_submission.filled_by_secretariat ? $gettext('secretariat'): $gettext('party')) + ')'}}</em>&#8239;
      <span v-translate>at</span>&#8239;
      <em>{{dateFormat($store.state.current_submission.updated_at)}}</em>
    </div>
  </div>
</template>

<script>
import { getCommonLabels } from '@/components/common/dataDefinitions/labels'
import { dateFormatToDisplay } from '@/components/common/services/languageService.js'

export default {
  data() {
    return {
      superseded_tooltip: this.$gettext('Another version has been submitted, overriding this one'),
      labels: getCommonLabels(this.$gettext)
    }
  },
  methods: {
    dateFormat(date) {
      return dateFormatToDisplay(date)
    }
  }
  // computed: {
  //   flag_approved_field() {
  //     return this.$store.state.form.tabs.flags && this.$store.state.form.tabs.flags.form_fields.flag_approved
  //   }
  // }
}
</script>
<style scoped>
.color-green {
  color: green;
}
.color-red {
  color: red;
}
</style>

