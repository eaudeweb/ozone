import 'toastedjs/src/sass/toast.scss'
import Toasted from 'toastedjs/dist/toasted.min.js'

import { sortAscending } from '@/components/common/services/utilsService'

import { getFormArt7 } from '@/components/art7/dataDefinitions/form'
import art7TableRowConstructor from '@/components/art7/services/tableRowConstructorService'
import { getFormLetter } from '@/components/letter/dataDefinitions/form'
import { getFormHat } from '@/components/hat/dataDefinitions/form'
import hatTableRowConstructor from '@/components/hat/services/tableRowConstructorService'
import { getFormRaf } from '@/components/raf/dataDefinitions/form'
import rafTableRowConstructor from '@/components/raf/services/tableRowConstructorService'
import { getFormExemption } from '@/components/exemption/dataDefinitions/form'
import exemptionTableRowConstructor from '@/components/exemption/services/tableRowConstructorService'

const options = {
	position: 'bottom-left',
	duration: 10000,
	theme: 'bulma'
}
const toasted = new Toasted(options)

const mutations = {
	updateBreadcrumbs(state, data) {
		state.route = data.join(' / ')
	},

	addComment(state, { data, tab, field }) {
		// If there is no field specified, it means that the data comes from server for prefill
		console.log('comments', data, tab, field)
		if (!field) {
			const [commentsData] = data
			Object.keys(state.form.tabs[tab].comments).forEach(comment => {
				state.form.tabs[tab].comments[comment].selected = commentsData[comment]
			})
		} else {
			state.form.tabs[tab].comments[field].selected = data
		}
	},

	updateFormField(state, data) {
		console.log('updateFormField', data)
		const tab = state.form.tabs[data.fieldInfo.tabName]
		const formField = tab.form_fields[data.fieldInfo.index]
		if (data.fieldInfo.index === data.fieldInfo.field) {
			formField.selected = data.value
		} else {
			formField[data.fieldInfo.field].selected = data.value
		}
	},

	setSubmissionHistory(state, data) {
		state.currentSubmissionHistory = data
	},

	setForm(state, { formName, $gettext }) {
		let currentFormStructure = null
		let tableRowConstructor = null
		switch (formName) {
		case 'art7':
			currentFormStructure = getFormArt7($gettext)
			tableRowConstructor = art7TableRowConstructor
			break
		case 'hat':
			currentFormStructure = getFormHat($gettext)
			tableRowConstructor = hatTableRowConstructor
			break
		case 'exemption':
			currentFormStructure = getFormExemption($gettext)
			tableRowConstructor = exemptionTableRowConstructor
			break
		case 'other':
			currentFormStructure = getFormLetter($gettext)
			break
		case 'essencrit':
			currentFormStructure = getFormRaf($gettext)
			tableRowConstructor = rafTableRowConstructor
			break

		default:
			break
		}
		state.form = JSON.parse(JSON.stringify(currentFormStructure))
		state.tableRowConstructor = tableRowConstructor
	},

	incrementOrderingId(state, data) {
		state.form.tabs[data.tabName].ordering_id += 1
	},

	setTabOrderingId(state, data) {
		state.form.tabs[data.tabName].ordering_id = data.ordering_id
	},

	setFormPermissions(state, data) {
		state.permissions.form = data
	},

	// dashboard

	setDashboardParties(state, data) {
		state.dashboard.parties = data
	},
	setDashboardObligations(state, data) {
		state.dashboard.obligations = data
	},
	setDashboardPeriods(state, data) {
		state.dashboard.periods = data
	},
	setDashboardSubmissions(state, data) {
		state.dashboard.submissions = data.results
		state.dashboard.table.totalRows = data.count
	},
	setCurrentUserPartyInDashboard(state, data) {
		state.dashboard.table.filters.party = data
	},
	setDashboardMySubmissions(state, data) {
		state.dashboard.mySubmissions = data
	},
	// alerts

	setCurrentAlertMessage(state, message) {
		state.currentAlert.message = message
	},

	setCurrentAlertVisibility(state, showState) {
		state.currentAlert.show = showState
	},

	setCurrentAlertVariant(state, variant) {
		state.currentAlert.variant = variant
	},

	// initial data

	updateAvailableTransitions(state, data) {
		state.available_transitions = data
	},

	setCurrentUser(state, data) {
		[state.currentUser] = data
	},

	updateSubmissionData(state, data) {
		state.current_submission = data
	},

	updatePartyRatifications(state, data) {
		state.initialData.partyRatifications = data
	},

	updateCountries(state, data) {
		state.initialData.countryOptions = data
	},

	updateCountriesDisplay(state, data) {
		state.initialData.display.countries = data
	},

	updateGroupSubstances(state, data) {
		state.initialData.groupSubstances = data
	},

	updateSubstances(state, data) {
		state.initialData.substances = data
	},

	updateNonParties(state, data) {
		state.initialData.nonParties = data
	},

	updateSubstancesDisplay(state, data) {
		state.initialData.display.substances = data
	},

	updateBlends(state, data) {
		state.initialData.blends = data
	},

	updateBlendsDisplay(state, data) {
		state.initialData.display.blends = data
	},

	setBlendComponentRowVariant(state, data) {
		data.component._rowVariant = data.value
	},

	addAlertData(state, data) {
		const toastedOptions = {
			danger: 'error',
			success: 'success'
		}
		const now = new Date()
		state.alertData = state.alertData.filter(x => x.expires > now)
		const existingDisplayMessage = state.alertData.find(x => x.displayMessage === data.displayMessage)
		if (!existingDisplayMessage) {
			state.alertData.push({
				...data,
				expires: new Date((new Date()).getTime() + 5000)
			})
			toasted.show(data.displayMessage, { type: toastedOptions[data.variant], position: 'bottom-right' })
		}
	},

	// questionaire
	updateQuestionaireField(state, data) {
		const currentField = state.form.tabs.questionaire_questions.form_fields[data.field]
		currentField && (currentField.selected = data.value)
	},

	prefillTab(state, { tabName, data }) {
		Object.keys(state.form.tabs[tabName].form_fields).forEach(field => {
			if (data[field] !== undefined) {
				state.form.tabs[tabName].form_fields[field].selected = data[field]
			}
		})
	},
	// addRow
	addRow(state, { sectionName, row }) {
		state.form.tabs[sectionName].form_fields.push(row)
	},

	addCreateBlendToBlendList(state, data) {
		state.initialData.blends.push(data)
	},

	setTabStatus(state, data) {
		state.form.tabs[data.tab].status = data.value
	},

	// permissions

	setFlagsPermissions(state, data) {
		// some forms either might not have flags or the flags will be implemented on a latter date
		// the "state.form.tabs.flags &&" verification prvents hard failure for those forms
		state.form.tabs.flags && Object.keys(state.form.tabs.flags.form_fields).forEach(key => {
			if (data.includes(key)) state.form.tabs.flags.form_fields[key].disabled = false
		})
	},

	updateDashboardPermissions(state, permission) {
		state.permissions.dashboard = permission
	},

	updateActionsPermissions(state, permission) {
		state.permissions.actions = permission
	},

	addCountryEntries(state, { tabName, index, countryList }) {
		countryList.forEach(c => {
			state.form.tabs[tabName].form_fields[index][c] = { selected: null, type: 'number' }
		})
	},

	// form state
	updateNewTabs(state, tab) {
		if (tab !== 'sub_info') state.newTabs = Array.from(new Set([...state.newTabs, ...[tab]]))
	},

	tabHasBeenSaved(state, tab) {
		state.newTabs = state.newTabs.filter(currentTab => currentTab !== tab)
	},

	// removal
	resetTab(state, tab) {
		state.form.tabs[tab].form_fields = []
	},
	removeField(state, data) {
		state.form.tabs[data.tab].form_fields.splice(data.index, 1)
	},
	addTabFiles(state, { files }) {
		if (!files) {
			return
		}
		const { form_fields } = state.form.tabs.files
		files.forEach(file => {
			form_fields.files.push(file)
		})
		form_fields.files = sortAscending(form_fields.files, 'updated')
	},
	addTabFile(state, { file }) {
		const { form_fields } = state.form.tabs.files
		form_fields.files = sortAscending([...form_fields.files, file], 'updated')
	},
	updateTabFileDescription(state, { file, description }) {
		if (file.description === description) {
			return
		}
		file.description = description
		file.isDescriptionUpdated = true
		file.upload_successful = false
	},
	updateTabFileWithServerInfo(state, { file, fileServerInfo }) {
		console.log('updateTabFileWithServerInfo', { file, fileServerInfo })
		file.id = fileServerInfo.id
		file.upload_successful = fileServerInfo.upload_successful
		file.file_url = fileServerInfo.file_url
		file.updated = fileServerInfo.updated
		file.tus_id = fileServerInfo.tus_id
	},
	deleteTabFile(state, { file }) {
		const { form_fields } = state.form.tabs.files
		form_fields.files = form_fields.files.filter(fileOld => fileOld !== file)
	},
	deleteAllTabFiles(state) {
		const { form_fields } = state.form.tabs.files
		form_fields.files = []
	}
}

export default mutations
