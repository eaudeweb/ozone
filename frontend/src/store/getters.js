import { Decimal } from 'decimal.js'
import { doSum, valueConverter } from '@/components/common/services/utilsService'

const sumBiggerThanParts = (state, tab, partyField) => {
  if (!state.form.tabs[tab].form_fields.length) return {}
  if (!state.form.tabs[tab].form_fields[0].hasOwnProperty(partyField)) return {}
  const multipleSubstances = {}
  const finalError = {}

  state.form.tabs[tab].form_fields.forEach(row => {
    multipleSubstances[row.substance.selected] = [...state.form.tabs[tab].form_fields.filter(substance => row.substance.selected === substance.substance.selected)]
  })

  Object.keys(multipleSubstances).forEach(key => {
    if (multipleSubstances[key].length <= 1) {
      delete multipleSubstances[key]
    }
    if (multipleSubstances[key] && multipleSubstances[key].length && multipleSubstances[key].every(entry => entry[partyField].selected)) {
      // eslint-disable-next-line eqeqeq
      state.form.tabs[tab].form_fields.filter(field => field.substance.selected == key).forEach(field => {
        field.skipValidation = 0
      })
      delete multipleSubstances[key]
    }
  })
  if (Object.keys(multipleSubstances).length < 1) {
    return {}
  }
  Object.keys(multipleSubstances).forEach(key => {
    finalError[key] = {
      left: 0,
      right: 0
    }

    multipleSubstances[key].forEach(entry => {
      finalError[key].left = Decimal.add(valueConverter(entry.quantity_total_new.selected), finalError[key].left).toNumber()
      finalError[key].right = Decimal.add(doSum([entry.quantity_feedstock.selected, entry.quantity_exempted.selected, entry.quantity_quarantine_pre_shipment.selected]), finalError[key].right).toNumber()
    })
  })
  Object.keys(finalError).forEach(key => {
    // This might be confuzing. We're using a trilean heare. 0 is base state, 1 is valid for multirow validation, 2 is invalid for multirow validation
    let multiValidationState = 1
    console.log('finalerror', finalError[key].left, finalError[key].right)
    if (finalError[key].left >= finalError[key].right) {
      multiValidationState = 1
      delete finalError[key]
    } else {
      multiValidationState = 2
    }

    // eslint-disable-next-line eqeqeq
    state.form.tabs[tab].form_fields.filter(field => field.substance.selected == key).forEach(field => {
      if (field[partyField].selected) {
        field.skipValidation = 0
      } else {
        field.skipValidation = multiValidationState
      }
    })
  })
  return finalError
}

const getters = {
  // TODO: if there are errors caused by validation, check this first. There was a invalid, edited check for tab before getting validations
  getValidationForCurrentTab: (state) => (tab) => state.form.tabs[tab].form_fields
    .map(field => (field.validation.selected
      ? {
        validation: field.validation.selected,
        substance: field.substance ? field.substance.selected : null,
        source_party: field.source_party ? field.source_party.selected : null,
        destination_party: field.destination_party ? field.destination_party.selected : null,
        trade_party: field.trade_party ? field.trade_party.selected : null,
        blend: field.blend ? field.blend.selected : null,
        facility_name: field.facility_name ? field.facility_name.selected : null
      }
      : null)),

  multiRowValidation: (state) => (tab) => {
    switch (tab) {
    case 'has_imports':
      return sumBiggerThanParts(state, tab, 'source_party')
    case 'has_exports':
      return sumBiggerThanParts(state, tab, 'destination_party')
    default:
      return {}
    }
  },

  getCapturedSubstance: (state) => (substance) => state.initialData.substances.some(s => s.value === substance && s.is_captured),

  getCriticalSubstances: (state) => (substance) => state.initialData.substances.some(s => s.value === substance && s.has_critical_uses),

  getDuplicateSubmission: (state) => (data) => state.dashboard.mySubmissions && state.dashboard.mySubmissions.filter(
    (sub) => sub.obligation === data.obligation
			&& sub.party === data.party
			&& sub.reporting_period === data.reporting_period
			&& sub.current_state === 'data_entry'
  ),

  defaultPeriod: (state) => (submissionDefaultValues) => state.dashboard.periods && state.dashboard.periods.find(period => period.text.trim() === submissionDefaultValues.reporting_period),
  defaultObligation: (state) => (submissionDefaultValues) => state.dashboard.obligations && state.dashboard.obligations.find(o => o.text === submissionDefaultValues.obligation).value,

  getTabTitle: (state) => (tabName) => state.form.tabs[tabName].title,
  getTabStatus: (state) => (tabName) => state.form.tabs[tabName].status,
  pageTitle: (state) => state.route,
  // eslint-disable-next-line
  edit_mode: (state, getters) => state.permissions.form && state.permissions.form.edit_mode,
  /**
   * this getter needs state.initialData.countryOptions or state.dashboard.parties
   * TODO: maybe change this ?
   */
  currentCountryIso: (state) => {
    const { currentUser } = state
    let currentCountry = null
    if (!currentUser || !currentUser.party) return
    if (state.initialData.countryOptionsSubInfo) {
      currentCountry = state.initialData.countryOptionsSubInfo.find(c => currentUser.party === c.value)
    }
    if (state.dashboard.parties && state.dashboard.parties.length) {
      currentCountry = state.dashboard.parties.find(c => currentUser.party === c.value)
    }
    if (!currentCountry) return
    return currentCountry && currentCountry.iso.toLowerCase()
  },

  getSubmissionInfo: (state) => (submission) => {
    const submissionInfo = {
      obligation: () => state.dashboard.obligations.find(a => a.value === submission.obligation).text,
      period: () => {
        // TODO: find a better way to do this
        const period = state.dashboard.periods.find(a => a.value === submission.reporting_period)
        if (period && period.hasOwnProperty('text')) {
          return period.text
        }
      },
      period_description: () => {
        // TODO: find a better way to do this
        const period = state.dashboard.periods.find(a => a.value === submission.reporting_period)
        if (period && period.hasOwnProperty('text')) {
          return period.description
        }
      },
      party: () => state.dashboard.parties.find(a => a.value === submission.party).text,
      period_start: () => state.dashboard.periods.find(a => a.value === submission.reporting_period).start_date.split('-')[0],
      period_end: () => state.dashboard.periods.find(a => a.value === submission.reporting_period).end_date.split('-')[0]
    }
    return submissionInfo
  },

  getPeriodStatus: (state) => (periodId) => state.dashboard.periods.find((period) => period.value === periodId).is_reporting_open,

  checkIfBlendAlreadyEists: (state) => (blendName) => state.initialData.blends.find((blend) => blend.blend_id === blendName),

  getFilesUploadInProgress: (state) => state.filesUploadInProgress

}

export default getters
