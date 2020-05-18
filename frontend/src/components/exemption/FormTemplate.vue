<template>
  <div :id="`${tabName}_tab`" v-if="tab_info">
    <div class="form-sections">
      <div class="table-wrapper">
        <div class="table-title">
          <h6>
            <span v-translate>Substances</span>
          </h6>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDelete)" v-if="selectedForDelete.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDelete.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="table.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input :class="{ highlighted: table.filters.search && table.filters.search.length }" v-model="table.filters.search"/>
            </b-input-group>
          </div>
          <i @click="table.tableFilters = !table.tableFilters" class="fa fa-filter fa-lg"></i>
        </div>

        <b-table
          show-empty
          outlined
          v-if="tableRows"
          bordered
          hover
          head-variant="light"
          stacked="md"
          class="submission-table full-bordered"
          id="substance-table"
          :items="tableRows"
          :fields="tableFields"
          :empty-text="tableEmptyText"
          :filter="table.filters.search"
          ref="table"
        >
          <template v-for="field in tableFields" v-slot:[`head(${field.key})`]="field">
            <div v-html="field.label" :key="field.key"></div>
          </template>
          <template v-slot:cell(group)="cell">
            <div class="group-cell">{{cell.item.group}}</div>
          </template>
          <template v-slot:cell(substance)="cell">
            <div class="substance-blend-cell">{{cell.item.substance}}</div>
          </template>
          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              v-show="canEditSubstanceData"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>
          <template
            v-for="inputField in tab_info.rowInputFields"
            v-slot:[`cell(${inputField})`]="cell"
          >
            <fieldGenerator
              :icon="cell.item.originalObj[inputField].icon"
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :field="cell.item.originalObj[inputField]"
              :disabled="!canEditSubstanceData"
              @icon-clicked="createModalData(cell.item.originalObj, cell.item.index)"
            />
          </template>

          <template v-slot:cell(validation)="cell">
            <b-btn-group class="row-controls">
              <span  @click="createModalData(cell.item.originalObj, cell.item.index)">
                <i
                  :class="{
                    'fa-pencil-square-o': !isActionReadOnly('edit', 'substance_data'),
                    'fa-eye': !isActionReadOnly('view', 'substance_data'),
                    'fa fa-lg': true
                  }"
                  :title="!isActionReadOnly('edit', 'substance_data') ? $gettext('Edit') : $gettext('View')"
                  v-b-tooltip
                ></i>
              </span>
              <span
                v-if="!isActionReadOnly('delete', 'substance_data')"
                @click="remove_field(cell.item.index)"
                class="table-btn"
              >
                <i class="fa fa-trash fa-lg" v-b-tooltip :title="$gettext('Delete')"></i>
              </span>
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.originalObj.validation.selected"
                :index="cell.item.index"
              />
            </b-btn-group>
          </template>
        </b-table>
      </div>
    </div>
    <div id="tab-comments" class="table-wrapper" v-if="tab_info.comments">
      <div
        v-for="(comment, comment_key) in tab_info.comments"
        :key="comment_key"
        class="comments-input"
      >
        <label>
          <span>{{labels[comment_key]}}</span>
        </label>
        <textarea
          @change="$store.commit('addComment', {data: $event.target.value, tab:tabName, field: comment_key})"
          :disabled="isRemarkReadOnly(comment_key)"
          class="form-control"
          :value="comment.selected"
        ></textarea>
      </div>
    </div>
    <hr>
    <AppAside
      v-if="canEditSubstanceData || validationLength > 0"
      fixed
    >
      <DefaultAside
        v-on:fillSearch="fillTableSearch($event)"
        :canEditSubstanceData="canEditSubstanceData"
        :parentTabIndex.sync="sidebarTabIndex"
        :hovered="hovered"
        :tabName="tabName"
      ></DefaultAside>
    </AppAside>

    <b-modal size="lg" ref="edit_modal" id="edit_modal" @hide="modal_data = null">
      <div v-if="modal_data" slot="modal-title">
        <span
          v-if="modal_data.field.substance.selected"
          v-translate="{name: tab_data.display.substances[modal_data.field.substance.selected]}"
        >Edit %{name} substance</span>
      </div>
      <div v-if="modal_data">
        <p class="muted">
          <span
            v-translate
          >All the quantity values should be expressed in metric tons (not ODP or CO₂-equivalent tonnes).</span>
          <br>
          <b>
            <span v-translate>The values are saved automatically in the table, as you type.</span>
          </b>
        </p>
        <b-row v-if="modal_data.field.substance.selected">
          <b-col>
            <span v-translate>Change substance</span>
          </b-col>
          <b-col>
            <multiselect
              class="mb-2"
              @input="updateFormField($event, {index:modal_data.index,tabName: tabName, field:'substance'})"
              trackBy="value"
              :disabled="!canEditSubstanceData"
              :hide-selected="true"
              label="text"
              :placeholder="$gettext('Select substance')"
              :value="parseInt(modal_data.field.substance.selected)"
              :options="tab_data.substances"
            />
          </b-col>
        </b-row>
        <div class="mb-3" v-for="modalField in tab_info.rowInputFields" :key="modalField">
          <b-row>
            <b-col>
              <span>{{labels[modalField]}}</span>
            </b-col>
            <b-col>
              <fieldGenerator
                :fieldInfo="{index:modal_data.index, tabName: tabName, field:modalField}"
                :disabled="!canEditSubstanceData"
                :field="modal_data.field[modalField]"
              />
            </b-col>
          </b-row>
        </div>
        <div v-if="tabName === 'approved'">
          <div v-translate class="mb-2">Agreed critical use categories</div>
          <b-row>
            <b-col>
              <addCategories
                :index="modal_data.index"
                :tabName="tabName"
                v-if="canEditSubstanceData"
              ></addCategories>
            </b-col>
          </b-row>
          <b-row
              class="mb-2 special"
              v-for="category in modal_data.field.approved_uses"
              :key="category.critical_use_category"
            >
              <b-col cols="5">{{$store.state.initialData.display.criticalUseCategoryList[category.critical_use_category]}}</b-col>
              <b-col>
                <fieldGenerator
                  :fieldInfo="{ index:modal_data.index,tabName: tabName, field: category, category: category.critical_use_category }"
                  :field="category"
                  :disabled="!canEditSubstanceData"
                />
              </b-col>
              <b-col cols="1" v-if="!isActionReadOnly('delete', 'substance_data')" class="d-flex align-items-center">
                <i class="fa fa-trash fa-lg cursor-pointer d-flex align-items-center" @click="$store.commit('removeFormField', { index: modal_data.index, tabName: tabName, fieldName: 'approved_uses', fieldIndex: modal_data.field.approved_uses.indexOf(category)})"></i>
              </b-col>
            </b-row>
          <hr>
        </div>
      </div>
      <div slot="modal-footer">
        <b-btn @click="$refs.edit_modal.hide()" variant="success">
          <span v-translate>Close</span>
        </b-btn>
      </div>
    </b-modal>
  </div>
</template>

<script>
import FormTemplateMixin from '@/components/common/mixins/FormTemplateMixin'
import ValidationLabel from '@/components/common/form-components/ValidationLabel'
import { getLabels } from '@/components/exemption/dataDefinitions/labels'
import DefaultAside from '@/components/exemption/form-components/DefaultAside'
import addCategories from '@/components/raf/AddCategories'

export default {
  mixins: [FormTemplateMixin],
  components: {
    ValidationLabel, DefaultAside, addCategories
  },
  data() {
    return {
      tableRows: null,
      labels: null
    }
  },

  computed: {
    tableEmptyText() {
      if (this.readOnly) {
        return this.$gettext('This table shows substances and amounts once the secretariat processes your submission')
      }
      return this.$gettext('Please use the form on the right sidebar to add substances')
    },
    tableItems() {
      const tableFields = []
      this.tab_info.form_fields.forEach(form_field => {
        const tableRow = {}
        for (const key of Object.keys(form_field)) {
          if (key === 'quantity_use_categories') continue
          if (form_field.substance.selected) {
            tableRow[key] = this.typeOfDisplayObj[key]
              ? this.$store.state.initialData.display[
                this.typeOfDisplayObj[key]
              ][form_field[key].selected]
              : (tableRow[key] = form_field[key].selected)
          }
        }
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
    }
  },

  created() {
    const labels = getLabels(this.$gettext)
    this.labels = {
      ...labels[this.tab_info.name]
    }
    this.setTableRows()
  },
  methods: {
    fillTableSearch(data) {
      if (data.substance) {
        this.table.filters.search = data.substance
        this.table.tableFilters = true
      }
    },
    setTableRows() {
      const tableRows = []
      this.tab_info.form_fields.forEach((form_field) => {
        const tableRow = {}
        for (const key of Object.keys(form_field)) {
          if (key === 'quantity_use_categories') continue
          if (form_field.substance.selected) {
            tableRow[key] = this.typeOfDisplayObj[key]
              ? this.$store.state.initialData.display[
                this.typeOfDisplayObj[key]
              ][form_field[key].selected]
              : (tableRow[key] = form_field[key].selected)
          }
        }
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = form_field
          tableRow.index = this.tab_info.form_fields.indexOf(form_field)
          if (tableRow.originalObj.validation.selected.length) {
            tableRow.validation = 'invalid'
          } else {
            tableRow.validation = 'valid'
          }
          tableRows.push(tableRow)
        }
      })
      this.tableRows = tableRows
    }
  },
  watch: {
    '$language.current': {
      handler() {
        this.setLabels()
      }
    },
    'tab_info.form_fields': {
      handler() {
        if (this.$refs.edit_modal.is_show) {
          this.tableRows = []
          setTimeout(() => this.setTableRows(), 200)
        } else {
          this.setTableRows()
        }
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

<style lang="scss">
  table {
    .multiselect__content-wrapper {
      min-width: 300px;
    }
    td {
      vertical-align: middle!important;
    }
  }
</style>
