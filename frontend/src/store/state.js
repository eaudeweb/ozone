const state = {
  currentUser: null,
  actionToDispatch: null,
  submissionDefaultValues: null,
  preventLeaveConfirm: false,
  dataForAction: null,
  emailTemplates: null,
  saveSuccess: [],
  dashboard: {
    mySubmissions: null,
    submissions: null,
    periods: null,
    obligations: null,
    parties: null,
    table: {
      currentPage: 1,
      perPage: 10,
      totalRows: 0,
      sorting: {
        sortBy: null,
        sortDesc: true,
        sortDirection: 'desc'
      },
      filters: {
        search: null,
        currentState: null,
        period_start: null,
        is_superseded: null,
        period_end: null,
        obligation: null,
        party: null,
        isCurrent: null
      }
    }
  },
  currentAlert: {
    message: null,
    show: false,
    variant: null
  },
  confirmModal: {
    isVisible: false,
    title: null,
    description: null,
    okCallback: () => {},
    cancelCallback: () => {}
  },
  current_submission: null,
  route: '',
  currentSubmissionHistory: null,
  permissions: {
    dashboard: null,
    form: null,
    actions: null
  },
  tableRowConstructor: null,
  newTabs: [],
  form: null,
  initialData: {
    countryOptions: null,
    countryOptionsSubInfo: null,
    groupSubstances: null,
    reportingChannel: null,
    criticalUseCategoryList: null,
    substances: null,
    controlledGroups: null,
    approvedExemptionsList: null,
    partyRatifications: null,
    essenCritTypes: null,
    submissionFormats: null,
    blends: null,
    nonParties: null,
    display: {
      substances: null,
      blends: null,
      countries: null,
      periods: null,
      criticalUseCategoryList: null
    }
  },
  alertData: [],
  recordDataObligations: ['art9', 'transfer']
}

export default state
