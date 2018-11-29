import Vue from 'vue'
import Vuex from 'vuex'
import form from '@/assets/form.js'
import tableRowConstructor from '@/mixins/tableRowConstructor'
import { 
    fetch, 
    getSubmissionHistory, 
    callTransition, 
    getSubstances, 
    getExportBlends, 
    getSubmission, 
    getCustomBlends, 
    deleteSubmission, 
    getSubmissions, 
    getPeriods, 
    getObligations, 
    createSubmission, 
    getParties 
} from '@/api/api.js'

import dummyTransition from '@/assets/dummyTransition.js'

Vue.use(Vuex)

function intersect(a, b) {
    var setA = new Set(a);
    var setB = new Set(b);
    var intersection = new Set([...setA].filter(x => setB.has(x)));
    return Array.from(intersection);
}

const store = new Vuex.Store({
    // strict: true,
    state: {
        dashboard: {
            submissions: null,
            periods: null,
            obligations: null,
            parties: null,
        },
        currentAlert: {
            message: null,
            show: false,
            variant: null,
        },
        current_submission: null,
        currentSubmissionHistory: null,
        available_transitions: null,
        permissions: {
            dashboard: null,
            form: null,
            actions: null,
        },
        newTabs: [],
        form: null,
        initialData: {
            countryOptions: null,
            substances: null,
            blends: null,
            display: {
                substances: null,
                blends: null,
                countries: null,
            }
        },
    },


    getters: {
        // ...
        getValidationForCurrentTab: (state) => (tab) => {
            if(['edited',false].includes(state.form.tabs[tab].status)){
                return state.form.tabs[tab].form_fields.map(field => field.validation.selected ?
                    { validation: field.validation.selected, substance: field.substance.selected, blend: field.blend ? field.blend.selected : null } :
                    null)
            }
        },


        getDuplicateSubmission: (state) => (data) => {
            return state.dashboard.submissions.filter(
                (sub) => {
                    return sub.obligation === data.obligation &&
                        sub.party === data.party &&
                        sub.reporting_period === data.reporting_period
                })
        },


        getSubmissionInfo: (state) => (submission) =>{
          let submissionInfo = {
            obligation: () => {
              return state.dashboard.obligations.find( a => { return a.value === submission.obligation }).text
            },
            period: () => {
              return state.dashboard.periods.find(a => {return a.value === submission.reporting_period}).text
            },
            party: () => {
              return state.dashboard.parties.find(a => { return a.value === submission.party}).text
            },
            period_start: () => {
              return state.dashboard.periods.find(a => {return a.value === submission.reporting_period}).start_date.split('-')[0]
            },
            period_end: () => {
              return state.dashboard.periods.find(a => {return a.value === submission.reporting_period}).end_date.split('-')[0]
            },
          }
          return submissionInfo
        },



        getPeriodStatus: (state) => (periodId) => {
            return state.dashboard.periods.find( (period) => { return period.value === periodId}).is_reporting_open
        },

        checkIfBlendAlreadyEists: (state) => (blendName) => {
            return state.initialData.blends.find( (blend) => { return blend.blend_id === blendName})
        },

        transitionState: (state) => {
            const currentState = state.permissions.form
            const availableTransitions = state.available_transitions || []

            let tstate = null
            if (intersect(currentState, ['edit', 'save']).length)
                tstate = false
            else
                tstate = true

            if (!availableTransitions.includes('submit')) {
                tstate = true
            }

            return tstate
        },
    },

    actions: {

        addSubmission(context, data) {
            return new Promise((resolve, reject) => {
                const duplicate = context.getters.getDuplicateSubmission(data)
                const isReportingOpen = context.getters.getPeriodStatus(data.reporting_period)
                if (duplicate.length) {
                    context.dispatch('setAlert', { message: 'Another submission already exists in Data Entry stage.', variant: 'danger' })
                } 
                // TODO: should this be a thing ?
                // else if(!isReportingOpen) {
                //     context.dispatch('setAlert', { message: 'Reporting is not open for the selected period', variant: 'danger' })
                // } 
                else {
                    createSubmission(data).then((response) => {
                        context.dispatch('setAlert', { message: 'Submission Created', variant: 'success' })
                        context.dispatch('getCurrentSubmissions').then( r => {
                            resolve(response.data)
                        })
                        
                    }).catch((error) => {
                        context.dispatch('setAlert', { message: 'Failed to create submission', variant: 'danger' })
                        reject(error.response)
                    })
                }
            });

        },

        getCurrentSubmissions(context) {
            return new Promise((resolve, reject) => {
                getSubmissions().then(response => {
                    context.commit('setDashboardSubmissions', response.data)
                    resolve()
                })
            })
        },

        async getDashboardParties(context) {
            let response 
            try {
                response = await getParties()
            } catch(e) {
                console.log(e)
                return
            }

            const parties_temp = response.data
                                        .filter( country => country.id === country.parent_party )
                                        .map( country => {
                                            return { value: country.id, text: country.name}                 
                                        })
                context.commit('setDashboardParties', parties_temp)
        },

        getDashboardPeriods(context) {
            getPeriods().then(response => {
                let sortedPeriods = response.data
                                    .filter( a => a.is_reporting_allowed )
                                    .sort((a, b) => { 
                                        return (parseInt(b.end_date.split('-')[0]) - parseInt(a.end_date.split('-')[0])) === 0
                                        ?
                                        (parseInt(b.start_date.split('-')[0]) - parseInt(a.start_date.split('-')[0]))
                                        :
                                        (parseInt(b.end_date.split('-')[0]) - parseInt(a.end_date.split('-')[0]))
                                    })
                                    .sort((a, b) => { return  b.is_year - a.is_year })
               sortedPeriods = sortedPeriods.map( (period) => {
                    let start = period.start_date.split('-')[0]
                    let end = period.end_date.split('-')[0]
                    let periodDisplay = ''
                    if(start === end) {
                        if(period.name != start) {
                            periodDisplay += `(${start})`
                        }
                    } else {
                        periodDisplay += `(${start} - ${end})`
                    }

                    return { value: period.id, text: `${period.name} ${periodDisplay}`, end_date: period.end_date, start_date: period.start_date, is_reporting_open: period.is_reporting_open}
               })
                
                context.commit('setDashboardPeriods', sortedPeriods)
            })
        },

        getDashboardObligations(context) {
            getObligations().then(response => {
                let obligations_temp = response.data.map( obligation => { return { value: obligation.id, text: obligation.name, form_type: obligation.form_type}})
                context.commit('setDashboardObligations', obligations_temp)
            })
        },


        resetAlert(context) {
            return new Promise((resolve, reject) => {
                context.commit('setCurrentAlertMessage', null)
                context.commit('setCurrentAlertVisibility', false)
                context.commit('setCurrentAlertVariant', null)
                resolve()
            });
        },

        setAlert(context, data) {
            context.dispatch('resetAlert').then(r => {
                context.commit('setCurrentAlertMessage', data.message)
                context.commit('setCurrentAlertVisibility', true)
                context.commit('setCurrentAlertVariant', data.variant)
            })
        },

        prefillQuestionaire(context, data) {
            Object.keys(context.state.current_submission.article7questionnaire).forEach((element, index) => {
                context.commit('updateQuestionaireField', { value: context.state.current_submission.article7questionnaire[element], field: element })
            });
        },


        doSubmissionTransition(context, data) {
            callTransition(data.submission, data.transition).then((response) => {
                context.dispatch('getSubmissionData', data.submission)
                context.dispatch('setAlert', { message: 'Submission state updated', variant: 'success' })
            }).catch( error => {
                context.dispatch('setAlert', { message: 'Unable to change the state of this submission', variant: 'danger' })
                console.log(error)
            })
        },

        removeSubmission(context, submissionUrl) {
            deleteSubmission(submissionUrl).then((response) => {
                context.dispatch('getCurrentSubmissions')
                context.dispatch('setAlert', { message: 'Submission deleted', variant: 'success' })
            }).catch(error => {
                context.dispatch('getCurrentSubmissions')
                context.dispatch('setAlert', { message: 'Failed to delete submission', variant: 'danger' })
            })
        },


        getInitialData(context, data) {
            context.commit('getEmptyForm')
            return new Promise((resolve, reject) => {
                context.dispatch('getSubmissionData',data).then(r => {
                    context.dispatch('getCountries')
                    context.dispatch('getSubstances')
                    context.dispatch('getCustomBlends')
                    resolve()
                })
            });
        },



        getSubmissionData(context, data) {
            return new Promise((resolve, reject) => {
                getSubmission(data).then((response) => {
                    context.commit('updateSubmissionData', response.data)
                    context.commit('updateAvailableTransitions', response.data.available_transitions)
                    if (context.state.current_submission.article7questionnaire) {
                        context.dispatch('prefillQuestionaire')
                    }
                    context.commit('updateFormPermissions', dummyTransition)
                    context.dispatch('getCurrentSubmissionHistory', data)
                    resolve()
                })

            });

        },


        getCurrentSubmissionHistory(context, data) {
            getSubmissionHistory(data).then((response) => {
                context.commit('setSubmissionHistory', response.data)
            }).catch((error) => {
                context.dispatch('setAlert', { message: error.response.data, variant: 'danger' })
            })
        },



        getCountries(context) {
            let countryDisplay = {}
            getParties().then(response => {
                let countryOptions  = response.data.filter((p)=>{
                    countryDisplay[p.id] = p.name
                    return p.id != context.state.current_submission.party
                }).map((country) => {
                    return { value: country.id, text: country.name }
                })
                context.commit('updateCountries', countryOptions)
                context.commit('updateCountriesDisplay', countryDisplay)
            })
        },

        getSubstances(context) {
            let tempSubstances = []
            let substancesDisplay = {}
            getSubstances().then((response) => {
                for (let group of response.data) {
                    group.substances.sort( (a,b) => {return a.sort_order - b.sort_order})
                    for (let substance of group.substances) {
                        tempSubstances.push({ value: substance.id, text: substance.name, group: group })
                        substancesDisplay[substance.id] = substance.name
                    }
                }
                context.commit('updateSubstances', tempSubstances)
                context.commit('updateSubstancesDisplay', substancesDisplay)
            })
        },

        getCustomBlends(context) {
            let blendsDisplay = {}
            getCustomBlends().then((response) => {
                for (let blend of response.data) {
                    blendsDisplay[blend.id] = { name: blend.blend_id, components: blend.components }
                }
                context.commit('updateBlends', response.data)
                context.commit('updateBlendsDisplay', blendsDisplay)
            })
        },


        createSubstance(context, data) {
            let substancesHere = data.substanceList && data.substanceList.some((el) => { return el !== null })
            let blendsHere = data.blendList && data.blendList.some((el) => { return el !== null })
            if (substancesHere) {
                data.substanceList.forEach( substance => {
                    let ordering_id = 0
                    if(!data.prefill){
                        context.commit('incrementOrderingId',{tabName:data.currentSectionName})
                        ordering_id = context.state.form.tabs[data.currentSectionName].ordering_id
                    }
                    
                    // section, substance, group, country, blend, prefillData, ordering_id
                    let inner_fields = tableRowConstructor.getInnerFields({
                                                                section: data.currentSectionName, 
                                                                substance, 
                                                                group: data.groupName, 
                                                                country: data.country, 
                                                                blend: null, 
                                                                prefillData: data.prefillData, 
                                                                ordering_id
                                                            })
                    context.commit('addSubstance', { sectionName: data.currentSectionName, row: inner_fields })                    
                })
            } else if (blendsHere) {
                data.blendList.forEach( blend => {
                    let ordering_id = 0
                    if(!data.prefill) {
                        context.commit('incrementOrderingId',{tabName:data.currentSectionName})
                        ordering_id = context.state.form.tabs[data.currentSectionName].ordering_id
                    }
                    let inner_fields = tableRowConstructor.getInnerFields({
                                                                section: data.currentSectionName, 
                                                                substance: null, 
                                                                group: data.groupName, 
                                                                country: data.country, 
                                                                blend, 
                                                                prefillData: data.prefillData, 
                                                                ordering_id
                                                            })
                    context.commit('addSubstance', { sectionName: data.currentSectionName, row: inner_fields })
                })
                
            }
        },

        prefillEmissionsRow(context, data) {
            let row = {
                id: {
                    selected: null,
                },
                ordering_id: {
                    selected: 0,
                },
                facility_name: {
                    type: 'text',
                    selected: '',
                },
                quantity_generated: {
                    type: 'number',
                    selected: '',
                },
                quantity_feedstock: {
                    type: 'number',
                    selected: '',
                },
                quantity_destroyed: {
                    type: 'number',
                    selected: '',
                },
                quantity_emitted: {
                    type: 'number',
                    selected: '',
                },
                remarks_party: {
                    type: 'textarea',
                    selected: '',
                },
                remarks_os: {
                    type: 'textarea',
                    selected: '',
                },
                get validation() {
                    let errors = []
                    if (!this.facility_name.selected) {
                        errors.push('eroare1')
                    }

                    let returnObj = {
                        type: 'nonInput',
                        selected: errors
                    }

                    return returnObj
                },
            }
            if (data) {
                Object.keys(data).forEach((element, index) => {
                    row[element].selected = data[element]
                });
            }
            context.commit('addEmissionsRow', row)
        },

        removeDataFromTab(context, data) {
            return new Promise((resolve, reject) => {
                context.commit('resetTab', data)
                resolve()
            });
        },

        uploadFormAttachments({ commit, state }, uploadedFiles) {
            //upload to the server       
            //mocking server response
            const mockResponseAttachments = uploadedFiles.map(file => {
                return {
                    id: Math.floor(Math.random() * 100000),
                    name: file.name,
                    url: 'https://www.google.com',
                    size: `${file.size} bytes`,
                    dateUploaded: new Date(),
                    description: `DESCRIPTION ${file.name} ${file.name} ${file.name} ${file.name} ${file.name} ${file.name} ${file.name} ${file.name} ${file.name} ${file.name} ${file.name}`
                }
            });
            commit('setFormAttachments', [...state.form.tabs.attachments, ...mockResponseAttachments]);
        },

        saveFormAttachments({ commit, state }, payload) {                  
            alert('attachments saved');
            console.log(state.form.tabs.attachments);
        },
    },

    mutations: {
            // data - {value:value, fieldInfo:{index:tab_info.form_fields.indexOf(row),tabName: tabName, field:order}}
        updateFormField(state,data){
            let path;
            console.log(data.value)
            data.fieldInfo.index === data.fieldInfo.field 
            ?
            state.form.tabs[data.fieldInfo.tabName].form_fields[data.fieldInfo.index].selected = data.value
            :
            state.form.tabs[data.fieldInfo.tabName].form_fields[data.fieldInfo.index][data.fieldInfo.field].selected = data.value 
        },


        setSubmissionHistory(state,data){
            state.currentSubmissionHistory = data
        },

        getEmptyForm(state){
            state.form = JSON.parse(JSON.stringify(form))
        },


        incrementOrderingId(state,data){
            state.form.tabs[data.tabName].ordering_id += 1 
        },
    

        setTabOrderingId(state,data){
            console.log(data.tabName)
            state.form.tabs[data.tabName].ordering_id = data.ordering_id 
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
            state.dashboard.submissions = data
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

        updateSubmissionData(state, data) {
            state.current_submission = data
        },

        updateCountries(state, data) {
            state.initialData.countryOptions = data
        },

        updateCountriesDisplay(state, data) {
            state.initialData.display.countries = data
        },

        updateSubstances(state, data) {
            state.initialData.substances = data
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


        // questionaire
        updateQuestionaireField(state, data) {
            let currentField = store.state.form.tabs.questionaire_questions.form_fields[data.field]
            currentField && (currentField.selected = data.value)
        },

        // addsubstance
        addSubstance(state, data) {
            store.state.form.tabs[data.sectionName].form_fields.push(data.row)
        },

        addEmissionsRow(state, data) {
            store.state.form.tabs.has_emissions.form_fields.push(data)
        },

        addCreateBlendToBlendList(state, data) {
            store.state.initialData.blends.push(data)
        },

        setTabStatus(state, data) {
            store.state.form.tabs[data.tab].status = data.value
        },

        // permissions
        updateDashboardPermissions(state, permission) {
            state.permissions.dashboard = permission
        },
        updateFormPermissions(state, permission) {
            state.permissions.form = permission
        },
        updateActionsPermissions(state, permission) {
            state.permissions.actions = permission
        },

        // form state
        updateNewTabs(state, tab) {
            state.newTabs.push(tab)
        },

        tabHasBeenSaved(state, tab) {
            state.newTabs = state.newTabs.filter( currentTab => currentTab !== tab)
        },

        // removal

        resetTab(state, tab) {
            state.form.tabs[tab].form_fields = []
        },

        removeField(state, data) {
            state.form.tabs[data.tab].form_fields.splice(data.index, 1)
        },

        setFormAttachments(state, attachments) {
            state.form.tabs.attachments = attachments;
        },

        updateFormAttachment(state, attachment) {            
            const updatedAttachments = [];
            state.form.tabs.attachments.forEach(attach => {
                attach.id === attachment.id ? updatedAttachments.push(attachment) : updatedAttachments.push(attach)
            });
            state.form.tabs.attachments = updatedAttachments;
        },
        deleteFormAttachment(state, attachment) {           
            state.form.tabs.attachments = state.form.tabs.attachments.filter(attach => attach.id !== attachment.id);
        },        
    }
})


export default store