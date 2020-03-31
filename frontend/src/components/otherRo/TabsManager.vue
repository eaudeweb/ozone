<template>
  <div>
    <div class="breadcrumb custom">
      <small style="width: 30%;">
        <b-btn
          style="margin-right:.5rem"
          variant="primary"
          @click="createModalData"
          v-show="!selectedTab.hideInfoButton"
        >
          <i class="fa fa-info fa-lg"></i>
        </b-btn>
        <div v-html="selectedTab.detailsHtml"></div>
      </small>
      <div class="tab-title">
        <div v-if="selectedTab.tooltipHtml" v-b-tooltip :title="selectedTab.tooltipHtml">
          <span v-html="selectedTab.titleHtml"></span>
          <i style="margin-left: 5px" class="fa fa-info-circle fa-lg"></i>
        </div>
        <div v-else v-html="selectedTab.titleHtml"></div>
      </div>
    </div>

    <b-modal size="lg" ref="instructions_modal" id="instructions_modal">
      <div v-if="modal_data" v-html="modal_data"></div>
      <div slot="modal-footer">
        <b-btn @click="$refs.instructions_modal.hide()" variant="success">
          <span v-translate>Close</span>
        </b-btn>
      </div>
    </b-modal>

    <div class="form-wrapper" style="position: relative">
      <b-card style="margin-bottom: 5rem;" no-body>
        <b-tabs no-key-nav v-model="tabIndex" card>
          <b-tab active>
            <template slot="title">
              <tab-title-with-loader :tab="$store.state.form.tabs.sub_info"/>
            </template>
            <SubmissionInfo
              ref="sub_info"
              :flags_info="$store.state.form.tabs.flags"
              :info="$store.state.form.tabs.sub_info"
              :tabId="0"
            />
          </b-tab>
          <b-tab>
            <template slot="title">
              <tab-title-with-loader :tab="$store.state.form.tabs.files"/>
            </template>
            <Files :tabIndex="tabIndex" :tabId="1"/>
          </b-tab>
          <b-tab v-for="tabId in formTabs" :key="tabId">
            <template slot="title">
              <tab-title-with-loader :tab="$store.state.form.tabs[tabId]"/>
            </template>
            <FormTemplate
              :tabId="$store.state.form.formDetails.tabsDisplay.indexOf(tabId)"
              :tabIndex="tabIndex"
              :tabName="tabId"
            />
          </b-tab>
        </b-tabs>
      </b-card>
    </div>
    <Footer style="display:inline">
      <Save
        class="actions mt-2 mb-2"
        v-show="$store.getters.can_enable_edit_mode && $store.getters.edit_mode"
        :data="$store.state.form"
        :submission="submission"
        :obligation_type="obligation_type"
      ></Save>
      <Edit :submission="submission" :obligation_type="obligation_type" class="actions mt-2 mb-2" />
      <router-link class="btn mt-2 mb-2 btn-light ml-2" :to="{name: 'Dashboard'}" v-translate>Close</router-link>
      <b-button-group v-if="$store.state.recordDataObligations.includes(obligation_type) && $store.state.currentUser.is_secretariat && $store.state.current_submission.submitted_at" class="pull-right actions ml-2 mt-2 mb-2">
        <b-btn
          :href="`${api}/admin/core/transfer/add/?submission_id=${$store.state.current_submission.id}`"
          target="_blank"
          variant="outline-primary"
        >
          <span v-translate>Record Data</span>
        </b-btn>
      </b-button-group>
      <b-button-group class="pull-right actions mt-2 mb-2">
        <b-btn v-if="$store.state.current_submission.is_versionable" @click="$refs.history_modal.show()" variant="outline-dark">
          <span v-translate>Versions</span>
        </b-btn>
      </b-button-group>
      <b-button-group class="pull-right actions mt-2 mb-2">
        <b-btn
          v-if="$store.state.current_submission.available_transitions.includes('submit')"
          @click="checkBeforeSubmitting"
          variant="outline-primary"
        >
          <span v-translate>Submit</span>
        </b-btn>
        <b-btn
          variant="outline-primary"
          v-for="transition in availableTransitions"
          :key="transition"
          @click="currentTransition = transition"
        >
          <span>{{labels[transition]}}</span>
        </b-btn>

        <b-btn
          variant="outline-primary"
          @click="clone($route.query.submission)"
          v-if="$store.state.current_submission.is_cloneable"
          :disabled="$store.state.currentUser.is_read_only"
        >Revise</b-btn>
        <b-btn
          @click="removeSubmission"
          id="delete-button"
          v-if="$store.getters.can_edit_data"
          variant="outline-danger"
        >
          <span v-translate>Delete Submission</span>
        </b-btn>
      </b-button-group>
    </Footer>

    <b-modal
      size="lg"
      ref="history_modal"
      id="history_modal"
      :title="$gettext('Submission versions')"
    >
      <SubmissionHistory
        :history="$store.state.currentSubmissionHistory"
        :currentVersion="$store.state.current_submission.version"
      ></SubmissionHistory>
      <div slot="modal-footer">
        <b-btn @click="$refs.history_modal.hide()" variant="success">
          <span v-translate>Close</span>
        </b-btn>
      </div>
    </b-modal>
    <TransitionQuestions
      v-on:removeTransition="currentTransition = null"
      :submission="submission"
      :transition="currentTransition"
      :skipArt7Specific="true"
    ></TransitionQuestions>
  </div>
</template>

<script>
import { Footer } from '@coreui/vue'
import SubmissionInfo from '@/components/common/SubmissionInfo.vue'
import Edit from '@/components/common/Edit'
import Files from '@/components/common/Files'

import { api, getInstructions, cloneSubmission } from '@/components/common/services/api'
import Save from '@/components/otherRo/Save'

import SubmissionHistory from '@/components/common/SubmissionHistory.vue'
import { getLabels } from '@/components/hat/dataDefinitions/labels'
import TabTitleWithLoader from '@/components/common/TabTitleWithLoader'
import FormTemplate from '@/components/otherRo/FormTemplate.vue'
import TransitionQuestions from '@/components/common/TransitionQuestions'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'

export default {
  components: {
    SubmissionInfo,
    Edit,
    Files,
    Footer,
    Save,
    SubmissionHistory,
    TabTitleWithLoader,
    FormTemplate,
    TransitionQuestions
  },
  props: {
    data: null,
    submission: String,
    obligation_type: String
  },
  data() {
    return {
      api,
      tabIndex: 0,
      modal_data: null,
      labels: getLabels(this.$gettext).common,
      currentTransition: null,
      alerts: getAlerts(this.$gettext)
    }
  },
  created() {
    this.updateBreadcrumbs()
    this.api = api.defaults.apiBase
  },
  computed: {
    availableTransitions() {
      return this.$store.state.current_submission.available_transitions.filter(t => t !== 'submit')
    },
    selectedTab() {
      const { form } = this.$store.state
      const tab = form.tabs[form.formDetails.tabsDisplay[this.tabIndex]]
      return tab
    },
    formTabs() {
      const { form } = this.$store.state
      return form.formDetails.tabsDisplay.filter(tabName => !['files', 'sub_info'].includes(tabName)).filter(tabName => this.$store.state.form.tabs[tabName].form_fields.length)
    }
  },
  methods: {
    async clone(submissionId) {
      const confirmed = await this.$store.dispatch('openConfirmModal', { title: 'Please confirm', description: 'You are about to create a new version for data entry. The current version will be superseded once the new version is submitted.', $gettext: this.$gettext })
      if (!confirmed) {
        return
      }
      cloneSubmission(submissionId).then((response) => {
        this.$router.push({ name: this.$route.name, query: { submission: response.data.id }, params: { obligation_type: this.obligation_type } })
        this.$router.go(this.$router.currentRoute)
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { __all__: [this.alerts.new_version_created] },
          variant: 'success'
        })
        this.$destroy()
      }).catch(error => {
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { ...error.response.data },
          variant: 'danger' })
        console.log(error)
      })
    },
    updateBreadcrumbs() {
      this.$store.commit('updateBreadcrumbs', `${this.$store.state.current_submission.reporting_period_description} ${this.$store.state.current_submission.obligation} ${this.$gettext('data submission for')} ${this.$store.state.initialData.display.countries[this.$store.state.current_submission.party]}`)
    },
    createModalData() {
      const tabName = this.$store.state.form.formDetails.tabsDisplay[this.tabIndex]
      const formName = this.$route.name
      getInstructions(formName, tabName).then((response) => {
        this.modal_data = response.data
        this.$refs.instructions_modal.show()
      })
    },
    checkBeforeSubmitting() {
      const unsavedTabs = Object.values(this.$store.state.form.tabs).filter(tab => [false, 'edited'].includes(tab.status))
      if (unsavedTabs.length) {
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { __all__: [this.alerts.save_before_submitting] },
          variant: 'danger'
        })
        return
      }
      this.currentTransition = 'submit'
      // this.$store.dispatch('doSubmissionTransition', { $gettext: this.$gettext, submission: this.submission, transition: 'submit' })
    },
    removeSubmission() {
      this.$store.dispatch('removeSubmission', {
        $gettext: this.$gettext,
        submissionId: this.submission
      }).then((result) => {
        if (result) {
          this.$router.push({ name: 'Dashboard' })
        }
      })
    }
  },
  watch: {
    '$language.current': {
      handler() {
        this.updateBreadcrumbs()
      }
    },
    '$store.state.current_submission.current_state': {
      handler() {
        this.updateBreadcrumbs()
      }
    }
  }
}

</script>

<style lang="css" scoped>
.legend {
  padding: 0.2rem 2rem;
  background: #f0f3f5;
}

.legend .spinner {
  margin-left: 0;
}
</style>
