<template>
  <div>
    <b-btn class="square-right" @click="checkIfSaved('getAggregations')" variant="outline-dark" v-translate>Calculated amounts</b-btn>
    <b-modal id="aggregationModal" size="xl" ref="aggregationModal">
      <div slot="modal-title">
        <span v-translate>Calculated production and consumption</span> - {{ $store.state.initialData.display.countries[$store.state.current_submission.party] }} - {{ $store.state.current_submission.reporting_period }}
      </div>
      <AggregationsTable :standalone="false" :aggregations="aggregations"></AggregationsTable>
      <div slot="modal-footer">
        <b-btn
          variant="outline-dark mr-2"
          @click="exportPDF"
         v-translate>Export PDF</b-btn>
        <b-btn @click="$refs.aggregationModal.hide()" variant="outline-danger" v-translate>Close</b-btn>
      </div>
    </b-modal>
  </div>
</template>
<script>

import { getSubmissionAggregations } from '@/components/common/services/api'
import AggregationsTable from '@/components/common/AggregationsTable'
import SaveWatcher from '@/components/common/SaveWatcher'

export default {
  props: {
    submission: String
  },
  components: {
    AggregationsTable
  },
  mixins: [SaveWatcher],
  data() {
    return {
      aggregations: null,
      id: null
    }
  },
  computed: {
    unsaved() {
      const tabsWithData = []
      Object.values(this.$store.state.form.tabs).forEach((tab) => {
        [false, 'edited'].includes(tab.status) && tabsWithData.push(tab.title)
      })
      return tabsWithData.length
    }
  },
  methods: {
    async checkIfSaved(callback) {
      if (this.unsaved) {
        const confirmed = await this.$store.dispatch('openConfirmModal', { title: 'Please confirm', description: 'You have unsaved changes in the data form. Do you wish to save before continuing ?', $gettext: this.$gettext })
        if (confirmed) {
          this.triggerSave(this[callback])
        }
      } else {
        this[callback]()
      }
    },
    async getAggregations() {
      const aggregations = await getSubmissionAggregations(this.submission)
      this.aggregations = aggregations.data
      this.$refs.aggregationModal.show()
    },
    async exportPDF() {
      this.$store.dispatch('downloadStuff', {
        url: `${this.submission}/export_prodcons_pdf/`,
        fileName: `${this.$store.state.current_submission.obligation} - ${this.$store.state.initialData.display.countries[this.$store.state.current_submission.party]} - ${this.$store.state.current_submission.reporting_period} - production & consumption.pdf`
      })
    }
  }
}
</script>
<style>
  .square-right {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
  }
  #aggregationModal.modal.show .modal-dialog {
    margin-top: 5rem;
  }
</style>

