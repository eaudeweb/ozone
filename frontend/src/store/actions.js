/* eslint-disable no-useless-escape */
import {
  fetch,
  getSubmissionHistory,
  callTransition,
  getSubstances,
  getCustomBlends,
  getSubmissions,
  getSubmission,
  getSubmissionFiles,
  deleteSubmission,
  deleteSubmissionFile,
  getPeriods,
  getObligations,
  createSubmission,
  getParties,
  getNonParties,
  getPartyRatifications,
  getCurrentUser,
  updateCurrentUser,
  uploadFile,
  getSubmissionDefaultValues,
  getSubmissionStates,
  getTransitions,
  getSubmissionFormat,
  getControlledGroups,
  getApprovedExemptionsList,
  getReports,
  getReportingChannel,
  getEmailTemplates,
  getCriticalUseCategoryList
} from '@/components/common/services/api'

import {
  getLevel2PropertyValue,
  escapeHTML
} from '@/components/common/services/utilsService.js'

import { getLabels } from '@/components/art7/dataDefinitions/labels'

import router from '@/router'

const actions = {
  openConfirmModal({ commit }, { title, description, $gettext }) {
    return new Promise(resolve => {
      if (!title) {
        title = $gettext('Please confirm')
      }
      commit('setConfirmModal', {
        title,
        description,
        isVisible: true,
        okCallback: () => {
          commit('resetConfirmModal')
          resolve(true)
        },
        cancelCallback: () => {
          commit('resetConfirmModal')
          resolve(false)
        }
      })
    })
  },
  addSubmission({ state, getters, dispatch }, { submission, $gettext }) {
    return new Promise((resolve, reject) => {
      const duplicatesAll = getters.getDuplicateSubmission(submission)
      const duplicatesByCurrentUser = duplicatesAll && duplicatesAll.length ? duplicatesAll.filter(x => x.filled_by_secretariat === state.currentUser.is_secretariat) : []
      if (duplicatesAll.length >= 2 || duplicatesByCurrentUser.length) {
        dispatch('setAlert', {
          $gettext,
          message: { __all__: [$gettext('Unable to add submission. Another submission for this obligation/year already exists. Please resume work on the existing one.')] },
          variant: 'danger'
        })
        // TODO: should this be a thing ?
        // else if(!isReportingOpen) {
        //     context.dispatch('setAlert', { message: 'Reporting is not open for the selected period', variant: 'danger' })
        // }
      } else {
        createSubmission(submission).then((response) => {
          dispatch('setAlert', {
            $gettext,
            message: { __all__: [$gettext('Submission added successfully.')] },
            variant: 'success'
          })
          dispatch('getCurrentSubmissions').then(() => {
            resolve(response.data)
          })
        }).catch((error) => {
          dispatch('setAlert', {
            $gettext,
            message: { __all__: [$gettext('Unable to add submission.')] },
            variant: 'danger'
          })
          reject(error.response)
        })
      }
    })
  },

  prefillComments(context, data) {
    Object.keys(context.state.form.tabs)
      .filter(tab => context.state.form.tabs[tab].comments)
      .forEach(tab => context.commit('addComment', { data, tab }))
  },

  getCurrentSubmissions(context) {
    return new Promise((resolve) => {
      getSubmissions(context.state.dashboard.table).then(response => {
        context.commit('setDashboardSubmissions', response.data)
        context.dispatch('getMyCurrentSubmissions')
        resolve()
      })
    })
  },

  getUnsavedTabs(context) {
    const tabsWithData = []
    Object.values(context.state.form.tabs).forEach((tab) => {
      [false, 'edited'].includes(tab.status) && tabsWithData.push(tab.title)
    })
    return tabsWithData.length
  },
  // id = id of the component that triggered the save
  async confirmSaveDone(context, id) {
    const unsaved = await context.dispatch('getUnsavedTabs')
    if (!unsaved) {
      context.commit('saveSuccess', id)
    }
  },

  saveCallback(context, { actionToDispatch, data }) {
    context.dispatch(actionToDispatch, data)
  },

  async triggerSave(context, data) {
    if (data) {
      context.commit('setActionToDispatch', data.action)
      context.commit('setDataForAction', data.data)
    }
    document.getElementById('save-button').click()
  },

  async getMyCurrentUser({ commit }) {
    let response
    try {
      response = await getCurrentUser()
      commit('setCurrentUser', response.data)
      // TODO: WHY IS IT AN ARRAY ?
      commit('setCurrentUserPartyInDashboard', response.data[0].party)
      return new Promise((resolve) => {
        resolve(response.data)
      })
    } catch (e) {
      console.log('getMyCurrentUser', e)
    }
  },

  async downloadStuff(context, { url, fileName }) {
    try {
      const downloaded = await fetch(url, { responseType: 'arraybuffer', exposedHeaders: ['Content-Disposition'] })
      const blob = new Blob([downloaded.data])
      const contentDisp = downloaded.request.getResponseHeader('Content-Disposition')

      const regex = /filename[^;=\n]*=(UTF-8(['"]*))?(.*)/
      const matches = regex.exec(contentDisp)

      if (matches != null && matches[3]) {
        fileName = matches[3].replace(/['"]/g, '')
      }
      const link = document.createElement('a')
      if (typeof link.download === 'undefined') {
        /**
         * [ie11 doesn't support download attribute. we use msSaveBlob instead]
         */
        if (navigator.msSaveBlob) {
          return navigator.msSaveBlob(blob, fileName)
        }
      }
      const download_url = window.URL.createObjectURL(blob)
      link.href = download_url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (e) {
      console.log('download error', e)
    }
  },

  async updateCurrentUser({ commit, dispatch }, { user, $gettext }) {
    try {
      await updateCurrentUser(user)
      await dispatch('getMyCurrentUser')
      commit('addAlertData', {
        displayMessage: $gettext('Saved'),
        variant: 'success'
      })
    } catch (e) {
      commit('addAlertData', {
        displayMessage: $gettext('Error'),
        variant: 'danger'
      })
      console.log('updateCurrentUser', e)
    }
  },

  getCurrentUserForm(context) {
    return new Promise((resolve) => {
      getCurrentUser().then(response => {
        context.commit('setCurrentUser', response.data)
        resolve(response.data)
      })
    })
  },

  getMyCurrentSubmissions(context) {
    return new Promise((resolve) => {
      getSubmissions({
        filters: {
          currentState: 'data_entry',
          party: context.state.currentUser.party
        },
        sorting: {
          sortDesc: true,
          sortBy: 'reporting_period'
        },
        perPage: null,
        currentPage: null
      }).then(response => {
        context.commit('setDashboardMySubmissions', response.data)
        resolve()
      })
    })
  },
  async getDashboardParties(context) {
    let response
    try {
      response = await getParties()
    } catch (e) {
      console.log(e)
      return
    }

    const parties_temp = response.data
      .filter(country => country.id === country.parent_party)
      .map(country => ({ value: country.id, text: country.name, iso: country.abbr }))
    context.commit('setDashboardParties', parties_temp)
    return parties_temp
  },

  async getPeriods(context) {
    const periodsDisplay = {}

    const response = await getPeriods()
    response.data.forEach(period => {
      periodsDisplay[period.id] = period.name
    })

    context.commit('setDisplayPeriods', periodsDisplay)
  },

  async getDashboardPeriods(context) {
    const response = await getPeriods()
    let sortedPeriods = response.data
      .filter(a => a.is_reporting_allowed)
      .sort((a, b) => ((parseInt(b.end_date.split('-')[0]) - parseInt(a.end_date.split('-')[0])) === 0
        ? (parseInt(b.start_date.split('-')[0]) - parseInt(a.start_date.split('-')[0]))
        : (parseInt(b.end_date.split('-')[0]) - parseInt(a.end_date.split('-')[0]))))
      .sort((a, b) => b.is_year - a.is_year)
    sortedPeriods = sortedPeriods.map((period) => {
      const start = period.start_date.split('-')[0]
      const end = period.end_date.split('-')[0]
      let periodDisplay = ''
      if (start === end) {
        if (period.name !== start) {
          periodDisplay += `(${start})`
        }
      } else {
        periodDisplay += `(${start} - ${end})`
      }

      return {
        value: period.id, text: `${period.name} ${periodDisplay}`, end_date: period.end_date, start_date: period.start_date, is_reporting_open: period.is_reporting_open, description: period.description
      }
    })

    context.commit('setDashboardPeriods', sortedPeriods)
    return sortedPeriods
  },

  getDashboardObligations(context) {
    getObligations().then(response => {
      const obligations_temp = response.data.sort((a, b) => parseInt(a.sort_order) > parseInt(b.sort_order)).map(obligation => ({ value: obligation.id, text: obligation.name, obligation_type: obligation.obligation_type, is_active: obligation.is_active }))
      context.commit('setDashboardObligations', obligations_temp)
    })
  },

  setAlert(context, data) {
    Object.keys(data.message).forEach(key => {
      let message = data.message[key]
      if (Array.isArray(message)) {
        message = message.map(text => escapeHTML(text)).join('<br>')
      } else if (typeof message === 'string') {
        message = escapeHTML(message)
      }
      const labelValue = getLevel2PropertyValue(getLabels(data.$gettext), key)
      const displayMessage = `${labelValue ? `${labelValue}: ` : ''}${message}`
      context.commit('addAlertData', {
        displayMessage,
        variant: data.variant
      })
    })
  },

  async doSubmissionTransition({ dispatch }, { source, submission, transition, $gettext, noModal, backToDashboard = true }) {
    // console.log('doing transition')
    if (!noModal) {
      const confirmed = await dispatch('openConfirmModal', { $gettext })
      if (!confirmed) {
        return
      }
    }
    callTransition(submission, transition).then(() => {
      if (source === 'dashboard') {
        dispatch('getCurrentSubmissions')
      } else {
        dispatch('getSubmissionData', { submission, $gettext })
      }
      if (process.env.NODE_ENV !== 'development' && backToDashboard) {
        router.push({ path: '/dashboard' })
      }
      dispatch('setAlert', {
        $gettext,
        message: { __all__: [$gettext('Submission status updated successfully.')] },
        variant: 'success'
      })
    }).catch(error => {
      dispatch('setAlert', {
        $gettext,
        message: { __all__: [$gettext('Unable to update submission status.')] },
        variant: 'danger'
      })
      console.log(error)
    })
  },

  async removeField({ dispatch, commit }, { tab, index, $gettext, noAlert }) {
    if (!noAlert) {
      const confirmed = await dispatch('openConfirmModal', { title: 'Please confirm', description: 'Are you sure you want to delete the selected row?', $gettext })
      if (!confirmed) {
        return confirmed
      }
    }
    commit('removeField', { tab, index })
  },

  async removeBulkFields({ dispatch, commit }, { tab, indexList, $gettext }) {
    const confirmed = await dispatch('openConfirmModal', { title: 'Please confirm', description: 'Are you sure you want to delete the selected rows?', $gettext })
    if (!confirmed) {
      return confirmed
    }
    commit('removeBulkFields', { tab, indexList })
  },

  async removeSubmission({ dispatch }, { submissionUrl, $gettext }) {
    const confirmed = await dispatch('openConfirmModal', { title: 'Please confirm', description: 'Are you sure you want to delete the submission? All data will be deleted irreversibly.', $gettext })
    if (!confirmed) {
      return confirmed
    }
    deleteSubmission(submissionUrl).then(() => {
      dispatch('getCurrentSubmissions')
      dispatch('setAlert', {
        $gettext,
        message: { __all__: [$gettext('Submission deleted successfully.')] },
        variant: 'success'
      })
    }).catch(() => {
      dispatch('getCurrentSubmissions')
      dispatch('setAlert', {
        $gettext,
        message: { __all__: [$gettext('Unable to delete submission.')] },
        variant: 'danger'
      })
    })
    return confirmed
  },

  // CHECK THIS IF formName CHANGES. It's hardcoded for optimization purpose
  async getInitialData(context, { submission, formName, $gettext, additionalAction }) {
    context.commit('setForm', { formName, $gettext })
    console.log('----------------', formName)
    await context.dispatch('getSubmissionData', { submission, $gettext }).then(async (reporting_period) => {
      context.dispatch('getCurrentUserForm').then(currentUser => {
        if (formName === 'art7'
          && ((Array.isArray(currentUser) && currentUser[0].is_secretariat)
          || (!Array.isArray(currentUser) && currentUser && currentUser.is_secretariat))
        ) {
          context.dispatch('getEmailTemplates')
        }
      })
      await context.dispatch('getCountries')
      await context.dispatch('getSubstances')
      await context.dispatch('getSubmissionDefaultValues')
      await context.dispatch('getReportingChannel')
      // Filter custom blends by the submission's party, because the API will
      // by default show all custom blends for secretariat users.
      // This way, even secretariat users will only see the correct available
      // custom blends.
      await context.dispatch('getCustomBlends', { party: context.state.current_submission.party })
      await context.dispatch('getSubmissionFormatOptions')
      if (formName === 'art7') {
        await context.dispatch('getControlledGroups', { party: context.state.current_submission.party, period: reporting_period })
        await context.dispatch('getNonParties', reporting_period)
      }
      if (formName === 'essencrit' || formName === 'exemption') {
        await context.dispatch('getApprovedExemptionsList', { partyId: context.state.current_submission.party, period: reporting_period })
        await context.dispatch('getCriticalUseCategoryList')
      }
      if (formName === 'transfer') {
        await context.dispatch('getPeriods')
      }
      if (additionalAction) {
        await context.dispatch(additionalAction)
      }
    })
  },
  // party id, period name
  async getControlledGroups(context, { party, period }) {
    const controlledGroups = await getControlledGroups(party, period)
    context.commit('setControlledGroups', controlledGroups.data)
  },

  async getCriticalUseCategoryList(context) {
    const list = await getCriticalUseCategoryList()
    context.commit('setCriticalUseCategoryList', {
      data: list.data.map(cat => ({ text: cat.name, value: cat.id, code: cat.code })),
      display: list.data.reduce((result, item) => {
        result[item.id] = item.name
        return result
      }, {})
    })
  },

  async getEmailTemplates(context) {
    const templates = await getEmailTemplates()
    context.commit('setEmailTemplates', templates.data)
  },

  async getApprovedExemptionsList(context, { partyId, period }) {
    const exemptionsList = await getApprovedExemptionsList(partyId, period)
    context.commit('setApprovedExemptionsList', exemptionsList.data)
  },

  async getSubmissionFormatOptions(context) {
    const submissionFormatOptions = await getSubmissionFormat()
    context.commit('setSubmissionFormatOptions', submissionFormatOptions.data.map(s => ({ text: s.name, value: s.name })))
  },

  getSubmissionData(context, { submission, $gettext }) {
    return new Promise((resolve) => {
      getSubmission(submission).then(async (response) => {
        await context.commit('updateSubmissionData', response.data)
        await context.commit('setFlagsPermissions', response.data.changeable_flags)
        await context.dispatch('getCurrentSubmissionHistory', { submission, $gettext })
        await context.commit('setFormPermissions', {
          can_change_remarks_party: response.data.can_change_remarks_party,
          can_change_remarks_secretariat: response.data.can_change_remarks_secretariat,
          can_change_reporting_channel: response.data.can_change_reporting_channel,
          can_upload_files: response.data.can_upload_files,
          can_edit_data: response.data.can_edit_data
        })
        resolve(response.data.reporting_period)
      })
    })
  },

  getCurrentSubmissionHistory(context, { submission, $gettext }) {
    getSubmissionHistory(submission).then((response) => {
      context.commit('setSubmissionHistory', response.data)
    }).catch((error) => {
      context.dispatch('setAlert', {
        $gettext,
        message: { ...error.response.data },
        variant: 'danger'
      })
    })
  },

  getPartyRatifications(context) {
    getPartyRatifications().then(response => {
      context.commit('updatePartyRatifications', response.data)
    })
  },

  async getReportsList() {
    const reports = await getReports()
    return reports.data.map(r => ({ value: r.name, text: r.display_name, original: r }))
  },

  getReportingChannel(context) {
    getReportingChannel().then(response => {
      const reportingChannel = response.data.map(channel => ({ text: channel.name, value: channel.name, is_secretariat: channel.is_secretariat, is_party: channel.is_party }))
      context.commit('updateReportingChannel', reportingChannel)
    })
  },

  getCountries(context) {
    const countryDisplay = {}
    getParties().then(response => {
      const countryOptions = response.data.map((country) => {
        countryDisplay[country.id] = country.name
        countryDisplay['other'] = 'other'
        return { value: country.id, text: country.name, iso: country.abbr }
      }).filter((p) => p.value !== context.state.current_submission.party)
      const countryOptionsSubInfo = response.data.map((country) => ({ value: country.id, text: country.name, iso: country.abbr }))
      context.commit('updateCountries', countryOptions)
      context.commit('updateCountriesDisplay', countryDisplay)
      context.commit('updateCountriesSubInfo', countryOptionsSubInfo)
    })
  },

  async getSubstances(context) {
    const tempSubstances = []
    const substancesDisplay = {}
    const response = await getSubstances()
    response.data.forEach(group => {
      group.substances.sort((a, b) => a.sort_order - b.sort_order)
      group.substances.forEach(substance => {
        tempSubstances.push({
          value: substance.id,
          text: substance.name,
          group,
          is_qps: substance.is_qps,
          is_contained_in_polyols: substance.is_contained_in_polyols,
          is_captured: substance.is_captured,
          has_critical_uses: substance.has_critical_uses
        })
        substancesDisplay[substance.id] = substance.name
      })
    })

    await context.commit('updateGroupSubstances', response.data)
    await context.commit('updateSubstances', tempSubstances)
    await context.commit('updateSubstancesDisplay', substancesDisplay)
  },

  getCustomBlends(context, { party }) {
    const blendsDisplay = {}
    getCustomBlends(party).then((response) => {
      response.data.forEach(blend => {
        blend.components.sort((component1, component2) => component2.percentage - component1.percentage)
        blendsDisplay[blend.id] = { name: blend.blend_id, components: blend.components, is_qps: blend.is_qps }
      })
      context.commit('updateBlends', response.data)
      context.commit('updateBlendsDisplay', blendsDisplay)
    })
  },

  getNonParties(context, reporting_period) {
    getNonParties(reporting_period).then((response) => {
      context.commit('updateNonParties', response.data)
    })
  },

  createSubstance(context, data) {
    return new Promise((resolve) => {
      const substancesHere = data.substanceList && data.substanceList.some((el) => el !== null)
      const blendsHere = data.blendList && data.blendList.some((el) => el !== null)
      if (substancesHere) {
        data.substanceList.forEach(substance => {
          // let ordering_id = 0
          // if (!data.prefillData) {
          //   context.commit('incrementOrderingId', { tabName: data.currentSectionName });
          //   ({ ordering_id } = context.state.form.tabs[data.currentSectionName])
          // }
          // section, substance, group, country, blend, prefillData, ordering_id
          const inner_fields = context.state.tableRowConstructor.substanceRows({
            $gettext: data.$gettext,
            section: data.currentSectionName,
            substance,
            group: data.groupName,
            country: data.country,
            blend: null,
            prefillData: data.prefillData,
            // ordering_id,
            countries: context.state.initialData.display.countries,
            critical: data.critical || null,
            exemptionValue: data.exemptionValue,
            critical_use_categories: context.state.initialData.display.criticalUseCategoryList,
            has_critical_uses: context.getters.getCriticalSubstances(substance, data.substanceList)
          })
          context.commit('addRow', { sectionName: data.currentSectionName, row: inner_fields })
        })
      } else if (blendsHere) {
        data.blendList.forEach(blend => {
          // let ordering_id = 0
          // if (!data.prefillData) {
          //   context.commit('incrementOrderingId', { tabName: data.currentSectionName });
          //   ({ ordering_id } = context.state.form.tabs[data.currentSectionName].ordering_id)
          // }
          const inner_fields = context.state.tableRowConstructor.substanceRows({
            $gettext: data.$gettext,
            section: data.currentSectionName,
            substance: null,
            group: data.groupName,
            country: data.country,
            blend,
            prefillData: data.prefillData
            // ordering_id
          })
          context.commit('addRow', { sectionName: data.currentSectionName, row: inner_fields })
        })
      }
      resolve()
    })
  },

  createRow(context, { currentSectionName, prefillData, $gettext }) {
    return new Promise((resolve) => {
      let ordering_id = 0
      if (!prefillData) {
        context.commit('incrementOrderingId', { tabName: currentSectionName });
        ({ ordering_id } = context.state.form.tabs[currentSectionName])
      }

      const row = context.state.tableRowConstructor.nonSubstanceRows({
        $gettext,
        currentSectionName,
        prefillData,
        ordering_id
      })
      context.commit('addRow', { sectionName: currentSectionName, row })
      resolve()
    })
  },

  clearEdited({ state, commit }) {
    Object.keys(state.form.tabs).filter(tab => state.form.tabs[tab].status === 'edited').forEach((tab) => {
      commit('setTabStatus', { tab, value: null })
    })
  },

  removeDataFromTab(context, data) {
    return new Promise((resolve) => {
      context.commit('resetTab', data)
      resolve()
    })
  },
  async uploadFiles(context, { files, onProgressCallback }) {
    for (let i = 0; i < files.length; i += 1) {
      const file = files[i]
      const response = await uploadFile(file, context.state.current_submission.id, onProgressCallback)
      file.tus_url = response.url
      file.percentage = 100
    }
  },

  async getNewTransitions({ state, commit }) {
    const transitions = await getTransitions(state.current_submission.available_transitions_url)
    console.log(transitions)
    commit('updateTransitions', transitions.data[0].available_transitions)
  },

  async getSubmissionFiles(context) {
    const response = await getSubmissionFiles(context.state.current_submission.id)
    return response.data
  },
  async deleteTabFile({ state, commit }, { file }) {
    console.log(file)
    if (file.tus_id) {
      await deleteSubmissionFile({ file, submissionId: state.current_submission.id })
    }

    commit('deleteTabFile', { file })
  },
  updateLocalFilesFromServerFilesResponse({ state, commit }, { filesOnServer }) {
    const { form_fields } = state.form.tabs.files
    const filesLocal = form_fields.files
    filesOnServer.forEach(fileServerInfo => {
      const fileJustUploaded = filesLocal.find(x => {
        if (x.tus_id) {
          return x.tus_id === fileServerInfo.tus_id
        }
        return x.tus_url && x.tus_url.endsWith(fileServerInfo.tus_id)
      })
      console.log(fileJustUploaded)
      if (fileJustUploaded) {
        commit('updateTabFileWithServerInfo', {
          file: fileJustUploaded,
          fileServerInfo
        })
      }
    })
  },
  async setJustUploadedFilesState({ dispatch }) {
    const filesOnServer = await dispatch('getSubmissionFiles')
    await dispatch('updateLocalFilesFromServerFilesResponse', {	filesOnServer })
  },
  async getSubmissionDefaultValues({ commit }) {
    const response = await getSubmissionDefaultValues()
    commit('setSubmissionDefaultValues', response.data)
    return response.data || {}
  },
  async fetchSubmissionStates({ commit }) {
    const response = await getSubmissionStates()
    commit('setSubmissionStates', response.data)
    return response.data || {}
  }
}

export default actions
