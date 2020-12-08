<template>
  <b-btn
    v-show="canEnableEditMode && editModeEnabled"
    :disabled="$store.getters.getFilesUploadInProgress"
    @click="validation"
    id="save-button"
    ref="save_button"
    variant="primary"
  >
    <span v-translate>Save and continue</span>
  </b-btn>
</template>

<script>

import { post, update } from '@/components/common/services/api'
import { isObject } from '@/components/common/services/utilsService'
import { dateFormatToYYYYMMDD } from '@/components/common/services/languageService'
import { getCommonLabels } from '@/components/common/dataDefinitions/labels'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'
import FilesMixin from './FilesMixin'

export default {
  mixins: [FilesMixin],

  props: {
    submission: String
  },

  data() {
    return {
      invalidTabs: [],
      tabsToSave: [],
      labels: null,
      validateBeforeTransitions: ['before-submit'],
      alerts: getAlerts(this.$gettext)
    }
  },

  created() {
    this.labels = getCommonLabels(this.$gettext)
  },

  computed: {
    form() {
      return this.$store.state.form
    },
    newTabs() {
      return this.$store.state.newTabs
    },
    tabsToValidate() {
      return Object.values(this.form.tabs).filter(tab => tab.validate).map(tab => tab.name)
    },
    action() {
      return this.$store.state.dataForAction ? this.$store.state.dataForAction.transition : 'save'
    }
  },

  methods: {
    resetActionToDispatch(edit_mode = true) {
      this.$store.commit('setActionToDispatch', null)
      this.$store.commit('setDataForAction', null)
      this.updateEditMode(edit_mode)
    },
    updateEditMode(edit_mode) {
      this.$store.commit('updateEditMode', edit_mode)
      this.$router.push({ name: this.$route.name, query: { submission: this.submission, edit_mode } })
    },
    validation() {
      this.invalidTabs = []
      const restrictedTabs = [] // Tabs that are invalid because questionnaire answer is No while form_fields.length > 0
      for (const tab of this.tabsToValidate) {
        if (tab === 'sub_info' || this.validateBeforeTransitions.includes(this.action)) {
          if (tab !== 'files' || (tab === 'files' && !this.isSecretariat)) {
            if (
              this.form.tabs.questionaire_questions
              && this.form.tabs.questionaire_questions.form_fields.hasOwnProperty(tab)
              && this.form.tabs.questionaire_questions.form_fields[tab].selected === false
              && this.form.tabs[tab].form_fields.length > 0
            ) {
              restrictedTabs.push(this.form.tabs[tab].name)
              this.$store.commit('setTabStatus', { tab, value: false })
            }
            // DO NOT REMOVE THIS
            console.log(this.$store.getters.multiRowValidation(tab), tab)
            if (Object.keys(this.$store.getters.multiRowValidation(tab)).length) {
              this.invalidTabs.push(this.form.tabs[tab].name)
              this.$store.commit('setTabStatus', { tab, value: false })
            }
            if (Array.isArray(this.form.tabs[tab].form_fields)) {
              for (const field of this.form.tabs[tab].form_fields) {
                if (field.validation.selected.length) {
                  this.invalidTabs.push(this.form.tabs[tab].name)
                  this.$store.commit('setTabStatus', { tab, value: false })
                  break
                }
              }
            } else if (this.form.tabs[tab].form_fields.validation) {
              console.log(this.form.tabs[tab].form_fields.validation.selected.length)
              if (this.form.tabs[tab].form_fields.validation && this.form.tabs[tab].form_fields.validation.selected.length) {
                this.invalidTabs.push(this.form.tabs[tab].name)
                this.$store.commit('setTabStatus', { tab, value: false })
              }
            } else if (this.form.tabs[tab].validation === false) {
              this.invalidTabs.push(this.form.tabs[tab].name)
              this.$store.commit('setTabStatus', { tab, value: false })
            }
          }
        }
      }
      if (this.invalidTabs.length || restrictedTabs.length) {
        let message = { __all__: [`${this.$gettextInterpolate('Unable to save submission. Fill in the %{invalidTabs}', { invalidTabs: Array.from(new Set(this.invalidTabs)).map(tab => this.labels[tab]).join(', ') })} mandatory fields before saving.`] }

        if (this.validateBeforeTransitions.includes(this.action)) {
          message = { __all__: [] }
          if (this.invalidTabs.length) {
            message.__all__.push(
              `${this.$gettextInterpolate('Unable to %{nextTransition} submission. Fill in the %{invalidTabs} mandatory fields %{transition}.', {
                nextTransition: this.$store.state.dataForAction.nextTransition,
                invalidTabs: Array.from(new Set(this.invalidTabs)).map(tab => this.labels[tab]).join(', '),
                transition: this.$store.state.dataForAction.transition.split('-').join(' ')
              })}`
            )
          }
          if (restrictedTabs.length) {
            message.__all__.push(
              `${this.$gettextInterpolate('Submitting the form is not allowed because you have entered substances in %{invalidTabs} tab/tabs while choosing No in the corresponding questionnaire.', {
                invalidTabs: Array.from(new Set(restrictedTabs)).map(tab => this.labels[tab]).join(', ')
              })}`
            )
          }
        }
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message,
          variant: 'danger'
        })
        this.resetActionToDispatch()
      } else {
        this.prepareCommentsForSave()
        this.prepareDataForSave()
      }
    },

    prepareDataForSave() {
      //  This can be reimplemented in every component
      this.tabsToSave = []
      const doNotSave = []
      this.updateEditMode(false)
      Object.values(this.form.tabs).filter(tab => tab.hasOwnProperty('form_fields') && tab.hasOwnProperty('endpoint_url')).forEach(async tab => {
        if (this.form.tabs.questionaire_questions && this.form.tabs.questionaire_questions.form_fields) {
          if ( //  Tabs that are in questionaire_questions and are set to YES OR NO
            this.form.tabs.questionaire_questions.form_fields[tab.name]
            && this.form.tabs.questionaire_questions.form_fields[tab.name].selected !== null
            && (tab.status === 'edited' || tab.status === false)
          ) {
            this.tabsToSave.push(tab.name)
          } else if ( //  Tabs that are in questionaire_questions and are set to NO and have data
            this.form.tabs.questionaire_questions.form_fields[tab.name]
            && !this.form.tabs.questionaire_questions.form_fields[tab.name].selected
            && !tab.form_fields.length
            && this.newTabs.includes(tab.name)
          ) {
            doNotSave.push(tab.name)
          } else if (tab.status === 'edited' || tab.status === false) {
            this.tabsToSave.push(tab.name)
          }
        } else if (tab.status === 'edited' || tab.status === false) {
          this.tabsToSave.push(tab.name)
        }
        //  Submit data
        if (!doNotSave.includes(tab.name)) {
          const url = this.$store.state.current_submission[tab.endpoint_url]
          if (this.tabsToSave.includes(tab.name)) {
            await this.submitData(tab, url)
          } else {
            url && await this.submitData(tab, url)
          }
          this.checkIfThereIsAnotherActionToDoBeforeReturning(tab.name)
        }
      })
    },

    prepareCommentsForSave() {
      if (!this.form.formDetails.comments_default_properties) return
      const commentsObj = JSON.parse(JSON.stringify(this.form.formDetails.comments_default_properties))
      Object.keys(this.form.tabs).forEach(tab => {
        this.form.tabs[tab].comments && Object.keys(this.form.tabs[tab].comments).forEach(comment_field => {
          commentsObj[comment_field] = this.form.tabs[tab].comments[comment_field].selected
        })
      })
      const url = this.$store.state.current_submission[this.form.formDetails.comments_endpoint_url]
      this.saveComments(commentsObj, url)
    },

    async saveComments(data, url) {
      try {
        await update(url, data)
      } catch (error) {
        console.log(error)
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: error,
          variant: 'danger'
        })
        this.resetActionToDispatch()
      }
    },

    async submitData(tab, url) {
      await new Promise(async (resolve) => {
        if (tab.name === 'sub_info' && !this.canEditSubmissionInfoData) {
          resolve()
          return
        }
        if (tab.skipSave) {
          resolve()
          return
        }
        if (tab.status === 'edited' || tab.status === false) {
          this.$store.commit('setTabStatus', { tab: tab.name, value: 'saving' })
        } else {
          resolve()
          return
        }
        let current_tab_data

        if (Array.isArray(tab.form_fields)) {
          current_tab_data = []
          tab.form_fields.forEach(form_field => {
            const save_obj = JSON.parse(JSON.stringify(tab.default_properties))
            for (const row in form_field) {
              // special case for raf imports
              if (!form_field[row]) continue
              if (!Array.isArray(form_field[row])) {
                save_obj[row] = form_field[row] ? form_field[row].selected : null
              } else {
                save_obj[row] = form_field[row]
              }

              if (form_field[row].type === 'date') {
                save_obj[row] = dateFormatToYYYYMMDD(save_obj[row], this.$language.current)
              }
            }
            current_tab_data.push(save_obj)
          })
        }

        if (isObject(tab.form_fields)) {
          const save_obj = JSON.parse(JSON.stringify(tab.default_properties))
          current_tab_data = {}
          Object.keys(save_obj).forEach(key => {
            if (key === 'submitted_at' && !this.isSecretariat) {
              resolve()
              return
            }
            if (tab.name === 'flags') {
              if (this.$store.state.current_submission.changeable_flags.includes(key)) {
                current_tab_data[key] = tab.form_fields[key].selected
              }
            } else {
              current_tab_data[key] = tab.form_fields[key].selected
            }
            if (tab.form_fields[key].type === 'date') {
              current_tab_data[key] = dateFormatToYYYYMMDD(current_tab_data[key], this.$language.current)
            }
          })
        }

        try {
          if (this.newTabs.includes(tab.name) && tab.name !== 'files') {
            await post(url, current_tab_data)
            this.$store.commit('setTabStatus', { tab: tab.name, value: true })

            if (isObject(tab.form_fields)) {
              this.$store.commit('tabHasBeenSaved', tab.name)
            }

            if (Array.isArray(tab.form_fields)) {
              if (tab.form_fields.length) {
                this.$store.commit('tabHasBeenSaved', tab.name)
              } else {
                this.$store.commit('updateNewTabs', tab.name)
              }
            }
          } else {
            if (tab.name === 'files') {
              await this.uploadFiles()

              current_tab_data = this.getFilesWithUpdatedDescription()
                .map(file => ({
                  id: file.id,
                  name: file.name,
                  description: file.description
                }))
            }

            await update(url, current_tab_data)
            console.log('update done', tab.name)

            if (tab.name === 'files') {
              await this.getSubmissionFiles()
            }
            if (tab.status !== null) {
              this.$store.commit('setTabStatus', { tab: tab.name, value: true })
            }
            if (Array.isArray(tab.form_fields)) {
              if (!tab.form_fields.length) {
                this.$store.commit('updateNewTabs', tab.name)
              }
            }
          }
          if (tab.name === 'sub_info') {
            this.$store.dispatch('getNewTransitions')
          }
        } catch (error) {
          this.$store.commit('setTabStatus', { tab: tab.name, value: false })
          console.log(error)
          this.resetActionToDispatch()
          this.$store.dispatch('setAlert', {
            $gettext: this.$gettext,
            message: { __all__: [this.alerts.save_failed] },
            variant: 'danger' })
        }
        resolve()
      })
    },
    checkIfThereIsAnotherActionToDoBeforeReturning(tabName) {
      this.tabsToSave = this.tabsToSave.filter(t => t !== tabName)
      if (this.tabsToSave.length === 0) {
        if (this.$store.state.actionToDispatch) {
          this.$store.dispatch('clearEdited')
          this.$store.dispatch('saveCallback', { actionToDispatch: this.$store.state.actionToDispatch, data: this.$store.state.dataForAction })
          this.resetActionToDispatch(false)
        }
      }
    }
  }
}
</script>
