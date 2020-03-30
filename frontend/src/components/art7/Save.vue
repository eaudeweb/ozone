<script>
import SaveMixin from '@/components/common/mixins/SaveMixin'

export default {
  mixins: [SaveMixin],
  methods: {
    alertUnsavedData(tabName, tab, url) {
      const answer = window.confirm(`${this.$gettextInterpolate('Data in form "%{tab}" will be removed, because you have chosen "No" in the questionnaire for the corresponding question.', { tab: this.labels[tabName] })}`)
      if (answer) {
        this.$store.dispatch('removeDataFromTab', tabName).then(async () => {
          await this.submitData(tab, url)
          this.checkIfThereIsAnotherActionToDoBeforeReturning(tab.name)
        })
        return true
      }
      // this.$store.dispatch('setAlert', {
      // 	$gettext: this.$gettext,
      // 	message: { __all__: [`${tabName}: ${this.$gettext('Data was not saved')}`] },
      // 	variant: 'danger' })
      // this.$store.commit('setTabStatus', { tab: tabName, value: false })
      return false
    },

    prepareDataForSave() {
      const justSave = []
      const removeDataAndSave = []
      const doNotSave = []
      Object.values(this.form.tabs.questionaire_questions.form_fields).forEach(questionnaire_field => {
        if (questionnaire_field.selected && !this.invalidTabs.includes(questionnaire_field.name)) {
          justSave.push(questionnaire_field.name)
        }
        if (questionnaire_field.selected === false && this.$store.state.form.tabs[questionnaire_field.name].form_fields.length) {
          removeDataAndSave.push(questionnaire_field.name)
        }
        if (!questionnaire_field.selected
						&& !this.$store.state.form.tabs[questionnaire_field.name].form_fields.length
						&& this.newTabs.includes(questionnaire_field.name)) {
          doNotSave.push(questionnaire_field.name)
        }
      })
      Object.values(this.form.tabs).filter(tab => !Object.keys(this.form.tabs.questionaire_questions.default_properties).includes(tab.name)).forEach(tab => {
        if (tab.status === 'edited' && !doNotSave.includes(tab.name)) {
          justSave.push(tab.name)
        }
      })
      let stopSave = false
      Object.values(this.form.tabs).filter(tab => tab.hasOwnProperty('form_fields')).forEach(tab => {
        const url = this.$store.state.current_submission[tab.endpoint_url]
        if (removeDataAndSave.includes(tab.name)) {
          if (!this.alertUnsavedData(tab.name, tab, url)) {
            stopSave = true
          } else {
            stopSave = false
          }
        }
      })
      this.tabsToSave = [...justSave, ...removeDataAndSave]
      if (!stopSave) {
        this.updateEditMode(false)
        this.$router.push({ name: this.$route.name, query: { submission: this.submission, edit_mode: false }, params: { obligation_type: this.obligation_type } })
        Object.values(this.form.tabs).filter(tab => tab.hasOwnProperty('form_fields')).forEach(async tab => {
          const url = this.$store.state.current_submission[tab.endpoint_url]
          if (!doNotSave.includes(tab.name)) {
            if (justSave.includes(tab.name)) {
              await this.submitData(tab, url)
            } else {
              url && await this.submitData(tab, url)
            }
            this.checkIfThereIsAnotherActionToDoBeforeReturning(tab.name)
          }
        })
      }
    }
  }
}
</script>
