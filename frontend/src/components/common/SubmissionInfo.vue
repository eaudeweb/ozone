<template>
  <div v-if="info" class="submission-info-tab">
    <form class="form-sections table-wrapper">
      <b-row>
        <b-col md="7" lg="7">
            <div class="form-fields">
              <b-row
                :id="order"
                v-for="order in submissionInfoFields"
                class="field-wrapper"
                :key="order"
              >
                <b-col lg="3">
                  <span
                    v-if="info.form_fields[order].tooltip"
                    v-b-tooltip.hover
                    placement="left"
                    :title="info.form_fields[order].tooltip"
                  >
                    <label>{{labels[order]}}</label>&nbsp;
                    <i class="fa fa-info-circle fa-sm"></i>
                  </span>
                  <span v-else>
                    <label>
                      {{labels[order]}}
                      <div
                        class="floating-error"
                        :class="{danger: info.form_fields[order].validation && error_danger}"
                        v-if="info.form_fields[order].description"
                      >({{ info.form_fields[order].description }})</div>
                    </label>
                  </span>
                </b-col>
                <b-col>
                  <fieldGenerator
                    :fieldInfo="{index:order, tabName: info.name, field:order}"
                    :disabled="isDisabled(order)"
                    :field="info.form_fields[order]"
                  ></fieldGenerator>
                </b-col>
              </b-row>
              <b-row
                v-if="is_secretariat || (!is_secretariat && info.form_fields['submitted_at'].selected)"
              >
                <b-col lg="3">
                  <label>
                    {{labels.submitted_at}}
                    <div
                      :class="{danger: info.form_fields['submitted_at'].validation && error_danger}"
                      class="floating-error"
                      v-if="info.form_fields['submitted_at'].description"
                      variant="danger"
                    >({{ info.form_fields['submitted_at'].description }})</div>
                  </label>
                </b-col>
                <b-col>
                  <fieldGenerator
                    :fieldInfo="{index:'submitted_at', tabName: info.name, field:'submitted_at'}"
                    :field="info.form_fields.submitted_at"
                    :disabled="isDisabled('submitted_at')"
                  ></fieldGenerator>
                </b-col>
              </b-row>
            </div>
        </b-col>

        <b-col>
          <h5>
            <span v-if="flags_info" v-translate>Flags</span>
          </h5>
          <b-card v-if="flags_info" id="flags">
            <b-row class="mb-2">
              <b-col>
                <div class="d-flex" v-for="order in general_flags" :key="order">
                  <fieldGenerator
                    :fieldInfo="{index:order, tabName: flags_info.name, field:order}"
                    :disabled="$store.getters.transitionState || !$store.getters.edit_mode"
                    :field="flags_info.form_fields[order]"
                    :id="order"
                    @change="setTabStatus"
                  ></fieldGenerator>
                  <label style="margin-left: -3px" :class="{'muted': flags_info.form_fields[order].disabled}" :for="order">
                    <div
                      v-if="flags_info.form_fields[order].tooltip"
                      v-b-tooltip.hover
                      placement="left"
                      :title="flags_info.form_fields[order].tooltip"
                    >
                      {{labels.flags[order]}}
                      <i class="fa fa-info-circle fa-sm"></i>
                    </div>
                    <div v-else>{{labels.flags[order]}}</div>
                  </label>
                </div>
              </b-col>
              <b-col v-if="$store.state.currentUser.is_secretariat" >
                <div class="d-flex" v-for="order in blank_flags" :key="order">
                    <fieldGenerator
                      :fieldInfo="{index:order, tabName: flags_info.name, field:order}"
                      :disabled="$store.getters.transitionState || !$store.getters.edit_mode || (is_secretariat && is_submitted && created_by_party)"
                      :field="flags_info.form_fields[order]"
                      :id="order"
                      @change="setTabStatus"
                    ></fieldGenerator>
                    <label style="margin-left: -3px" :class="{'muted': flags_info.form_fields[order].disabled}" :for="order">
                      <div
                        v-if="flags_info.form_fields[order].tooltip"
                        v-b-tooltip.hover
                        placement="left"
                        :title="flags_info.form_fields[order].tooltip"
                      >
                        <i class="fa fa-info-circle fa-sm"></i>
                        {{labels.flags[order]}}
                      </div>
                      <div v-else>{{labels.flags[order]}}</div>
                    </label>
                </div>
              </b-col>
            </b-row>
          </b-card>

          <h5 v-if="flags_info && specific_flags_columns.length"
            class="mb-3" v-translate v-b-tooltip.hover placement="left"
            :title="$gettext('Select the annex groups for which you are submitting complete data, including reporting of zeros where appropriate, e.g. for phased-out substances or annex groups.')">
            Annex groups reported in full
            <i class="fa fa-info-circle fa-sm"></i>
          </h5>
          <b-card v-if="flags_info && specific_flags_columns.length">
            <div id="annex-flags">
              <div class="flags-row" v-for="column in specific_flags_columns" :key="column">
                <div
                  class="specific-flags-wrapper"
                  v-for="order in specific_flags.filter(o => o.split('_')[3].includes(column))"
                  :key="order"
                >
                  <span cols="1">
                    <fieldGenerator
                      :fieldInfo="{index:order, tabName: flags_info.name, field:order}"
                      :disabled="$store.getters.transitionState || !$store.getters.edit_mode"
                      :field="flags_info.form_fields[order]"
                      :id="order"
                      @change="setTabStatus"
                    ></fieldGenerator>
                  </span>
                  <span>
                    <label :class="{'muted': flags_info.form_fields[order].disabled}" :for="order">
                      <div
                        v-if="flags_info.form_fields[order].tooltip"
                        v-b-tooltip.hover
                        placement="left"
                        :title="flags_info.form_fields[order].tooltip"
                      >
                        <i class="fa fa-info-circle fa-sm"></i>
                        {{labels.flags[order]}}
                      </div>
                      <div v-else>{{labels.flags[order]}}</div>
                    </label>
                  </span>
                </div>
              </div>
            </div>
          </b-card>

          <h5>
            <span v-translate>Submission status</span>
          </h5>
          <b-card>
            <SubmissionStatus/>
          </b-card>
        </b-col>
      </b-row>
    </form>
  </div>
</template>

<script>

import fieldGenerator from '@/components/common/form-components/fieldGenerator'
import { getCommonLabels } from '@/components/common/dataDefinitions/labels'
import SubmissionStatus from '@/components/common/SubmissionStatus'

export default {
  props: {
    info: Object,
    flags_info: Object
  },

  created() {
    this.labels = getCommonLabels(this.$gettext)
    this.setSubmitted_atValidation()
  },

  components: {
    fieldGenerator,
    SubmissionStatus
  },

  computed: {
    submissionInfoFields() {
      return this.info.filterOut ? this.info.fields_order.filter(field => !this.info.filterOut.includes(field)) : this.info.fields_order
    },

    onlySelectedValue() {
      return Object.keys(this.info.form_fields).filter(field => !['current_state', 'validation'].includes(field)).map(field => this.info.form_fields[field].selected)
    },
    error_danger() {
      return this.info.status === false
    },
    general_flags() {
      return ['flag_provisional']
    },
    exclude_flags() {
      return ['flag_superseded', 'flag_valid']
    },
    blank_flags() {
      return Object.keys(this.flags_info.form_fields).filter(f => this.flags_info.fields_order.includes(f) && f !== 'validation' && f.split('_').includes('blanks'))
    },

    specific_flags() {
      return Object.keys(this.flags_info.form_fields).filter(f => this.flags_info.fields_order.includes(f) && ![...this.general_flags, ...this.exclude_flags, ...this.blank_flags, 'validation'].includes(f))
    },

    specific_flags_columns() {
      return [...new Set(this.specific_flags.map(f => f.split('_')[3]).map(f => f.split('')[0]))]
    },

    is_secretariat() {
      return this.$store.state.currentUser.is_secretariat
    },
    is_data_entry() {
      this.info.form_fields.current_state.selected = this.$store.state.current_submission.current_state === 'data_entry'
      return this.$store.state.current_submission.current_state === 'data_entry'
    },
    is_submitted() {
      return this.$store.state.current_submission.current_state === 'submitted'
    },
    created_by_party() {
      return this.$store.state.current_submission.created_by !== 'secretariat'
    }
  },

  data() {
    return {
      labels: null
    }
  },

  methods: {
    setSubmitted_atValidation() {
      const { submitted_at } = this.info.form_fields
      if (!this.is_secretariat || submitted_at.selected) {
        submitted_at.validation = null
      } else {
        submitted_at.validation = this.$gettext('Required')
      }
      if (!this.is_data_entry) {
        submitted_at.validation = null
      }
      this.$forceUpdate()
    },
    checkUserType(order) {
      if (order === 'reporting_channel') {
        return !this.$store.getters.can_change_reporting_channel
      }
      if (order === 'submission_format' && !this.$store.state.currentUser.is_secretariat) {
        return true
      }
      return !this.$store.getters.can_edit_data
    },
    isDisabled(order) {
      if (order === 'reporting_channel') {
        return !(this.$store.getters.can_change_reporting_channel && this.$store.getters.edit_mode)
      }
      if (order === 'submission_format' && !this.$store.state.currentUser.is_secretariat) {
        return true
      }
      if (order === 'submitted_at') {
        !(this.$store.state.current_submission.can_change_submitted_at && this.$store.getters.edit_mode)
      }
      return !this.$store.getters.edit_mode
    },
    setTabStatus(fieldInfo) {
      //  Set flags tab status when flag is ticked
      if (fieldInfo && fieldInfo.tabName === 'flags') {
        if (this.$store.state.current_submission.changeable_flags.includes(fieldInfo.index)) {
          this.$store.commit('setTabStatus', { tab: fieldInfo.tabName, value: 'edited' })
        }
      }
    }
  },
  watch: {
    '$language.current': {
      handler() {
        this.labels = getCommonLabels(this.$gettext)
      }
    },
    'info.form_fields.submitted_at.selected': {
      handler() {
        this.setSubmitted_atValidation()
      }
    },
    'onlySelectedValue': {
      handler(old_val, new_val) {
        if (this.info.status !== 'edited' && JSON.stringify(old_val) !== JSON.stringify(new_val)) {
          this.$store.commit('setTabStatus', {
            tab: 'sub_info',
            value: 'edited'
          })
        }
      }
    }
  }
}
</script>
