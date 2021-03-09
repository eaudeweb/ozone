<script>
import { Aside as AppAside } from '@coreui/vue'
import fieldGenerator from '@/components/common/form-components/fieldGenerator'
import DefaultAside from '@/components/common/form-components/DefaultAside'
import Multiselect from '@/components/common/ModifiedMultiselect'
import PermissionsMixin from './PermissionsMixin'

export default {
  mixins: [PermissionsMixin],

  props: {
    tabName: String,
    tabId: Number,
    tabIndex: Number
  },

  components: {
    fieldGenerator,
    AppAside,
    DefaultAside,
    Multiselect
  },

  data() {
    return {
      typeOfDisplayObj: {
        substance: 'substances',
        blend: 'blends',
        trade_party: 'countries',
        source_party: 'countries',
        destination_party: 'countries'
      },
      table: {
        tableFilters: false,
        pageOptions: [5, 25, 100],
        filters: {
          search: null,
          period_start: null,
          period_end: null,
          obligation: null,
          party: null,
          isCurrent: null
        }
      },

      tableBlends: {
        tableFilters: false,
        pageOptions: [5, 25, 100],
        filters: {
          search: null,
          period_start: null,
          period_end: null,
          obligation: null,
          party: null,
          isCurrent: null
        }
      },

      modal_data: null,
      labels: null,
      hovered: null,
      sidebarTabIndex: 0
    }
  },

  mounted() {
    const tables = document.querySelectorAll('body .tab-pane table')
    tables.forEach(t => {
      t.addEventListener('click', this.closeSidebar)
    })
  },

  computed: {
    selectedForDelete() {
      return this.tableItems.length && this.tableItems.filter(field => field.checkForDelete).map(field => field.index)
    },
    validationLength() {
      return this.$store.getters.getValidationForCurrentTab(this.tabName).filter(field => field.validation.length).length
    },
    selectedForDeleteBlends() {
      return this.tableItemsBlends.length && this.tableItemsBlends.filter(field => field.checkForDelete).map(field => field.index)
    },

    blendSubstanceHeaders() {
      return this.tab_info.blend_substance_headers.filter(header => !['substance', 'percent'].includes(header))
    },

    tableItems() {
      const tableFields = []
      this.tab_info.form_fields.forEach(form_field => {
        const tableRow = {}
        Object.keys(form_field).forEach(key => {
          if (form_field.substance.selected) {
            if (this.typeOfDisplayObj[key] && this.$store.state.initialData.display[this.typeOfDisplayObj[key]]) {
              tableRow[key] = this.$store.state.initialData.display[this.typeOfDisplayObj[key]][form_field[key].selected]
            } else {
              tableRow[key] = form_field[key].selected
            }
          }
        })
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = form_field
          tableRow.index = this.tab_info.form_fields.indexOf(form_field)
          tableRow._showDetails = true
          if (tableRow.originalObj.validation.selected.length) {
            tableRow.validation = 'invalid'
          } else {
            tableRow.validation = 'valid'
          }
          tableFields.push(tableRow)
        }
      })
      return tableFields
    },
    tableEmptyText() {
      if (this.isReadOnly) {
        return this.$gettext('There are no records to show')
      }
      return this.$gettext('Please use the form on the right sidebar to add substances')
    },
    tableItemsBlends() {
      const tableFields = []
      this.tab_info.form_fields.filter(
        form_field => form_field.blend.selected
      ).forEach(form_field => {
        const tableRow = {}
        Object.keys(form_field).forEach(key => {
          if (this.typeOfDisplayObj[key]) {
            if (this.typeOfDisplayObj[key] === 'blends') {
              const blend = this.tab_data.display[
                this.typeOfDisplayObj[key]
              ][form_field[key].selected] || {}
              tableRow[key] = blend.name || form_field[key].selected
            } else {
              tableRow[key] = this.tab_data.display[
                this.typeOfDisplayObj[key]
              ][form_field[key].selected]
            }
          } else if (form_field[key]) {
            tableRow[key] = form_field[key].selected
          }
        })
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = form_field
          tableRow._showDetails = false
          tableRow.index = this.tab_info.form_fields.indexOf(form_field)
          if (tableRow.originalObj.validation.selected.length) {
            tableRow.validation = 'invalid'
          } else {
            tableRow.validation = 'valid'
          }
          tableFields.push(tableRow)
        }
      })
      return tableFields
    },
    tableBlendsEmptyText() {
      if (this.isReadOnly) {
        return this.$gettext('There are no records to show')
      }
      return this.$gettext('Please use the form on the right sidebar to add mixtures')
    },
    tableFields() {
      const tableHeaders = []
      const options = {}
      this.tab_info.section_subheaders.forEach((form_field) => {
        options.class = form_field.class
        tableHeaders.push({
          key: form_field.name,
          label: form_field.label,
          width: form_field.width || null,
          ...options
        })
      })
      tableHeaders.unshift({
        key: 'checkForDelete',
        label: ''
      })
      return tableHeaders
    },

    tableFieldsBlends() {
      const tableHeaders = []
      const options = {}
      this.tab_info.section_subheaders.forEach((form_field) => {
        if (form_field.name === 'substance') {
          if (this.tabName === 'has_imports' && this.$route.name === 'art7') {
            tableHeaders.push({
              key: 'blend',
              label: `(2a) <br> ${this.$gettext('Mixture')}`,
              width: form_field.width || null,
              ...options
            })
          } else if (['has_destroyed', 'has_exports'].includes(this.tabName) && this.$route.name === 'art7') {
            tableHeaders.push({
              key: 'blend',
              label: `(1b) <br> ${this.$gettext('Mixture')}`,
              width: form_field.width || null,
              ...options
            })
          } else {
            tableHeaders.push({
              key: 'blend',
              label: `(2) <br> ${this.$gettext('Mixture')}`,
              width: form_field.width || null,
              ...options
            })
          }
        } else if (form_field.name === 'group') {
          if (['has_destroyed', 'has_exports'].includes(this.tabName) && this.$route.name === 'art7') {
            tableHeaders.push({
              key: 'type',
              label: `(1a) <br> ${this.$gettext('Type')}`,
              width: form_field.width || null,
              ...options
            })
          } else {
            tableHeaders.push({
              key: 'type',
              label: `(1) <br> ${this.$gettext('Type')}`,
              width: form_field.width || null,
              ...options
            })
          }
        } else {
          tableHeaders.push({
            key: form_field.name,
            label: form_field.label,
            width: form_field.width || null,
            ...options
          })
        }
      })
      tableHeaders.unshift({
        key: 'checkForDelete',
        label: ''
      })
      return tableHeaders
    },
    tab_info() {
      return this.$store.state.form.tabs[this.tabName]
    },
    tab_data() {
      return this.$store.state.initialData
    },

    isReadOnly() {
      const { isReadOnly } = this.$store.getters
      return isReadOnly
    }
  },

  methods: {
    closeSidebar(e) {
      if (!e.target.classList.contains('fa-exclamation-circle')) {
        const body = document.querySelector('body')
        body.classList.remove('aside-menu-lg-show')
      }
    },
    bulkRemove(indexList) {
      this.$store.dispatch('removeBulkFields', {
        tab: this.tabName,
        indexList,
        $gettext: this.$gettext
      })
    },
    fillTableSearch(data) {
      if (data.substance) {
        this.table.filters.search = data.substance
        this.table.tableFilters = true
      }
      if (data.blend) {
        this.tableBlends.filters.search = data.blend
        this.tableBlends.tableFilters = true
      }
    },
    updateFormField(value, fieldInfo) {
      this.$store.commit('updateFormField', {
        value,
        fieldInfo
      })
      if (fieldInfo.field === 'substance') {
        this.$store.commit('updateFormField', {
          value: this.getGroupBySubstance(value),
          fieldInfo: { index: fieldInfo.index, tabName: fieldInfo.tabName, field: 'group' }
        })
      }
    },

    getGroupBySubstance(value) {
      return this.tab_data.substances.find(g => value === g.value).group.group_id
    },

    getBlendType(selectedBlendId) {
      const selectedBlend = this.tab_data.blends.find(blend => selectedBlendId === blend.id)
      if (!selectedBlend) return 'Unknown'
      return selectedBlend.type
    },

    getMixtureComposition(mixture) {
      const totalNewQuantity = mixture.map(substance => substance.quantity_total_new).reduce((a, b) => a + b, 0)

      return mixture.map(substance => ({
        component_name: substance.substance,
        percentage: substance.quantity_total_new / totalNewQuantity,
        substance: this.tab_data.substances.find(tabDataSubstance => tabDataSubstance.text === substance.substance).value
      })).sort((a, b) => b.percentage - a.percentage)
    },

    expandedStatus(status) {
      if (status) return 'down'
      return 'right'
    },
    rowHovered(index) {
      this.hovered = index
    },

    openValidation(index) {
      this.rowHovered(index)
      const body = document.querySelector('body')
      if (this.tabName !== 'has_produced') {
        this.sidebarTabIndex = 2
      } else {
        this.sidebarTabIndex = 1
      }

      body.classList.add('aside-menu-lg-show')
    },

    pushUnique(array, item) {
      if (array.indexOf(item) === -1) {
        array.push(item)
      }
    },

    remove_field(index, noAlert) {
      this.$store.dispatch('removeField', {
        tab: this.tabName,
        index,
        $gettext: this.$gettext,
        noAlert
      })
    },

    splitBlend(value, percent) {
      percent *= 100
      if (value && value !== 0 && percent) {
        const count = (parseFloat(value) * parseFloat(percent)) / 100
        if (count === 0) {
          return ''
        } if (count < 0) {
          return count.toPrecision(3)
        } if (count > 999) {
          return parseInt(count)
        }
        return count.toPrecision(3)
      }
      return ''
    },

    createModalData(field, index) {
      this.modal_data = { field, index }
      this.$refs.edit_modal.show()
    }

  },

  watch: {
    'tab_info.form_fields': {
      handler() {
        if (parseInt(this.tabId) === this.tabIndex) {
          if (this.tab_info.status !== 'edited') {
            this.$store.commit('setTabStatus', {
              tab: this.tabName,
              value: 'edited'
            })
          }
        }
      },
      deep: true
    }
  }
}

</script>

<style lang="css" scoped>
  .blend {
    font-weight: bold;
  }

  td {
    text-align: center !important;
  }

  tr.small td {
    border-collapse: collapse;
    padding: 5px 0;
  }

  tr.small td .row {
    margin-left: 0;
    margin-right: 0;
  }

  tr.small td .row:not(:last-of-type) {
    border-bottom: 1px solid #444;
  }

  tr.small {
    background: white;
  }
  tr.small th {
    border: 1px solid #444;
  }

  .blend-name i {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
  }
  .subheader i {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
  }
  .subheader th > div {
    position: relative;
    margin-bottom: 0.5rem;
  }

  .comments-section {
    position: absolute;
    right: 0.5rem;
    z-index: 1;
  }

  /*  .submission-table tr td:last-of-type > * {
      max-width: 90%;
    }*/

  .comment-row {
    border-bottom: 3px solid #c8ced3;
    opacity: 0.9;
  }

  .fa-info-circle {
    margin-left: 5px;
  }

  td[rowspan="2"] {
    vertical-align: middle;
    border-right: 1px solid #c8ced3;
    border-bottom: 3px solid #c8ced3;
  }

  .validation-wrapper {
    display: block;
    font-size: 1rem;
  }

  .validation-wrapper:hover .fa-exclamation {
    font-weight: bold;
    color: black !important;
  }
  .header-only {
    margin-bottom: 0;
    border-bottom: none;
  }
  .modal-footer-info {
    position: absolute;
    left: 1rem;
  }
</style>
