<template>
  <div>
  <div class="breadcrumb custom">
    <small style="width: 30%;">
      <b-btn style="margin-right:.5rem" variant="info-outline" @click="createModalData" v-show="!selectedTab.hideInfoButton"> <i class="fa fa-info fa-lg"></i></b-btn>
      <div v-html="selectedTab.detailsHtml"></div>
    </small>
    <div class="tab-title">
      <div  v-if='selectedTab.tooltipHtml' v-b-tooltip :title="selectedTab.tooltipHtml" >
        <span v-html="selectedTab.titleHtml"></span>
         <i style='margin-left: 5px' class="fa fa-info-circle fa-lg"></i>
      </div>
      <div v-else v-html="selectedTab.titleHtml"></div>
    </div>
   <b-button-group class="actions">
      <Save style="border-top-right-radius: .25em;border-bottom-right-radius: .25em;"  v-if="$store.state.available_transitions.includes('submit')"  :data="$store.state.form" :submission="submission"></Save>
    </b-button-group>
  </div>

    <b-modal size="lg" ref="instructions_modal" id="instructions_modal">
		<div v-if="modal_data" v-html="modal_data"></div>
		<div slot="modal-footer">
			<b-btn @click="$refs.instructions_modal.hide()" variant="success"><span v-translate>Close</span></b-btn>
		</div>
	</b-modal>

  <div class="form-wrapper" style="position: relative">
    <b-card style="margin-bottom: 5rem;" no-body>
			<b-tabs v-model="tabIndex" card>

			<b-tab active>
				<template slot="title">
					<tab-title-with-loader :tab="$store.state.form.tabs.sub_info" />
				</template>
					<SubmissionInfo ref="sub_info" :flags_info="$store.state.form.tabs.flags" :info="$store.state.form.tabs.sub_info" :tabId="0" />
			</b-tab>

			<b-tab v-for="tabId in tabsIdsWithAssideMenu" :key="tabId">
				<template slot="title">
					<tab-title-with-loader :tab="$store.state.form.tabs[tabId]" />
				</template>
				<FormTemplate :tabId="$store.state.form.formDetails.tabsDisplay.indexOf(tabId)" :tabIndex="tabIndex" :tabName="tabId" />
			</b-tab>

				<b-tab>
					<template slot="title">
						<tab-title-with-loader :tab="$store.state.form.tabs.files" />
					</template>
					<Files :tabId="2" :tabIndex="tabIndex" />
				</b-tab>
			</b-tabs>
    </b-card>
    </div>
    <Footer style="display:inline">
		<b-button-group class="actions mt-2 mb-2">
			<Save v-if="$store.state.available_transitions.includes('submit')" :data="$store.state.form" :submission="submission"></Save>
		</b-button-group>

		<b-button-group class="pull-right actions mt-2 mb-2">
			<b-btn
				v-if="$store.state.available_transitions.includes('submit')"
				@click="checkBeforeSubmitting"
				variant="outline-success">
				<span v-translate>Submit</span>
			</b-btn>
			<b-btn
				variant="outline-primary"
				v-for="transition in availableTransitions"
				:key="transition"
				@click="$store.dispatch('doSubmissionTransition', {$gettext, submission, transition})">
				<span>{{labels[transition]}}</span>
			</b-btn>
			<b-btn @click="$refs.history_modal.show()" variant="outline-info">
				<span v-translate>Versions</span>
			</b-btn>
			<b-btn @click="removeSubmission" v-if="$store.state.available_transitions.includes('submit')"  variant="outline-danger">
				<span v-translate>Delete Submission</span>
			</b-btn>
		</b-button-group>
    </Footer>

	<b-modal size="lg" ref="history_modal" id="history_modal" :title="$gettext('Submission versions')">
        <SubmissionHistory :history="$store.state.currentSubmissionHistory"
							:currentVersion="$store.state.current_submission.version">
		</SubmissionHistory>
		<div slot="modal-footer">
          <b-btn @click="$refs.history_modal.hide()" variant="success"><span v-translate>Close</span></b-btn>
		</div>
	</b-modal>
  </div>
</template>

<script>
import { Footer } from '@coreui/vue'
import SubmissionInfo from '@/components/common/SubmissionInfo.vue'
import Files from '@/components/common/Files'
import { getInstructions } from '@/components/common/services/api'
import Save from '@/components/hat/Save'
import SubmissionHistory from '@/components/common/SubmissionHistory.vue'
import { getLabels } from '@/components/raf/dataDefinitions/labels'
import TabTitleWithLoader from '@/components/common/TabTitleWithLoader'
import FormTemplate from '@/components/raf/FormTemplate.vue'

export default {
	components: {
		SubmissionInfo,
		Files,
		Footer,
		Save,
		SubmissionHistory,
		TabTitleWithLoader,
		FormTemplate
	},
	props: {
		data: null,
		submission: String
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
			const body = document.querySelector('body')
			if (tab.hasAssideMenu && !this.$store.getters.isReadOnly) {
				body.classList.add('aside-menu-lg-show')
			} else {
				body.classList.remove('aside-menu-lg-show')
			}
			return tab
		},
		tabsIdsWithAssideMenu() {
			const { form } = this.$store.state
			return form.formDetails.tabsDisplay.filter(tabName => form.tabs[tabName].hasAssideMenu)
		}
	},
	methods: {
		updateBreadcrumbs() {
			this.$store.commit('updateBreadcrumbs', [this.$gettext('Dashboard'), this.labels[this.$route.name], this.$store.state.initialData.display.countries[this.$store.state.current_submission.party], this.$store.state.current_submission.reporting_period])
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
					message: { __all__: [this.$gettext('Please save before submitting')] },
					variant: 'danger'
				})
				return
			}
			this.$store.dispatch('doSubmissionTransition', { $gettext: this.$gettext, submission: this.submission, transition: 'submit' })
		},
		removeSubmission() {
			const r = confirm(this.$gettext('Deleting the submission is ireversible. Are you sure ?'))
			if (r === true) {
				this.$store.dispatch('removeSubmission', {
					$gettext: this.$gettext,
					submissionUrl: this.submission
				}).then(() => {
					this.$router.push({ name: 'Dashboard' })
				})
			}
		}
	},
	watch: {
		'$language.current': {
			handler() {
				this.updateBreadcrumbs()
			}
		}
	},
	data() {
		return {
			tabIndex: 0,
			modal_data: null,
			labels: getLabels(this.$gettext).common
		}
	}
}

</script>

<style lang="css" scoped>
.legend {
  padding: .2rem 2rem;
  background: #f0f3f5;
}

.legend .spinner {
  margin-left: 0;
}
</style>