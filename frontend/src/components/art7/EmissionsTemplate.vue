<template>
  <div v-if="tab_info" id="has_emissions_tab">
    <h5
      class="errorHeading"
      v-if="$store.state.form.tabs.questionaire_questions.form_fields[tabName].selected === false && tab_info.form_fields.length"
    >The data in this form will not be saved because you have selected in the questionnaire "no" for this section</h5>
    <div class="form-sections">
      <div class="table-wrapper">
        <div class="table-title mb-3">
          <h4></h4>
          <b-btn class="mr-3" variant="outline-primary" @click="bulkRemove" v-if="selectedForDelete.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDelete.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="table.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Search all columns')">
              <b-form-input v-model="table.filters.search"/>
            </b-input-group>
          </div>
          <span>
            <i @click="table.tableFilters = !table.tableFilters" class="fa fa-filter fa-lg"></i>
          </span>
        </div>

        <b-table
          id="facility-table"
          show-empty
          outlined
          v-if="getTabInputFields"
          bordered
          hover
          head-variant="light"
          stacked="md"
          class="submission-table full-bordered"
          :items="tableItems"

          :fields="tableFields"
          :filter="table.filters.search"
          ref="table"
        >
          <template v-for="field in tableFields" v-slot:[`head(${field.key})`]>
            <div v-html="field.label" :key="field.key"></div>
          </template>
          <template v-slot:thead-top>
            <tr class="first-header">
              <th
                v-for="(header, header_index) in tab_info.section_headers"
                :colspan="header.colspan"
                :key="header_index"
              >
                <div
                  v-if="header.tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="header.tooltip"
                >
                  <span v-html="header.label"></span>
                  <i class="fa fa-info-circle fa-lg"></i>
                </div>
                <div v-else>
                  <span v-html="header.label"></span>
                </div>
              </th>
            </tr>
          </template>

          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :disabled="!$store.getters.edit_mode"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>

          <template v-for="inputField in getTabInputFields" v-slot:[`cell(${inputField})`]="cell">
            <fieldGenerator
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :disabled="['remarks_os', 'remarks_party'].includes(inputField) ? getCommentFieldPermission(inputField) : !$store.getters.edit_mode"
              :field="cell.item.originalObj[inputField]"
            />
          </template>

          <template v-slot:cell(validation)="cell">
            <span
              class="row-controls"
              :key="`${cell.item.index}_validation_${tabName}_button`"
              v-if="$store.getters.edit_mode"
            >
              <i class="fa fa-trash fa-lg" @click="remove_field(cell.item.index)" ></i>&nbsp;
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.validation"
                :index="cell.item.index"
              />
            </span>
          </template>
        </b-table>
      </div>
      <b-btn v-if="$store.getters.edit_mode" id="add-facility-button" class="mb-2" variant="primary" @click="addField">
        <span v-translate>Add facility</span>
      </b-btn>
    </div>

    <div class="table-wapper">
      <div
        v-for="(comment, comment_key) in tab_info.comments"
        :key="comment_key"
        class="comments-input"
      >
        <label>{{labels[comment_key]}}</label>
        <!-- addComment(state, { data, tab, field }) { -->
        <textarea
          @change="$store.commit('addComment', {data: $event.target.value, tab:tabName, field: comment_key})"
          :disabled="getCommentFieldPermission(comment_key)"
          class="form-control"
          :value="comment.selected"
        ></textarea>
      </div>
    </div>

    <AppAside v-if="$store.getters.edit_mode || validationLength" fixed>
      <DefaultAside
        v-on:fillSearch="table.tableFilters = true; table.filters.search = $event.facility"
        :parentTabIndex.sync="sidebarTabIndex"
        :hovered="hovered"
        :tabName="tabName"
      ></DefaultAside>
    </AppAside>
  </div>
</template>

<script>

import fieldGenerator from '@/components/common/form-components/fieldGenerator'
import ValidationLabel from '@/components/common/form-components/ValidationLabel'
import inputFields from '@/components/art7/dataDefinitions/inputFields'
import DefaultAside from '@/components/common/form-components/DefaultAside'
import { Aside as AppAside } from '@coreui/vue'
import { getLabels } from '@/components/art7/dataDefinitions/labels'

export default {
  props: {
    tabName: String,
    tabId: Number,
    tabIndex: Number
  },

  components: {
    fieldGenerator,
    AppAside,
    DefaultAside,
    ValidationLabel
  },

  created() {
    this.labels = getLabels(this.$gettext)[this.tab_info.name]
  },

  data() {
    return {
      modal_data: null,
      modal_comments: null,
      hovered: null,
      sidebarTabIndex: 0,
      table: {
        currentPage: 1,
        totalRows: 5,
        tableFilters: false,
        filters: {
          search: null,
          period_start: null,
          period_end: null,
          obligation: null,
          party: null,
          isCurrent: null
        }
      }
    }
  },

  computed: {
    selectedForDelete() {
      return this.tab_info.form_fields.filter(field => field.checkForDelete.selected).map(field => this.tab_info.form_fields.indexOf(field))
    },
    validationLength() {
      return this.$store.getters.getValidationForCurrentTab(this.tabName).filter(field => field.validation.length).length
    },
    tableItems() {
      const tableFields = []
      this.tab_info.form_fields.forEach(form_field => {
        const tableRow = {}
        Object.keys(form_field).forEach(key => {
          tableRow[key] = form_field[key].selected
        })
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = form_field
          tableRow.index = this.tab_info.form_fields.indexOf(form_field)
          tableFields.push(tableRow)
        }
      })
      this.table.totalRows = tableFields.length
      return tableFields
    },
    tableFields() {
      const tableHeaders = []
      const options = { class: 'text-center' }
      this.tab_info.section_subheaders.forEach((form_field) => {
        tableHeaders.push({
          key: form_field.name,
          label: form_field.label,
          ...options
        })
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
    hasInvalidFields() {
      return this.tab_info.form_fields.some(field => field.validation.selected.length)
    },
    tab_data() {
      return this.$store.state.initialData
    },
    getTabInputFields() {
      return this.intersect(inputFields, this.tab_info.fields_order)
    },

    isReadOnly() {
      return this.$store.getters.isReadOnly || this.hasDisabledFields
    }

  },

  methods: {
    remove_field(index) {
      this.$store.dispatch('removeField', { tab: this.tabName, index, $gettext: this.$gettext })
    },

    bulkRemove() {
      this.$store.commit('removeBulkFields', {
        tab: this.tabName,
        indexList: this.selectedForDelete,
        $gettext: this.$gettext
      })
    },

    getCommentFieldPermission(fieldName) {
      let type = fieldName.split('_')
      type = type[type.length - 1]
      if (type === 'party') {
        return !this.$store.getters.can_change_remarks_party || !this.$store.getters.edit_mode
      }
      if (['secretariat', 'os'].includes(type)) {
        return !this.$store.getters.can_change_remarks_secretariat || !this.$store.getters.edit_mode
      }
    },

    rowHovered(item) {
      this.hovered = item.index
    },
    openValidation() {
      const body = document.querySelector('body')
      body.classList.add('aside-menu-lg-show')
    },
    intersect(a, b) {
      const setA = new Set(a)
      const setB = new Set(b)
      const intersection = new Set([...setA].filter(x => setB.has(x)))
      return Array.from(intersection)
    },
    addField() {
      this.$store.dispatch('createRow', {
        $gettext: this.$gettext,
        prefillData: null,
        currentSectionName: this.tabName
      })
    }
  },

  watch: {
    'tab_info.form_fields': {
      handler() {
        if (parseInt(this.tabId) === this.tabIndex) {
          if (this.tab_info.status !== 'edited') {
            this.tab_info.status = 'edited'
          }
        }
      },
      deep: true
    }
  }

}
</script>

<style lang="css" scoped>
.form-fields td:first-of-type {
  padding-left: 2rem;
}
.blend {
  font-weight: bold;
}

td {
  text-align: center !important;
}

tr.small td {
  border: 1px solid #444 !important;
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

.fa-info-circle {
  margin-left: 5px;
}
.first-header th:first-of-type {
  padding-left: 2rem;
}
</style>
