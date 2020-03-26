import 'toastedjs/src/sass/toast.scss'
import Toasted from 'toastedjs/dist/toasted.min.js'

import { sortAscending } from '@/components/common/services/utilsService'
import { dateFormatToSeconds } from '@/components/common/services/languageService'

import { getFormArt7 } from '@/components/art7/dataDefinitions/form'
import art7TableRowConstructor from '@/components/art7/services/tableRowConstructorService'
import { getFormLetter } from '@/components/letter/dataDefinitions/form'
import { getFormHat } from '@/components/hat/dataDefinitions/form'
import hatTableRowConstructor from '@/components/hat/services/tableRowConstructorService'
import { getFormRaf } from '@/components/raf/dataDefinitions/form'
import rafTableRowConstructor from '@/components/raf/services/tableRowConstructorService'
import { getFormExemption } from '@/components/exemption/dataDefinitions/form'
import exemptionTableRowConstructor from '@/components/exemption/services/tableRowConstructorService'
import { getFormOtherRo } from '@/components/otherRo/dataDefinitions/form'
import otherRoTableRowConstructor from '@/components/otherRo/services/tableRowConstructorService'

const options = {
  position: 'bottom-left',
  duration: 10000,
  theme: 'bulma'
}
const toasted = new Toasted(options)

const mutations = {
  setConfirmModal(state, value) {
    state.confirmModal = value
  },
  resetConfirmModal(state) {
    state.confirmModal = {
      isVisible: false,
      title: null,
      description: null,
      okCallback: () => {},
      cancelCallback: () => {}
    }
  },
  updateBreadcrumbs(state, data) {
    state.route = data
  },

  addComment(state, { data, tab, field }) {
    // If there is no field specified, it means that the data comes from server for prefill
    const { comments } = state.form.tabs[tab]
    if (!field) {
      const [commentsData] = data
      Object.keys(comments).forEach(comment => {
        comments[comment].selected = commentsData[comment]
      })
    } else {
      comments[field].selected = data
    }
  },

  updateFormField(state, data) {
    const tab = state.form.tabs[data.fieldInfo.tabName]
    const formField = tab.form_fields[data.fieldInfo.index]

    if (data.fieldInfo.party) {
      formField.imports.find(i => i.party === data.fieldInfo.party).quantity = data.value
      return
    }
    if (data.fieldInfo.category) {
      if (formField.use_categories) {
        formField.use_categories.find(i => i.critical_use_category === data.fieldInfo.category).quantity = data.value
      }
      if (formField.approved_uses) {
        formField.approved_uses.find(i => i.critical_use_category === data.fieldInfo.category).quantity = data.value
      }
      formField.quantity_use_categories = null
      return
    }
    if (data.fieldInfo.index === data.fieldInfo.field) {
      formField.selected = data.value
    } else {
      formField[data.fieldInfo.field].selected = data.value
    }
  },

  removeFormField(state, { index, tabName, fieldName, fieldIndex }) {
    state.form.tabs[tabName].form_fields[index][fieldName].splice(fieldIndex, 1)
    if (state.form.tabs[tabName].form_fields[index].quantity_use_categories) {
      state.form.tabs[tabName].form_fields[index].quantity_use_categories = null
    }
  },

  setSubmissionHistory(state, data) {
    state.currentSubmissionHistory = data
  },

  resetStuff(state) {
    state.form = null
    state.initialData = {
      countryOptions: null,
      countryOptionsSubInfo: null,
      groupSubstances: null,
      substances: null,
      partyRatifications: null,
      essenCritTypes: null,
      submissionFormats: null,
      blends: null,
      nonParties: null,
      display: {
        substances: null,
        blends: null,
        countries: null
      }
    }
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
    case 'transfer':
      currentFormStructure = getFormOtherRo($gettext, formName)
      tableRowConstructor = otherRoTableRowConstructor
      break
    case 'procagent':
      currentFormStructure = getFormOtherRo($gettext, formName)
      tableRowConstructor = otherRoTableRowConstructor
      break
    case 'essencrit':
      currentFormStructure = getFormRaf($gettext)
      tableRowConstructor = rafTableRowConstructor
      break

    default:
      break
    }
    console.log(formName, '---------')
    // if anything breaks really bad, revert to state.form = JSON.parse(JSON.stringify(currentFormStructure))
    state.form = currentFormStructure
    state.tableRowConstructor = tableRowConstructor
  },

  setDataForAction(state, data) {
    state.dataForAction = data
  },

  setActionToDispatch(state, data) {
    state.actionToDispatch = data
  },

  updateTransitions(state, data) {
    state.current_submission.available_transitions = data
  },

  setEmailTemplates(state, data) {
    state.emailTemplates = data
  },

  setCriticalUseCategoryList(state, { data, display }) {
    state.initialData.criticalUseCategoryList = data
    state.initialData.display.criticalUseCategoryList = display
  },

  setEssenCritTypes(state, data) {
    state.initialData.essenCritTypes = data
  },

  setApprovedExemptionsList(state, data) {
    state.initialData.approvedExemptionsList = data
  },

  setExemptionBasedOnEmergency(state, { emergency, index }) {
    let emergency_mapping = 'emergency'
    if (emergency === false) {
      emergency_mapping = 'non_emergency'
    }
    if (state.form.tabs.essencrit.form_fields[index].quantity_exempted.exemptionValue[emergency_mapping]) {
      state.form.tabs.essencrit.form_fields[index].quantity_exempted.selected = state.form.tabs.essencrit.form_fields[index].quantity_exempted.exemptionValue[emergency_mapping]
    }
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

  setSubmissionFormatOptions(state, data) {
    state.initialData.submissionFormats = data
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

  resetDashboardFilters(state) {
    state.dashboard.table = {
      currentPage: 1,
      perPage: 10,
      totalRows: 0,
      sorting: {
        sortBy: null,
        sortDesc: null,
        sortDirection: 'desc'
      },
      filters: {
        search: null,
        period_start: null,
        is_superseded: null,
        period_end: null,
        obligation: null,
        party: null,
        isCurrent: null
      }
    }
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

  setSubmissionDefaultValues(state, data) {
    state.submissionDefaultValues = data
  },
  // initial data

  setSubmissionStates(state, data) {
    state.submissionStates = data
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

  updateCountriesSubInfo(state, data) {
    state.initialData.countryOptionsSubInfo = data
  },

  updateCountriesDisplay(state, data) {
    state.initialData.display.countries = data
  },

  setDisplayPeriods(state, data) {
    state.initialData.display.periods = data
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
    state.initialData.blends = data || []
  },

  updateBlendsDisplay(state, data) {
    state.initialData.display.blends = data
  },

  updateReportingChannel(state, data) {
    state.initialData.reportingChannel = []
    data.forEach(channel => {
      if ((state.currentUser.is_secretariat && channel.is_secretariat)
      || (state.currentUser.is_party && channel.is_party)
      || !state.current_submission.can_change_reporting_channel) {
        state.initialData.reportingChannel.push(channel)
      }
    })
  },

  updateEditMode(state, data) {
    state.permissions.form.edit_mode = data
  },

  setBlendComponentRowVariant(state, data) {
    data.component._rowVariant = data.value
  },

  setControlledGroups(state, data) {
    state.initialData.controlledGroups = data
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
      else state.form.tabs.flags.form_fields[key].disabled = true
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
      state.form.tabs[tabName].form_fields[index].imports.push({
        party: c, quantity: null
      })
    })
  },

  setPreventLeaveConfirm(state, data) {
    state.preventLeaveConfirm = data
  },

  // pushes the id of the component that did the save into an state.saveSuccess
  //  in order to watch for the state.saveSucess.indexOf(component._uid) somwhere else
  saveSuccess(state, id) {
    if (state.saveSuccess.indexOf(id) === -1) {
      state.saveSuccess.push(id)
    }
  },

  removeSaveSuccess(state, id) {
    state.saveSuccess.splice(state.saveSuccess.indexOf(id), 1)
  },

  addCategoryEntry(state, { tabName, index, categoryList }) {
    categoryList.forEach(c => {
      if (tabName === 'approved') {
        if (state.form.tabs[tabName].form_fields[index].approved_uses.filter(approved => approved.critical_use_category === c).length === 0) {
          state.form.tabs[tabName].form_fields[index].approved_uses.push({
            critical_use_category: c, quantity: null
          })
        }
      } else {
        state.form.tabs[tabName].form_fields[index].use_categories.push({
          critical_use_category: c, quantity: null
        })
      }
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
  removeField(state, { tab, index }) {
    state.form.tabs[tab].form_fields.splice(index, 1)
  },

  removeBulkFields(state, { tab, indexList }) {
    state.form.tabs[tab].form_fields = state.form.tabs[tab].form_fields.filter(field => !indexList.includes(state.form.tabs[tab].form_fields.indexOf(field)))
  },

  addTabFiles(state, { files }) {
    if (!files) {
      return
    }
    const { form_fields } = state.form.tabs.files
    files.forEach(file => {
      file.updated = dateFormatToSeconds(file.updated, state.currentUser.language)
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
    file.id = fileServerInfo.id
    file.upload_successful = fileServerInfo.upload_successful
    file.file_url = fileServerInfo.file_url
    file.updated = dateFormatToSeconds(fileServerInfo.updated, state.currentUser.language)
    file.tus_id = fileServerInfo.tus_id
  },
  updateFilePercentage(state, { file, percentage }) {
    const { form_fields } = state.form.tabs.files
    file.percentage = percentage
    form_fields.files = [...form_fields.files]
  },
  deleteTabFile(state, { file }) {
    const { form_fields } = state.form.tabs.files
    form_fields.files = form_fields.files.filter(fileOld => fileOld !== file)
  },
  deleteAllTabFiles(state) {
    const { form_fields } = state.form.tabs.files
    form_fields.files = []
  },
  updateFilesUploadInProgress(state, data) {
    state.filesUploadInProgress = data
  }
}

export default mutations
