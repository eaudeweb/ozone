<template>
  <div class="lookup-tables-page container pt-3">
    <b-row class="mb-2">
      <b-col>
        <b-input-group :prepend="$gettext('Search')">
          <b-form-input id="blends-name-filter" v-model="table.filters.searchName"/>
        </b-input-group>
      </b-col>
      <b-col>
        <b-input-group id="blends-component-filter">
          <multiselect
            :max-height="250"
            :multiple="true"
            :clear-on-select="false"
            :hide-selected="false"
            :close-on-select="true"
            label="text"
            trackBy="value"
            :placeholder="$gettext('Components')"
            v-model="table.filters.selectedComponentsNames"
            :options="searchComponentOptions"
          />
          <b-input-group-append>
            <b-btn
              variant="light"
              :disabled="!table.filters.selectedComponentsNames.length"
              @click="toggleIsComponentsSortDirectionDesc"
            >
              <span v-translate>Sort</span>&nbsp;
              <i v-if="!table.filters.isComponentsSortDirectionDesc" class="fa fa-arrow-up"></i>
              <i v-if="table.filters.isComponentsSortDirectionDesc" class="fa fa-arrow-down"></i>
            </b-btn>
          </b-input-group-append>
        </b-input-group>
      </b-col>
      <b-col>
        <b-input-group-append>
          <b-btn
            id="blends-clear-button"
            variant="light"
            :disabled="isDisabledClearFilters"
            @click="clearFilters"
          >
            <span v-translate>Clear</span>
          </b-btn>
        </b-input-group-append>
      </b-col>
    </b-row>
    <b-table
      show-empty
      outlined
      bordered
      hover
      head-variant="light"
      stacked="md"
      :items="visibleBlends"
      :fields="tableFields"
      :current-page="table.currentPage"
      :per-page="table.perPage"
      :sort-by.sync="table.sortBy"
      :sort-desc.sync="table.sortDesc"
      :sort-direction="table.sortDirection"
      :filter="table.filters.searchName"
      @filtered="onFiltered"
      ref="table"
    >
      <template v-slot:cell(other_names)="data">
        <span v-if="data.item.other_names">{{data.item.other_names}}</span>
        <span v-else>
        </span>
      </template>

      <!--template slot="components" slot-scope="row">
        <b-table
          show-empty
          outlined
          bordered
          hover
          small
          head-variant="light"
          stacked="md"
          :items="row.item.components"
          :fields="tableComponentsFields"
          :current-page="tableComponents.currentPage"
          :per-page="tableComponents.perPage"
          ref="table"
        >
          <template slot="component_name" slot-scope="data">
            <div>{{data.item.component_name}}</div>
          </template>
        </b-table>
      </template-->
    </b-table>
  </div>
</template>

<script>
import './styles.css'
import Multiselect from '@/components/common/ModifiedMultiselect'

const blendsCompareByComponentPercent = (blend1, blend2, componentName, isDescending) => {
  const { percentage: componentPercentageInBlend1 } = blend1.components.find(component => component.component_name === componentName)
  const { percentage: componentPercentageInBlend2 } = blend2.components.find(component => component.component_name === componentName)
  if (isDescending) {
    return componentPercentageInBlend2 - componentPercentageInBlend1
  }
  return componentPercentageInBlend1 - componentPercentageInBlend2
}

export default {
  components: {
    Multiselect
  },
  data() {
    return {
      table: {
        currentPage: 1,
        perPage: Infinity,
        filters: {
          searchName: null,
          selectedComponentsNames: [],
          isComponentsSortDirectionDesc: true
        }
      },
      tableComponents: {
        currentPage: 1,
        perPage: Infinity
      }
    }
  },
  computed: {
    tableFields() {
      return [{
        key: 'blend_id', label: this.$gettext('Name'), sortable: true, class: 'text-left'
      }, {
        key: 'type', label: this.$gettext('Type'), class: 'text-center'
      }, {
        key: 'odp', label: this.$gettext('ODP'), class: 'text-right'
      }, {
        key: 'gwp', label: this.$gettext('GWP'), class: 'text-right'
      }, {
        key: 'composition', label: this.$gettext('Composition'), class: 'text-left'
      /* }, {
        key: 'components', label: this.$gettext('Components'), class: 'text-center' */
      }, {
        key: 'other_names', label: this.$gettext('Other names'), sortable: true, class: 'text-center w-10'
      }, {
        key: 'trade_name', label: this.$gettext('Trade names'), sortable: true, class: 'text-center'
      }]
    },
    tableComponentsFields() {
      return [{
        key: 'component_name', label: this.$gettext('Name'), class: 'text-center'
      }, {
        key: 'percentage',
        label: this.$gettext('Percentage'),
        class: 'text-center',
        formatter: (value) => `${(value * 100).toFixed(2)}%`
      }]
    },
    isDisabledClearFilters() {
      const { filters } = this.table
      return !filters.searchName && !filters.selectedComponentsNames
    },
    searchComponentOptions() {
      const componentsAll = {}
      const { blends } = this.$store.state.initialData
      if (!blends) {
        return []
      }
      blends.forEach(blend => {
        blend.components.forEach(component => {
          componentsAll[component.component_name] = {
            value: component.component_name,
            text: component.component_name
          }
        })
      })
      return Object.values(componentsAll)
    },
    visibleBlends() {
      let visibleBlendsComputed = []
      const { blends } = this.$store.state.initialData
      const { selectedComponentsNames } = this.table.filters
      if (!blends) {
        return visibleBlendsComputed
      }
      blends.forEach(blend => {
        blend.components.forEach(component => {
          this.$store.commit('setBlendComponentRowVariant', { component })
        })
        const blendIsVisible = !selectedComponentsNames.length || selectedComponentsNames.every(
          selectedComponentName => blend.components.map(component => {
            if (selectedComponentsNames.includes(component.component_name)) {
              this.$store.commit('setBlendComponentRowVariant', { component, value: 'success' })
            }
            return component.component_name
          }).includes(selectedComponentName)
        )
        if (blendIsVisible) {
          visibleBlendsComputed.push(blend)
        }
      })

      if (this.table.filters.selectedComponentsNames.length) {
        visibleBlendsComputed = visibleBlendsComputed.sort((blend1, blend2) => blendsCompareByComponentPercent(blend1, blend2, this.table.filters.selectedComponentsNames[0], this.table.filters.isComponentsSortDirectionDesc))
      }

      return visibleBlendsComputed
    }
  },
  methods: {
    updateBreadcrumbs() {
      this.$store.commit('updateBreadcrumbs', `${this.$gettext('Mixtures')} | ${this.$gettext('Online Reporting System')}`)
    },
    onFiltered(filteredItems) {
      this.table.totalRows = filteredItems.length
      this.table.currentPage = 1
      this.table.filters.isComponentsSortDirectionDesc = true
    },
    filterCallback(blend) {
      const { searchName } = this.table.filters
      if (!searchName) {
        return true
      }
      return blend.blend_id && (
        blend.blend_id.toLowerCase().includes(searchName.toLowerCase())
				|| (blend.other_names && blend.other_names.toLowerCase().includes(searchName.toLowerCase())))
    },
    toggleIsComponentsSortDirectionDesc() {
      this.table.filters.isComponentsSortDirectionDesc = !this.table.filters.isComponentsSortDirectionDesc
    },
    clearFilters() {
      const { filters } = this.table
      filters.searchName = null
      filters.selectedComponentsNames = []
    }
  },
  watch: {
    '$language.current': {
      handler() {
        this.updateBreadcrumbs()
      }
    }
  },
  created() {
    this.$store.dispatch('getDashboardParties')
    // No need to filter by party here, the API will list all
    // the available blends for this user
    const body = document.querySelector('body')
    if (body.classList.contains('aside-menu-lg-show')) {
      document.querySelector('body').classList.remove('aside-menu-lg-show')
    }
    this.$store.dispatch('getCustomBlends', { party: undefined })
    this.updateBreadcrumbs()
  }
}
</script>
<style>
  .w-10 {
    width: 10%;
    min-width: 150px;
  }
</style>
