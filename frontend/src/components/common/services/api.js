import axios from 'axios'
import tus from 'tus-js-client'
// eslint-disable-next-line no-unused-vars
import { sortDescending } from '@/components/common/services/utilsService'

const logRequests = process.env.NODE_ENV === 'development'

let apiURL = `${window.location.origin}/api`
let apiBase = `${window.location.origin}`
let filesURL = `${window.location.protocol}//${process.env.VUE_APP_TUSD_HOST}:${process.env.VUE_APP_TUSD_PORT}${process.env.VUE_APP_TUSD_PATH}/files/`

if (process.env.VUE_APP_API_HOST) {
  apiURL = `${window.location.protocol}//${process.env.VUE_APP_API_HOST}/api`
  apiBase = `${window.location.protocol}//${process.env.VUE_APP_API_HOST}`
}

let isTestSession = false
if (process.env.NODE_ENV === 'development') {
  isTestSession = true
  apiURL = 'http://localhost:8000/api'
  apiBase = 'http://localhost:8000'
  filesURL = 'http://localhost:1080/files/'
}

const api = axios.create({
  baseURL: apiURL,
  withCredentials: true
})

const apiPublicDirectory = axios.create()

api.defaults.xsrfHeaderName = 'X-CSRFTOKEN'
api.defaults.xsrfCookieName = 'csrftoken'

const getCookie = (name) => {
  const cookie = {}
  document.cookie.split(';').forEach((el) => {
    const [k, v] = el.split('=')
    cookie[k.trim()] = v
  })
  return cookie[name]
}

const checkAuth = () => {
  if (!api.defaults.headers.authorization && getCookie('authToken')) {
    api.defaults.headers.authorization = `token ${getCookie('authToken')}`
  }
}

const fetch = (path, config = null) => {
  logRequests && console.log(`fetching ${path}...`)
  checkAuth()
  return api.get(path, config)
}

const fetchFromPublicDirectory = (path) => {
  logRequests && console.log(`fetching ${path}...`)
  return apiPublicDirectory.get(path)
}

const post = (path, data) => {
  logRequests && console.log(`posting ${path} with data ${data}...`)
  checkAuth()
  return api.post(path, data)
}

const update = (path, data) => {
  logRequests && console.log(`patching ${path} with data ${data}...`)
  checkAuth()
  return api.put(path, data)
}

const remove = (path) => {
  logRequests && console.log(`removig ${path} ...`)
  checkAuth()
  return api.delete(path)
}

const getSubstances = () => fetch('group-substances/')

/**
 * filter out 'uncontrolled'
 */
const getFilteredSubstances = () => new Promise(async (resolve, reject) => {
  try {
    const responseSubstances = await fetch('group-substances/')
    const result = { data: responseSubstances.data.filter(country => country.group_id !== 'uncontrolled') }
    resolve(result)
  } catch (error) { //  here goes if someAsyncPromise() rejected}
    reject(error) //  this will result in a resolved promise.
  }
})

const getUsers = () => fetch('users/')

const getCurrentUser = () => fetch('current-user/')

const updateCurrentUser = (user) => update(`current-user/${user.id}/`, user)

const getParties = () => fetch('parties/')

/**
 * will return the filtered list of parties that doesn't include islands
 */
const getFilteredParties = () => new Promise(async (resolve, reject) => {
  try {
    const responseParties = await fetch('parties/')
    const result = { data: responseParties.data.filter(country => country.id === country.parent_party) }
    resolve(result)
  } catch (error) { //  here goes if someAsyncPromise() rejected}
    reject(error) //  this will result in a resolved promise.
  }
})

const getTransitions = (url) => fetch(url)

const getPartyRatifications = () => fetch('get-party-ratifications/')

const getExportBlends = () => {
  if (isTestSession) {
    console.log('getting blends')
    return axios.get(`${window.location.origin}/blends.json`)
  }
  return null
}

const getSubmissionFormat = () => fetch('get-submission-formats/')

const getPeriods = () => fetch('periods/')

/**
 * sort reporting periods in descending order
 */
const getFilteredPeriods = () => new Promise(async (resolve, reject) => {
  try {
    const responsePeriods = await fetch('periods/')
    const sortedPeriods = responsePeriods.data
      .filter(a => a.is_reporting_allowed)
      .sort((a, b) => ((parseInt(b.end_date.split('-')[0]) - parseInt(a.end_date.split('-')[0])) === 0
        ? (parseInt(b.start_date.split('-')[0]) - parseInt(a.start_date.split('-')[0]))
        : (parseInt(b.end_date.split('-')[0]) - parseInt(a.end_date.split('-')[0]))))
      .sort((a, b) => b.is_year - a.is_year)
    const result = { data: sortedPeriods }
    resolve(result)
  } catch (error) { //  here goes if someAsyncPromise() rejected}
    reject(error) //  this will result in a resolved promise.
  }
})

const getObligations = () => fetch('obligations/')

const createSubmission = (submisson_data) => {
  console.log(api.defaults)
  return post('submissions/', submisson_data)
}

const createBlend = (blend) => post('blends/', blend)

const cloneSubmission = (url) => post(`${url}clone/`)

const getCustomBlends = (party) => fetch('blends/', {
  params: {
    party
  }
})

const getInstructions = (formName, tabName) => {
  if (isTestSession) {
    return fetch(`${window.location.origin}/instructions/${formName}/${tabName}.html`)
  }
  return fetch(`${window.location.origin}/instructions/${formName}/${tabName}.html`)
}

const getSubmissions = (tableOptions) => {
  const params = {
    page_size: tableOptions.perPage,
    page: tableOptions.currentPage
  }
  if (tableOptions.filters) {
    params.current_state = tableOptions.filters.currentState
    params.search = tableOptions.filters.search
    params.party = tableOptions.filters.party
    params.obligation = tableOptions.filters.obligation
    params.from_period = tableOptions.filters.period_start
    params.to_period = tableOptions.filters.period_end
    if (tableOptions.filters.is_superseded !== true) {
      params.is_superseded = false
    }
  }
  if (tableOptions.sorting && tableOptions.sorting.sortBy) {
    params.ordering = (tableOptions.sorting.sortDesc ? '-' : '') + tableOptions.sorting.sortBy
  }

  return fetch('submissions/', {
    params
  })
}

const getSubmissionHistory = (url) => fetch(`${url}versions/`)

const getSubmissionsVersions = () => fetch('submission-versions/')

const getSubmission = (url) => fetch(url)

const getSubmissionAggregations = (url) => fetch(`${url}aggregations/`)

const getSubmissionFiles = (submissionId) => fetch(`submissions/${submissionId}/files/`, {
  hideLoader: true
})

const deleteSubmission = (url) => remove(url)

const getEssenCritTypes = () => fetch('get-essen-crit-types/')

const deleteSubmissionFile = ({
  file,
  submissionId
}) => remove(`submissions/${submissionId}/files/${file.id}/`)

const callTransition = (url, transition) => post(`${url}call-transition/`, {
  transition
})

const getNonParties = (reporting_period) => fetch(`get-non-parties/?reporting_period=${reporting_period}`)

const getSubmissionDefaultValues = () => fetch('default-values/')

const getSubmissionStates = () => fetch('get-submission-states/')

const uploadFile = (file, submissionId, onProgressCallback) => new Promise(async (resolve, reject) => {
  const responseToken = await post(`submissions/${submissionId}/token/`)
  console.log(filesURL)
  const upload = new tus.Upload(file, {
    endpoint: filesURL,
    metadata: {
      token: responseToken.data.token,
      filename: file.name,
      description: file.description
    },
    retryDelays: [0, 1000, 3000, 5000],
    onError: function onError(error) {
      console.log('File upload failed because: ', error)
      reject(error)
    },
    onProgress: function onProgress(bytesUploaded, bytesTotal) {
      if (onProgressCallback) {
        const percentage = parseInt(((bytesUploaded / bytesTotal) * 100).toFixed(2), 10)
        onProgressCallback(file, percentage)
      }
    },
    onSuccess: function onSuccess() {
      resolve(upload)
    }
  })
  upload.start()
})

const getLimits = params => fetch('aggregations/', {
  params
})

const getEmailTemplates = () => fetch('email-templates/')

const getEmails = (submissionId) => fetch(`submissions/${submissionId}/email/`)

const sendEmail = (submissionId, mailData) => post(`submissions/${submissionId}/email/`, mailData)

const getReports = () => fetch('reports/')

const getReportingChannel = () => fetch('get-reporting-channels/')

const getControlledGroups = (party, period) => fetch(`parties/${party}/report_groups/?period=${period}`)

const getApprovedExemptionsList = (partyId, period) => fetch(`parties/${partyId}/approved_exemptions/?period=${period}`)

const getCriticalUseCategoryList = () => fetch('critical-use-categories/')

export {
  apiURL,
  apiBase,
  api,
  fetch,
  post,
  update,
  remove,
  getCookie,
  getSubstances,
  getFilteredSubstances,
  getExportBlends,
  getInstructions,
  getUsers,
  getParties,
  getPartyRatifications,
  getPeriods,
  getFilteredPeriods,
  getObligations,
  createSubmission,
  getSubmissions,
  getSubmissionHistory,
  getSubmissionsVersions,
  getSubmission,
  getSubmissionFiles,
  deleteSubmission,
  deleteSubmissionFile,
  createBlend,
  getCustomBlends,
  callTransition,
  cloneSubmission,
  getNonParties,
  getCurrentUser,
  updateCurrentUser,
  fetchFromPublicDirectory,
  getSubmissionStates,
  getSubmissionDefaultValues,
  uploadFile,
  getTransitions,
  getSubmissionFormat,
  getEssenCritTypes,
  getSubmissionAggregations,
  getLimits,
  getFilteredParties,
  getControlledGroups,
  getApprovedExemptionsList,
  getReports,
  getReportingChannel,
  getEmailTemplates,
  getEmails,
  sendEmail,
  getCriticalUseCategoryList
}
