<template>
  <div>
    <div>
      <div v-if="provisional">
        <p>Kindly note that the data being submitted is marked as provisional. Another report will need to be submitted with the final data.</p>
      </div>
      <div v-else>
        <p>You are about to submit your report.</p>
        <p>By clicking the OK button, you confirm that all blank cells and all substances not included are considered to have zero values.</p>
      </div>
      <div v-if="questionnaireStatus.length && !skipArt7Specific">
        <p><b>You have chosen "Yes" in the questionnaire, but not entered any substances in {{questionnaireStatus.join(', ')}} form.</b></p>
      </div>
      <div v-if="uncheckedFlags.length && !skipArt7Specific">
        <p class="color-red"><b> Under the TAB for 'Submission Information', you have not selected to report data for annex group(s) {{uncheckedFlags.join(', ')}}. Kindly note that these annex groups will be treated as 'NOT REPORTED' until the data is reported in full.</b></p>
      </div>
    </div>
    <div v-if="$store.state.currentUser.is_secretariat && formTabs.flags && !skipArt7Specific">
      <b-row v-for="order in blank_flags" :key="order">
        <b-col cols="1">
          <fieldGenerator
            :fieldInfo="{index:order, tabName: 'flags', field:order}"
            :disabled="$store.getters.transitionState"
            :field="formTabs.flags.form_fields[order]"
            :id="order"
          ></fieldGenerator>
        </b-col>
        <b-col>
          <label :class="{'muted': formTabs.flags.form_fields[order].disabled}" :for="order">
            <div
              v-if="formTabs.flags.form_fields[order].tooltip"
              v-b-tooltip.hover
              placement="left"
              :title="formTabs.flags.form_fields[order].tooltip"
            >
              <i class="fa fa-info-circle fa-lg"></i>
              {{labels.flags[order]}}
            </div>
            <div v-else>{{labels.flags[order]}}</div>
          </label>
        </b-col>
      </b-row>
    </div>

    <div v-if="$store.state.currentUser.is_secretariat && hasVersions">
      <p><b-form-checkbox
          id="minor_transition"
          v-model="increment_minor"
          name="minor_transition"
        >This is a minor revision.
      </b-form-checkbox></p>
    </div>
    <p>TODO: remove me: {{ increment_minor }}</p>
    <div>
      <p>Press OK to continue with the submission. Press Cancel to make further changes or corrections.</p>
    </div>
  </div>
</template>

<script>
import fieldGenerator from '@/components/common/form-components/fieldGenerator'
import { getCommonLabels } from '@/components/common/dataDefinitions/labels'
import flagMapping from '@/components/common/dataDefinitions/flagsMapping'

export default {
  data() {
    return {
      labels: null,
      flagMapping,
      increment_minor: this.$store.state.currentUser.is_secretariat
    }
  },
  props: {
    skipArt7Specific: Boolean,
    hasVersions: Boolean
  },
  created() {
    this.labels = getCommonLabels(this.$gettext)
  },
  components: {
    fieldGenerator
  },
  computed: {
    provisional() {
      return this.formTabs.flags && this.formTabs.flags.form_fields.flag_provisional && this.formTabs.flags.form_fields.flag_provisional.selected
    },
    blank_flags() {
      return this.$store.state.form.tabs.flags && Object.keys(this.formTabs.flags.form_fields).filter(f => this.formTabs.flags.fields_order.includes(f) && f !== 'validation' && f.split('_').includes('blanks'))
    },
    questionnaire() {
      return this.$store.state.form.tabs.questionaire_questions && this.formTabs.questionaire_questions
    },
    formTabs() {
      return this.$store.state.form.tabs
    },
    questionnaireStatus() {
      if (!this.questionnaire) {
        return []
      }
      const answeredYes = Object.keys(this.questionnaire.form_fields).filter(q => this.questionnaire.form_fields[q].selected)
      const anweredYesNoData = Object.keys(this.formTabs).filter(tab => answeredYes.includes(tab) && !this.formTabs[tab].form_fields.length)
      return anweredYesNoData.map(tab => this.labels[tab])
    },
    uncheckedFlags() {
      if (!this.$store.state.form.tabs.flags || this.skipArt7Specific) {
        return []
      }
      return Object.keys(this.formTabs.flags.form_fields).filter(
        flag => flag.includes('flag_has_reported')
        && !this.formTabs.flags.form_fields[flag].selected
        && this.$store.state.initialData.controlledGroups.includes(this.flagMapping[flag])
      ).map(flag => this.labels.flags[flag])
    }
  },
  methods: {
  },
  watch: {

  }
}
</script>

