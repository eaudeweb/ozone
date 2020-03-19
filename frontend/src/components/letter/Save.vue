<script>
import SaveMixin from '@/components/common/mixins/SaveMixin'

export default {
  mixins: [SaveMixin],
  methods: {
    prepareDataForSave() {
      const justSave = []
      Object.values(this.form.tabs).filter(tab => tab.hasOwnProperty('form_fields') && tab.hasOwnProperty('endpoint_url')).forEach(async tab => {
        if (tab.status === 'edited') {
          justSave.push(tab.name)
        }
        this.tabsToSave = [...justSave]
        const url = this.$store.state.current_submission[tab.endpoint_url]
        await this.submitData(tab, url)
        this.checkIfThereIsAnotherActionToDoBeforeReturning(tab.name)
      })
    }
  }
}
</script>
