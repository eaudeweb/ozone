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
              :info="$store.state.form.tabs.sub_info"
              :tabId="0"
              :hasVersions="false"
            />
          </b-tab>
          <b-tab>
            <template slot="title">
              <tab-title-with-loader :tab="$store.state.form.tabs.files"/>
            </template>
            <Files :tabId="1" :tabIndex="tabIndex" />
          </b-tab>
          <b-tab v-for="tabId in tabsIdsForSecretariat" :key="tabId">
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
      <b-button-group class="pull-left actions my-md-3 my-2">
        <Save
          class="actions"
          :data="$store.state.form"
          :submission="submission"
        ></Save>
        <Edit :submission="submission" class="actions" />
        <router-link class="btn btn-light ml-0 ml-md-2" :to="{name: 'Dashboard'}" v-translate>Close</router-link>
      </b-button-group>

      <b-button-group class="pull-right actions my-md-3 my-2 ml-md-2">
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
          @click="removeSubmission"
          id="delete-button"
          v-if="$store.state.current_submission.can_delete_data"
          variant="outline-danger"
        >
          <span v-translate>Delete Submission</span>
        </b-btn>
      </b-button-group>
    </Footer>
    <TransitionQuestions
      v-on:removeTransition="currentTransition = null"
      :submission="submission"
      :transition="currentTransition"
      :hasVersions="false"
    ></TransitionQuestions>
  </div>
</template>

<script>
import { Footer } from '@coreui/vue'
import SubmissionInfo from '@/components/common/SubmissionInfo.vue'
import Edit from '@/components/common/Edit'
import Files from '@/components/common/Files'
import { getInstructions } from '@/components/common/services/api'
import Save from '@/components/exemption/Save'
import { getLabels } from '@/components/art7/dataDefinitions/labels'
import TabTitleWithLoader from '@/components/common/TabTitleWithLoader'
import FormTemplate from '@/components/exemption/FormTemplate.vue'
import TransitionQuestions from '@/components/exemption/TransitionQuestions'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'

export default {
  components: {
    SubmissionInfo,
    Edit,
    Files,
    Footer,
    Save,
    TabTitleWithLoader,
    FormTemplate,
    TransitionQuestions
  },
  props: {
    data: null,
    submission: String
  },
  data() {
    return {
      tabIndex: 0,
      modal_data: null,
      labels: getLabels(this.$gettext).common,
      currentTransition: null,
      alerts: getAlerts(this.$gettext)
    }
  },
  created() {
    this.updateBreadcrumbs()
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
    tabsIdsForSecretariat() {
      const { form } = this.$store.state
      const tabIds = form.formDetails.tabsDisplay.filter(tabName => form.tabs[tabName].hasAssideMenu)
      tabIds.forEach(tabId => {
        if (!this.is_secretariat) {
          this.$store.state.form.tabs[tabId].skipSave = true
        }
      })
      return tabIds
    },
    is_secretariat() {
      return this.$store.state.currentUser.is_secretariat
    }
  },
  methods: {
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
        this.$store.commit('setActionToDispatch', null)
        this.$store.commit('setDataForAction', null)
        return
      }
      this.currentTransition = 'submit'
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
