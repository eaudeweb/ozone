<template>
  <div class="dashboard-page animated fadeIn">
    <b-row>
      <b-col v-if="basicDataReady && !currentUser.is_read_only" sm="12" :xl="currentUser.is_secretariat ? '12' : '6'">
        <b-card>
          <div slot="header">
            <strong>
              <span v-translate>Create submission</span>
            </strong>
          </div>
          <small>
            <span
              v-translate
            >Create a submission by specifying the obligation, the reporting period and the party name. All fields are mandatory.</span>
          </small>
          <div class="create-submission mt-2">
            <b-input-group id="obligation_selector" class="mb-2" :prepend="$gettext('Obligation')">
              <multiselect
                :placeholder="$gettext('Select option')"
                trackBy="value"
                label="text"
                v-model="submissionNew.obligation"
                :hide-selected="false"
                :options="obligationsOptions"
              />
            </b-input-group>

            <b-input-group id="period_selector" class="mb-2" :prepend="$gettext('Period')">
              <multiselect
                :placeholder="$gettext('Select option')"
                trackBy="value"
                label="description"
                customTemplateText="<i class='fa fa-clock-o fa-lg'></i>"
                customTemplate="is_reporting_open"
                :hide-selected="false"
                v-model="submissionNew.reporting_period"
                :options="periods"
              />
            </b-input-group>

            <b-input-group id="party_selector" class="mb-2" :prepend="$gettext('Party')">
              <multiselect
                :placeholder="$gettext('Select option')"
                trackBy="value"
                label="text"
                :disabled="Boolean(currentUser.party)"
                v-model="submissionNew.party"
                :hide-selected="false"
                :options="parties"
              />
            </b-input-group>

            <b-btn
              v-if="basicDataReady"
              :disabled="!(submissionNew.obligation && submissionNew.reporting_period && submissionNew.party)"
              variant="primary"
              @click="addSubmission"
            >
              <span v-translate>Create</span>
            </b-btn>
          </div>
        </b-card>
      </b-col>

      <b-col sm="12" xl="6" v-if="!currentUser.is_secretariat">
        <b-card v-if="basicDataReady">
          <div slot="header">
            <strong>
              <span
                v-translate="{totalRows: dataEntryTable.totalRows}"
              >Data entry in progress submissions (%{totalRows} records)</span>
            </strong>
          </div>
          <b-table
            id="data-entry-submissions-table"
            show-empty
            outlined
            bordered
            hover
            head-variant="light"
            stacked="md"
            :filter="dataEntryTable.search"
            :items="dataEntryTableItems"
            :fields="dataEntryTableFields"
            :per-page="dataEntryTable.perPage"
            :current-page="dataEntryTable.currentPage"
            :sort-by.sync="dataEntryTable.sorting.sortBy"
            :sort-desc.sync="dataEntryTable.sorting.sortDesc"
            :sort-direction="dataEntryTable.sorting.sortDirection"
            :sort-compare="sortCompare"
            ref="dataEntryTable"
            @filtered="onFiltered"
          >
            <template v-slot:cell(actions)="row">
              <router-link
                class="btn btn-light btn-sm"
                :to="{ name: getFormName(row.item.details.obligation), query: { submission: row.item.details.id, edit_mode: !!row.item.details.can_edit_data }}"
              >
                <span v-if="row.item.details.can_edit_data">{{labels['edit']}}</span>
                <span v-else>{{labels['view']}}</span>
              </router-link>
            </template>
          </b-table>
        </b-card>
      </b-col>
    </b-row>
    <b-row>
      <b-col sm="12">
        <b-card no-body v-if="basicDataReady">
          <template slot="header">
            <b-row>
              <b-col>
                <b>
                  <span
                    v-translate="{totalRows: tableOptions.totalRows}"
                  >All submissions (%{totalRows} records)</span>
                </b>
              </b-col>
              <b-col style="text-align: right">
                <b-form-checkbox type="checkbox" v-model="tableOptions.filters.is_superseded">
                  <span v-translate>Show all versions</span>
                </b-form-checkbox>
              </b-col>
            </b-row>
          </template>
          <b-container fluid>
            <div class="mt-2 mb-2 dashboard-filters all-submissions">
              <b-input-group :prepend="$gettext('Party')">
                <b-form-select
                  id="submission_party_filter"
                  :disabled="Boolean(currentUser.party)"
                  v-model="tableOptions.filters.party"
                  :options="sortOptionsParties"
                ></b-form-select>
              </b-input-group>
              <b-input-group :prepend="$gettext('Obligation')">
                <b-form-select
                  id="submission_obligation_filter"
                  v-model="tableOptions.filters.obligation"
                  :options="sortOptionsObligation"
                ></b-form-select>
              </b-input-group>
              <b-input-group :prepend="$gettext('Status')">
                <b-form-select
                  id="submission_status_filter"
                  v-model="tableOptions.filters.currentState"
                  :options="sortOptionsStatus"
                ></b-form-select>
              </b-input-group>
              <b-input-group class="w120" :prepend="$gettext('From')">
                <b-form-select
                  id="submission_from_filter"
                  v-model="tableOptions.filters.period_start"
                  :options="sortOptionsPeriodFrom"
                ></b-form-select>
              </b-input-group>
              <b-input-group class="w120" :prepend="$gettext('To')">
                <b-form-select
                  id="submission_to_filter"
                  v-model="tableOptions.filters.period_end"
                  :options="sortOptionsPeriodTo"
                ></b-form-select>
              </b-input-group>
              <b-btn variant="light" id="submission_clear_button" @click="clearFilters">
                <span v-translate>Clear</span>
              </b-btn>
            </div>
            <b-table
              id="all-submissions-table"
              show-empty
              outlined
              bordered
              hover
              no-local-sorting
              head-variant="light"
              stacked="md"
              :items="tableItems"
              :fields="tableFields"
              :per-page="tableOptions.perPage"
              :sort-by.sync="tableOptions.sorting.sortBy"
              :sort-desc.sync="tableOptions.sorting.sortDesc"
              :sort-direction="tableOptions.sorting.sortDirection"
              ref="table"
            >
              <template v-slot:cell(actions)="row">
                <b-button-group>
                  <router-link
                    class="btn btn-light btn-sm"
                    :to="{ name: getFormName(row.item.details.obligation), query: { submission: row.item.details.id, edit_mode: row.item.details.can_edit_data && !currentUser.is_read_only }}"
                  >
                    <span
                      v-if="row.item.details.can_edit_data && !currentUser.is_read_only"
                    >{{labels['edit']}}</span>
                    <span v-else>{{labels['view']}}</span>
                  </router-link>
                </b-button-group>
              </template>
            </b-table>

            <b-row>
              <b-col md="10" class="mt-1 mb-3">
                <b-pagination
                  :total-rows="tableOptions.totalRows"
                  :per-page="tableOptions.perPage"
                  v-model="tableOptions.currentPage"
                  class="my-0"
                />
              </b-col>
              <b-col md="2">
                <b-input-group horizontal :prepend="$gettext('Per page')" class="mb-0">
                  <b-form-select :options="table.pageOptions" v-model="tableOptions.perPage"/>
                </b-input-group>
              </b-col>
            </b-row>
          </b-container>
        </b-card>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { cloneSubmission } from '@/components/common/services/api'
import Multiselect from '@/components/common/ModifiedMultiselect'
import { getCommonLabels } from '@/components/common/dataDefinitions/labels'
import { getAlerts } from '@/components/common/dataDefinitions/alerts'
import { dateFormatToDisplay } from '@/components/common/services/languageService.js'

export default {
  name: 'Dashboard',
  data() {
    return {
      dataLoaded: false,
      alerts: getAlerts(this.$gettext),
      submissionNew: {
        obligation: null,
        reporting_period: null,
        party: null
      },
      table: {
        pageOptions: [10, 25, 100]
      },
      tableOptionsCurrentPageWasSetFromWatcher: false,
      dataEntryTable: {
        currentPage: 1,
        perPage: 5,
        totalRows: 0,
        sorting: {
          sortBy: 'updated_at',
          sortDesc: true,
          sortDirection: 'asc'
        },
        search: null,
        filters: {
          period_start: null,
          period_end: null,
          obligation: null,
          party: null
        },
        pageOptions: [5, 10, 25, 100]
      }
    }
  },

  async created() {
    if (!this.$store.state.currentUser) {
      await this.$store.dispatch('getMyCurrentUser')
    }
    document.querySelector('body').classList.remove('aside-menu-lg-show')
    this.$store.dispatch('getDashboardParties')
    this.$store.dispatch('getDashboardObligations')
    this.$store.dispatch('fetchSubmissionStates')

    await this.$store.dispatch('getDashboardPeriods')
    const submissionDefaultValues = await this.$store.dispatch('getSubmissionDefaultValues')
    const defaultPeriod = this.$store.getters.defaultPeriod(submissionDefaultValues)
    const reporting_period = defaultPeriod.value
    let defaultObligation = null
    if (submissionDefaultValues.obligation) {
      defaultObligation = this.$store.getters.defaultObligation(submissionDefaultValues)
      if (this.currentUser.is_secretariat) {
        this.tableOptions.filters.obligation = defaultObligation
        this.tableOptions.filters.period_start = defaultPeriod.start_date
      }
    }

    this.submissionNew = {
      ...this.submissionNew,
      ...submissionDefaultValues,
      reporting_period,
      obligation: defaultObligation
    }
    this.$store.dispatch('getCurrentSubmissions')

    this.updateBreadcrumbs()
  },

  components: {
    Multiselect
  },

  computed: {

    ...mapGetters(['getSubmissionInfo']),

    /* The problem

		Using item provider function as indicated in the documentation (https://bootstrap-vue.js.org/docs/components/table)
		for async pagination and filtering raises a few problems if the provider function or the function that fetches the data,
		also used in the provider function is called outside of the internal filter/pagination change watcher,
		like deleting an entry and trying to update the table after.

		Actually, the async call had some problems even if the calls where within the specified parameters, like perPage fiter.

		The solution

		1.Table items are provided to the table through a computed method that iterates through the list obtained via the async call.
		2.Filters/pagination are no longer specifically binded to the table. Instead, we use a watcher on tableOptions,
			doing a call for getting the filtered list of submissions every
		 	time a option changes in the tableOptions object, like pagination, filtering, perpage etc.
		3.Because the data is provided via computed, the table data also updates in the interface every time we get a new list of submissions,
			after doing actions like deleting, cloning or changing the state of a submission. */

    tableItems() {
      const tableFields = []
      if (this.submissions && this.submissions.length) {
        this.submissions.forEach((element) => {
          tableFields.push({
            obligation: this.getSubmissionInfo(element).obligation(),
            reporting_period: this.getSubmissionInfo(element).period_description(),
            party: this.getSubmissionInfo(element).party(),
            current_state: element.flag_superseded ? `${this.labels[element.current_state]} (${this.labels.flags.flag_superseded})` : this.labels[element.current_state],
            version: element.version,
            updated_at: dateFormatToDisplay(element.updated_at),
            created_by: element.filled_by_secretariat ? this.$gettext('Secretariat') : this.$gettext('Party'),
            details: element
          })
        })
      }
      return tableFields
    },
    labels() {
      return getCommonLabels(this.$gettext)
    },
    tableFields() {
      return [{
        key: 'obligation', label: this.$gettext('Obligation'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'reporting_period', label: this.$gettext('Period'), sortable: true, sortDirection: 'asc'
      }, {
        key: 'party', label: this.$gettext('Party'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'version', label: this.$gettext('Version'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'current_state', label: this.$gettext('Status'), sortable: true
      }, {
        key: 'updated_at', label: this.$gettext('Last modified'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'created_by', label: this.$gettext('Created by')
      }, {
        key: 'actions', label: this.$gettext('Actions')
      }]
    },
    dataEntryTableItems() {
      const tableFields = []
      const { filters } = this.dataEntryTable
      const filtersExist = Object.keys(filters).some(f => filters[f])
      if (this.mySubmissions && this.mySubmissions.length) {
        this.mySubmissions.forEach((element) => {
          if (filtersExist && this.checkFilters(filters, element)) {
            return
          }
          const row = {
            obligation: this.getSubmissionInfo(element).obligation(),
            reporting_period: this.getSubmissionInfo(element).period_description(),
            party: this.getSubmissionInfo(element).party(),
            version: element.version,
            updated_at: dateFormatToDisplay(element.updated_at),
            created_by: element.filled_by_secretariat ? this.$gettext('Secretariat') : this.$gettext('Party'),
            details: element
          }
          tableFields.push(row)
        })
      }
      this.dataEntryTable.totalRows = tableFields.length
      return tableFields
    },
    dataEntryTableFields() {
      return [{
        key: 'obligation', label: this.$gettext('Obligation'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'reporting_period', label: this.$gettext('Period'), sortable: true
      }, {
        key: 'party', label: this.$gettext('Party'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'version', label: this.$gettext('Version'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'updated_at', label: this.$gettext('Last modified'), sortable: true, sortDirection: 'desc'
      }, {
        key: 'created_by', label: this.$gettext('Created by')
      }, {
        key: 'actions', label: this.$gettext('Actions')
      }]
    },

    obligationsOptions() {
      return this.obligations.filter(a => a.is_active)
    },
    sortOptionsPeriodFrom() {
      return 	Array.from(new Set(this.periods.map(f => {
        if (this.tableOptions.filters.period_end !== null
				&& f.start_date > this.tableOptions.filters.period_end) {
          return null
        }
        return {
          text: f.start_date.split('-')[0],
          value: this.getStartDateOfYear(f.start_date)
        }
      }).filter(f => f !== null).map(JSON.stringify))).map(JSON.parse).sort((a, b) => parseInt(b.text) - parseInt(a.text))
    },

    sortOptionsPeriodTo() {
      return 	Array.from(new Set(this.periods.map(f => {
        if (this.tableOptions.filters.period_start !== null
				&& f.end_date < this.tableOptions.filters.period_start) {
          return null
        }
        return {
          text: f.end_date.split('-')[0],
          value: this.getEndDateOfYear(f.end_date)
        }
      }).filter(f => f !== null).map(JSON.stringify))).map(JSON.parse).sort((a, b) => parseInt(b.text) - parseInt(a.text))
    },

    sortOptionsPeriodFromDataEntry() {
      return 	Array.from(new Set(this.periods.map(f => {
        if (this.dataEntryTable.filters.period_end !== null
				&& f.start_date > this.dataEntryTable.filters.period_end) {
          return null
        }
        return {
          text: f.start_date.split('-')[0],
          value: this.getStartDateOfYear(f.start_date)
        }
      }).filter(f => f !== null).map(JSON.stringify))).map(JSON.parse).sort((a, b) => parseInt(b.text) - parseInt(a.text))
    },

    sortOptionsPeriodToDataEntry() {
      return 	Array.from(new Set(this.periods.map(f => {
        if (this.dataEntryTable.filters.period_start !== null
				&& f.end_date < this.dataEntryTable.filters.period_start) {
          return null
        }
        return {
          text: f.end_date.split('-')[0],
          value: this.getEndDateOfYear(f.end_date)
        }
      }).filter(f => f !== null).map(JSON.stringify))).map(JSON.parse).sort((a, b) => parseInt(b.text) - parseInt(a.text))
    },

    sortOptionsObligation() {
      return this.obligations
    },

    sortOptionsStatus() {
      if (this.submissionStates) {
        return [
          { text: 'Any', value: null },
          ...Object.keys(this.submissionStates).map(state => ({
            // TODO: use backend names instead of getCommonLabels?
            // text: this.submissionStates[state],
            text: getCommonLabels(this.$gettext)[state],
            value: state
          }))
        ]
      }
      return []
    },

    sortOptionsParties() {
      return this.parties
    },

    dataReady() {
      if (this.submissions
        && this.periods
        && this.currentUser
        && this.obligations
        && this.parties
        && this.submissionStates
        && this.submissions.length
        // && Object.values(this.submissionNew).some(value => value)
      ) {
        return true
      }
      return false
    },
    tableOptions() {
      return this.$store.state.dashboard.table
    },
    currentUser() {
      const { currentUser } = this.$store.state
      if (currentUser) {
        this.submissionNew.party = currentUser.party
      }
      return currentUser || {}
    },
    periods() {
      return this.$store.state.dashboard.periods
    },
    parties() {
      return this.$store.state.dashboard.parties
    },
    submissionStates() {
      return this.$store.state.submissionStates
    },
    obligations() {
      return this.$store.state.dashboard.obligations
    },
    submissions() {
      return this.$store.state.dashboard.submissions
    },
    mySubmissions() {
      return this.$store.state.dashboard.mySubmissions
    },

    basicDataReady() {
      if (this.periods
				&& this.obligations
				&& this.currentUser
				&& this.parties) {
        this.dataLoaded = true
        return true
      }
      return false
    },
    tableOptionsExceptFilters() {
      const { sorting, currentPage, perPage } = this.$store.state.dashboard.table
      const tableOptions = {
        sorting,
        currentPage,
        perPage
      }
      return tableOptions
    }
  },

  methods: {
    sortCompare(a, b, key, direction) {
      const placeholder = direction ? '1000' : '3000'
      if (key === 'updated_at') {
        const first = a[key] !== undefined ? new Date(a[key]) : new Date(placeholder)
        const second = b[key] !== undefined ? new Date(b[key]) : new Date(placeholder)
        if (first > second) {
          return 1
        }
        if (first < second) {
          return -1
        }
        if (first === second) {
          return 0
        }
      }
      return null
    },

    getStartDateOfYear(year) {
      const currentYear = year.split('-')
      currentYear[1] = '01'
      currentYear[2] = '01'
      return currentYear.join('-')
    },

    getEndDateOfYear(year) {
      const currentYear = year.split('-')
      currentYear[1] = '12'
      currentYear[2] = '31'
      return currentYear.join('-')
    },

    updateBreadcrumbs() {
      this.$store.commit('updateBreadcrumbs', `${this.$gettext('Dashboard')} | ${this.$gettext('Online Reporting System')}`)
    },
    addSubmission() {
      this.$store.dispatch('addSubmission', {
        $gettext: this.$gettext,
        submission: this.submissionNew
      }).then(r => {
        this.$store.dispatch('getMyCurrentSubmissions').then(() => {
          const currentSubmission = this.mySubmissions.find(sub => sub.id === r.id)
          this.$router.push({ name: this.getFormName(r.obligation), query: { submission: currentSubmission.id, edit_mode: true } })
        })
      })
    },
    clearFilters() {
      Object.keys(this.tableOptions.filters).forEach(key => {
        if (this.currentUser.party && key === 'party') {
          return
        }
        this.tableOptions.filters[key] = null
      })
    },
    clone(submissionId, obligation) {
      cloneSubmission(submissionId).then((response) => {
        this.$router.push({ name: this.getFormName(obligation), query: { submission: response.data.id } })
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { __all__: [this.alerts.new_version_created] },
          variant: 'success'
        })
        this.$destroy()
      }).catch(error => {
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { ...error.response.data },
          variant: 'danger' })
        console.log(error)
      })
    },

    checkFilters(filters, element) {
      if (filters.obligation && element.obligation !== filters.obligation) {
        return true
      }
      if (filters.party && element.party !== filters.party) {
        return true
      }
      if (filters.period_start && parseInt(this.getSubmissionInfo(element).period()) < parseInt(filters.period_start.split('-')[0])) {
        return true
      }
      if (filters.period_end && parseInt(this.getSubmissionInfo(element).period()) > parseInt(filters.period_end.split('-')[0])) {
        return true
      }
      return false
    },

    removeSubmission(id) {
      this.$store.dispatch('removeSubmission', {
        $gettext: this.$gettext,
        submissionId: id
      })
    },
    getFormName(obligation) {
      return this.obligations.find(o => o.value === obligation).obligation_type
    },
    onFiltered(filteredItems) {
      this.dataEntryTable.totalRows = filteredItems.length
      this.dataEntryTable.currentPage = 1
    }
  },

  watch: {
    '$language.current': {
      handler() {
        this.updateBreadcrumbs()
      }
    },
    'tableOptions.filters': {
      handler() {
        if (this.dataLoaded) {
          if (this.tableOptions.currentPage !== 1) {
            this.tableOptions.currentPage = 1
            this.tableOptionsCurrentPageWasSetFromWatcher = true
          }
          this.$store.dispatch('getCurrentSubmissions')
          if (!this.$refs.table) return
          this.$refs.table.refresh()
        }
      },
      deep: true
    },
    tableOptionsExceptFilters: {
      handler() {
        console.log(this.dataLoaded)

        if (this.dataLoaded) {
          if (this.tableOptionsCurrentPageWasSetFromWatcher) {
            this.tableOptionsCurrentPageWasSetFromWatcher = false
            return
          }
          this.$store.dispatch('getCurrentSubmissions')
        }
      },
      deep: true
    }
  }
}
</script>

<style lang="scss">
.dashboard-page {
  .dashboard-filters.all-submissions {
    flex-wrap: wrap;
    button {
      width: calc(10% - 5px);
    }
    .input-group {
      width: calc(30% - 5px);
      &:nth-child(1) {
        width: calc(35% - 5px);
        margin-bottom: 5px;
      }
      &:nth-child(2) {
        width: calc(65% - 5px);
        margin-bottom: 5px;
      }
    }
  }
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.5s;
  }
  .fade-enter,
  .fade-leave-to {
    opacity: 0;
  }

  .detail-header {
    margin-bottom: 0.5rem;
  }
  .dashboard-filters {
    display: flex;
  }
  .dashboard-filters > div,
  .filter-group > div {
    margin-right: 5px;
    min-width: 140px;
  }

  .filter-group {
    display: flex;
  }
  .w120 {
    width: 120px;
  }

  tr:hover a.btn {
    color: black;
    background: #ddd;
  }
  .table-hover tbody tr:hover {
    background-color: transparent;
    td {
      background-color: rgba(0, 0, 0, 0.04);
    }
  }

}
</style>
