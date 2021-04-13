<template>
  <div class="app blends-lookup-table flex-row align-items-top">
    <div class="w-100 pt-3">

      <!-- Filters -->
      <b-row v-if="tableReady && currentUser">
        <b-col v-for="(filterValue, filterKey) in filters" :key="filterKey">
          <b-input-group horizontal :prepend="$gettext(filterValue.name)" class="mb-1">
            <b-form-select v-model="selectedFilters[filterKey]">
              <option :value="null" selected></option>
              <option
                v-for="option in filterValue.options"
                :value="option.id"
                :key="option.id"
              >{{option.name}}</option>
            </b-form-select>
          </b-input-group>
        </b-col>
        <b-col md="1">
          <b-input-group-append>
            <b-btn id="blends-clear-button" variant="light" @click="onResetFilters">
              <span v-translate>Clear</span>
            </b-btn>
          </b-input-group-append>
        </b-col>
      </b-row>

      <!-- Table -->
      <b-table
        no-sort-reset
        show-empty
        outlined
        bordered
        hover
        head-variant="light"
        class="full-bordered"
        stacked="md"
        :items="filteredItems"
        :fields="fields"
        :sort-by.sync="sorting.sortBy"
        :sort-desc.sync="sorting.sortDesc"
        :sort-direction="sorting.sortDirection"
        :per-page="tableOptions.params.page_size"
        ref="table"
        @sort-changed="sortings"
      >
        <template v-slot:thead-top>
          <tr>
            <th v-for="(category, index) in tableTop" :key="index" :colspan="category.colspan">
              {{category.label}}
            </th>
          </tr>
        </template>
      </b-table>

      <b-row>
        <b-col md="10" class="my-1">
          <b-pagination
            :total-rows="tableOptions.totalRows"
            :per-page="tableOptions.params.page_size"
            v-model="tableOptions.params.page"
            class="my-0"
          />
        </b-col>
        <b-col md="2">
          <b-input-group horizontal :prepend="$gettext('Per page')" class="mb-0">
            <b-form-select
              :options="tableOptions.pageOptions"
              v-model="tableOptions.params.page_size"
            />
          </b-input-group>
        </b-col>
      </b-row>
    </div>
  </div>
</template>

<script>
import { getLimits, getFilteredPeriods, getFilteredSubstances, getFilteredParties } from '@/components/common/services/api.js'
import authMixin from '@/components/common/mixins/auth'

export default {
  mixins: [authMixin],
  data() {
    return {
      fields: [
        { key: 'party', label: this.$gettext('Party'), sortable: true, sortDirection: 'desc' },
        { key: 'group', label: this.$gettext('Annex/Group'), sortable: true, sortDirection: 'desc' },
        { key: 'reporting_period', label: this.$gettext('Reporting period'), sortable: true },
        { key: 'baseline_prod', label: this.$gettext('Baseline'), class: 'text-right' },
        { key: 'calculated_production', label: this.$gettext('Calculated'), class: 'text-right' },
        { key: 'limit_prod', label: this.$gettext('Limit'), class: 'text-right' },
        { key: 'baseline_cons', label: this.$gettext('Baseline'), class: 'text-right' },
        { key: 'calculated_consumption', label: this.$gettext('Calculated'), class: 'text-right' },
        { key: 'limit_cons', label: this.$gettext('Limit'), class: 'text-right' },
        // { key: 'baseline_bdn', label: this.$gettext('Baseline') },
        { key: 'production_article_5', label: this.$gettext('Reported'), class: 'text-right' },
        { key: 'limit_bdn', label: this.$gettext('Limit'), class: 'text-right' }
      ],
      items: [],
      filters: {
        party: { name: 'Party', options: [], call: getFilteredParties },
        group: { name: 'Annex/Group', options: [], call: getFilteredSubstances },
        reporting_period: { name: 'Reporting period', options: [], call: getFilteredPeriods }
      },
      selectedFilters: {
        party: null,
        group: null,
        reporting_period: null
      },
      prefiledFilters: false,
      sorting: {
        sortBy: 'reporting_period',
        sortDesc: true,
        sortDirection: 'desc'
      },
      tableOptions: {
        pageOptions: [10, 25, 100],
        totalRows: 0,
        params: {
          page_size: 10,
          page: null,
          party: null,
          reporting_period: null,
          group: null,
          ordering: null
        }
      },
      tableTop: [
        {
          label: ''
        },
        {
          label: ''
        },
        {
          label: ''
        },
        {
          label: this.$gettext('Production'),
          colspan: 3
        }, {
          label: this.$gettext('Consumption'),
          colspan: 3
        }, {
          label: this.$gettext('Production allowance for BDN of Article 5 Parties'),
          colspan: 2
        }
      ],
      tableReady: false,
      canRequest: false
    }
  },
  computed: {
    currentUser() {
      const { currentUser, submissionDefaultValues } = this.$store.state

      if (!this.prefiledFilters && currentUser && this.filters.reporting_period.options.length > 0) {
        this.selectedFilters.party = currentUser.party
        this.selectedFilters.reporting_period = this.filters.reporting_period.options.find((option) => option.name === submissionDefaultValues.reporting_period).id
        this.prefiledFilters = true
      }

      return currentUser
    },
    filteredItems: function filterItems() {
      const tempItems = this.items.slice()
      const result = tempItems.map(item => {
        for (const itemKey in item) {
          const filter = this.filters[itemKey]

          if (filter) {
            const optionItem = filter.options.find(option => option.id === item[itemKey])
            if (optionItem) {
              item[itemKey] = optionItem.name
            }
          }
        }
        return item
      })
      return result
    }
  },
  methods: {
    makeFilters() {
      const allPromises = this.makeArrayOfPromises()
      this.assignOptionsToFilters(allPromises)
    },
    assignOptionsToFilters(promises) {
      Promise.all(promises).then((responses) => {
        for (const responseItem of responses) {
          this.filters[responseItem.filterName].options = responseItem.response.data.slice()
        }
      })
    },
    makeArrayOfPromises() {
      const allPromises = []

      for (const filterName in this.filters) {
        const p = new Promise((resolve, reject) => {
          this.filters[filterName].call()
            .then((response) => {
              resolve({ filterName, response })
            })
            .catch((error) => reject(error))
        })
        allPromises.push(p)
      }
      return allPromises
    },
    getItems() {
      getLimits(this.tableOptions.params).then((response) => {
        this.items = response.data.results.slice()
        this.tableOptions.totalRows = response.data.count
        this.tableReady = true
      })
    },
    sortings(el) {
      if (el.sortBy) {
        this.tableOptions.params.page = null
        this.canRequest = false
        this.tableOptions.params.ordering = el.sortDesc ? `-${el.sortBy}` : el.sortBy
        this.getItems()
      }
    },
    onResetFilters() {
      const currentFilters = JSON.parse(JSON.stringify(this.selectedFilters))
      const tableOptionsParams = JSON.parse(JSON.stringify(this.tableOptions.params))

      for (const filter in currentFilters) {
        currentFilters[filter] = null
      }
      for (const option in tableOptionsParams) {
        tableOptionsParams[option] = null
      }
      [tableOptionsParams.page_size] = this.tableOptions.pageOptions // this will take the first value

      this.selectedFilters = { ...currentFilters }
      this.tableOptions.params = { ...tableOptionsParams }
      this.sorting = {
        sortBy: 'reporting_period',
        sortDesc: true,
        sortDirection: 'desc'
      }
    },
    updateBreadcrumbs() {
      this.$store.commit('updateBreadcrumbs', `${this.$gettext('Production and consumption')} | ${this.$gettext('Online Reporting System')}`)
    }
  },

  created() {
    this.getItems()
    this.updateBreadcrumbs()
    this.$store.dispatch('getMyCurrentUser')
    this.$store.dispatch('getDashboardParties').then(() => this.makeFilters())
    this.$store.dispatch('getSubmissionDefaultValues')
  },

  watch: {
    'selectedFilters': {
      handler() {
        this.canRequest = false
        this.tableOptions.params = { ...this.tableOptions.params, ...this.selectedFilters }
        this.tableOptions.params.page = null
        this.getItems()
      },
      deep: true
    },
    'tableOptions.params.page': {
      handler() {
        if (this.canRequest) {
          this.getItems()
        }
        this.canRequest = true
      }
    },
    'tableOptions.params.page_size': {
      handler() {
        this.canRequest = false
        this.tableOptions.params.page = null
        this.getItems()
      }
    },
    '$language.current': {
      handler() {
        this.updateBreadcrumbs()
      }
    }
  }
}
</script>

<style scoped>
  table thead tr:first-of-type th{
    text-align: center;
  }
</style>
