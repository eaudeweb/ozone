<template>
  <div v-if="info" class="submission-info-tab">
    <form class="form-sections table-wrapper">
      <b-row>
        <!-- Submission Info column -->
        <b-col md="7" lg="7">
          <div class="form-fields">
            <b-row
              v-for="field in submissionInfoFields"
              class="field-wrapper"
              :id="field"
              :key="field"
            >
              <b-col lg="3">
                <span
                  v-if="info.form_fields[field].tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="info.form_fields[field].tooltip"
                >
                  <label>{{labels[field]}}</label>&nbsp;
                  <i class="fa fa-info-circle fa-sm"></i>
                </span>
                <span v-else>
                  <label>
                    {{labels[field]}}
                    <div
                      v-if="info.form_fields[field].description"
                      class="floating-error"
                      :class="{danger: info.form_fields[field].validation && error_danger}"
                    >({{ info.form_fields[field].description }})</div>
                  </label>
                </span>
              </b-col>
              <b-col>
                <fieldGenerator
                  :fieldInfo="{index:field, tabName: info.name, field:field}"
                  :field="info.form_fields[field]"
                  :disabled="isSubmissionInfoReadOnly(field)"
                ></fieldGenerator>
              </b-col>
            </b-row>

            <b-row
              v-if="isSecretariat || (!isSecretariat && info.form_fields['submitted_at'].selected)"
            >
              <b-col lg="3">
                <label>
                  {{labels.submitted_at}}
                  <div
                    v-if="info.form_fields['submitted_at'].description"
                    variant="danger"
                    class="floating-error"
                    :class="{danger: info.form_fields['submitted_at'].validation && error_danger}"
                  >({{ info.form_fields['submitted_at'].description }})</div>
                </label>
              </b-col>
              <b-col>
                <fieldGenerator
                  :fieldInfo="{index:'submitted_at', tabName: info.name, field:'submitted_at'}"
                  :field="info.form_fields.submitted_at"
                  :disabled="isSubmissionInfoReadOnly('submitted_at')"
                ></fieldGenerator>
              </b-col>
            </b-row>
          </div>
        </b-col>
        <!-- Flags column -->
        <b-col>
          <h5>
            <span v-if="flags_info" v-translate>Flags</span>
          </h5>
          <b-card v-if="flags_info" id="flags">
            <b-row class="mb-2">
              <b-col>
                <!-- General flags -->
                <div class="d-flex" v-for="flag in general_flags" :key="flag">
                  <fieldGenerator
                    :id="flag"
                    :fieldInfo="{ index: flag, tabName: flags_info.name, field: flag }"
                    :field="flags_info.form_fields[flag]"
                    :disabled="isFlagReadOnly('flag_provisional')"
                    @change="setTabStatus"
                  ></fieldGenerator>
                  <label
                    style="margin-left: -3px"
                    :class="{'muted': flags_info.form_fields[flag].disabled}"
                    :for="flag"
                  >
                    <div
                      v-if="flags_info.form_fields[flag].tooltip"
                      v-b-tooltip.hover
                      placement="left"
                      :title="flags_info.form_fields[flag].tooltip"
                    >
                      {{labels.flags[flag]}}
                      <i class="fa fa-info-circle fa-sm"></i>
                    </div>
                    <div v-else>{{labels.flags[flag]}}</div>
                  </label>
                </div>
              </b-col>
              <b-col v-if="isSecretariat">
                <!-- Blank flags -->
                <div class="d-flex" v-for="flag in blank_flags" :key="flag">
                    <fieldGenerator
                      :id="flag"
                      :fieldInfo="{index:flag, tabName: flags_info.name, field:flag}"
                      :field="flags_info.form_fields[flag]"
                      :disabled="isFlagReadOnly('flag_blank')"
                      @change="setTabStatus"
                    ></fieldGenerator>
                    <label
                      style="margin-left: -3px"
                      :class="{'muted': flags_info.form_fields[flag].disabled}"
                      :for="flag"
                    >
                      <div
                        v-if="flags_info.form_fields[flag].tooltip"
                        v-b-tooltip.hover
                        placement="left"
                        :title="flags_info.form_fields[flag].tooltip"
                      >
                        <i class="fa fa-info-circle fa-sm"></i>
                        {{labels.flags[flag]}}
                      </div>
                      <div v-else>{{labels.flags[flag]}}</div>
                    </label>
                </div>
              </b-col>
            </b-row>
          </b-card>
          <!-- Annex groups flags -->
          <h5
            v-if="flags_info && annex_group_flags_columns.length"
            v-translate
            v-b-tooltip.hover
            placement="left"
            class="mb-3"
            :title="$gettext('Select the annex groups for which you are submitting complete data, including reporting of zeros where appropriate, e.g. for phased-out substances or annex groups.')"
          >
            Annex groups reported in full
            <i class="fa fa-info-circle fa-sm"></i>
          </h5>
          <b-card v-if="flags_info && annex_group_flags_columns.length">
            <div id="annex-flags">
              <div
                v-for="column in annex_group_flags_columns"
                class="flags-row"
                :key="column"
              >
                <div
                  v-for="flag in annex_group_flags.filter(o => o.split('_')[3].includes(column))"
                  class="specific-flags-wrapper"
                  :key="flag"
                >
                  <span cols="1">
                    <fieldGenerator
                      :id="flag"
                      :fieldInfo="{index:flag, tabName: flags_info.name, field:flag}"
                      :field="flags_info.form_fields[flag]"
                      :disabled="isFlagReadOnly('flag_annex_group')"
                      @change="setTabStatus"
                    ></fieldGenerator>
                  </span>
                  <span>
                    <label
                      :class="{'muted': flags_info.form_fields[flag].disabled}"
                      :for="flag"
                    >
                      <div
                        v-if="flags_info.form_fields[flag].tooltip"
                        v-b-tooltip.hover
                        placement="left"
                        :title="flags_info.form_fields[flag].tooltip"
                      >
                        <i class="fa fa-info-circle fa-sm"></i>
                        {{labels.flags[flag]}}
                      </div>
                      <div v-else>{{labels.flags[flag]}}</div>
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
            <SubmissionStatus :hasVersions="hasVersions"/>
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
import PermissionsMixin from '@/components/common/mixins/PermissionsMixin'

export default {
  mixins: [PermissionsMixin],

  props: {
    info: Object,
    flags_info: Object,
    hasVersions: Boolean
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
      return ['flag_checked_blanks', 'flag_has_blanks', 'flag_confirmed_blanks']
    },

    annex_group_flags() {
      // has_reported_xxx
      return Object.keys(this.flags_info.form_fields).filter(f => this.flags_info.fields_order.includes(f) && ![...this.general_flags, ...this.exclude_flags, ...this.blank_flags, 'validation'].includes(f))
    },

    annex_group_flags_columns() {
      return [...new Set(this.annex_group_flags.map(f => f.split('_')[3]).map(f => f.split('')[0]))]
    },

    is_data_entry() {
      this.info.form_fields.current_state.selected = this.$store.state.current_submission.current_state === 'data_entry'
      return this.$store.state.current_submission.current_state === 'data_entry'
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
      if (!this.isSecretariat || submitted_at.selected) {
        submitted_at.validation = null
      } else {
        submitted_at.validation = this.$gettext('Required')
      }
      if (!this.is_data_entry) {
        submitted_at.validation = null
      }
      this.$forceUpdate()
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
