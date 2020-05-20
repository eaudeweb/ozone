<template>
  <div v-if="tab_info">
    <div class="form-sections">
      <div class="table-wrapper">
        <div class="table-title mb-2">
          <div></div>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDelete)" v-if="selectedForDelete.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDelete.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="table.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input  :class="{ highlighted: table.filters.search && table.filters.search.length }"  v-model="table.filters.search"/>
            </b-input-group>
          </div>
          <i @click="table.tableFilters = !table.tableFilters" class="fa fa-filter fa-lg"></i>
        </div>

        <b-table
          show-empty
          outlined
          bordered
          hover
          head-variant="light"
          stacked="md"
          class="submission-table full-bordered"
          :items="tableItems"
          :fields="tableFields"
          :current-page="table.currentPage"
          :per-page="table.perPage"
          :sort-by.sync="table.sortBy"
          :sort-desc.sync="table.sortDesc"
          :sort-direction="table.sortDirection"
          :empty-text="tableEmptyText"
          :filter="table.filters.search"
          ref="table"
        >
          <template v-for="field in tableFields" v-slot:[`head(${field.key})`]="field">
            <div :style="`width: ${field.width ? field.width + 'px' : 'auto'}`" v-html="field.label" :key="field.key"></div>
          </template>

          <template v-slot:cell(substance)="cell">
            <div class="substance-blend-cell">{{cell.item.substance}}</div>
          </template>
          <template v-slot:cell(transferred_amount)="cell">
            <div class="text-right">{{cell.item.transferred_amount}}</div>
          </template>
          <template v-slot:cell(reporting_period)="cell">
            <div class="text-center">{{cell.item.reporting_period}}</div>
          </template>
          <template v-slot:cell(is_basic_domestic_need)="cell">
            <fieldGenerator
              style="text-align: center"
              :key="`${cell.item.index}_${'is_basic_domestic_need'}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'is_basic_domestic_need'}"
              :disabled="true"
              :field="cell.item.originalObj['is_basic_domestic_need']"
            ></fieldGenerator>
          </template>
          <template v-slot:cell(contain_technologies)="cell">
            <fieldGenerator
              :key="`${cell.item.index}_${'contain_technologies'}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'contain_technologies'}"
              :disabled="true"
              :field="cell.item.originalObj['contain_technologies']"
            ></fieldGenerator>
          </template>
        </b-table>
      </div>

    </div>

    <div class="table-wrapper">
      <div
        v-for="(comment, comment_key) in tab_info.comments"
        :key="comment_key"
        class="comments-input"
      >
        <label>
          <span>{{labels[comment_key]}}</span>
        </label>
        <!-- addComment(state, { data, tab, field }) { -->
        <textarea
          @change="$store.commit('addComment', {data: $event.target.value, tab:tabName, field: comment_key})"
          :disabled="isRemarkReadOnly(comment_key)"
          class="form-control"
          :value="comment.selected"
        ></textarea>
      </div>
    </div>

    <hr>

    <div class="footnotes">
      <p v-for="(footnote, footnote_index) in tab_info.footnotes" :key="footnote_index">
        <small>{{footnote}}</small>
      </p>
    </div>

  </div>
</template>

<script>
import FormTemplateMxin from '@/components/common/mixins/FormTemplateMixin'
import { getLabels } from '@/components/otherRo/dataDefinitions/labels'

export default {
  mixins: [FormTemplateMxin],

  data() {
    return {
      typeOfDisplayObj: {
        substance: 'substances',
        blend: 'blends'
      },
      types: {
        P: this.$gettext('Production'),
        C: this.$gettext('Consumption')
      }
    }
  },
  created() {
    const labels = getLabels(this.$gettext)
    this.labels = {
      ...labels.common,
      ...labels[this.tab_info.name]
    }
  },
  methods: {
  },
  computed: {
    tableItems() {
      const tableFields = []
      this.tab_info.form_fields.forEach(form_field => {
        const tableRow = {}
        Object.keys(form_field).forEach(key => {
          if (key === 'application') {
            tableRow[key] = form_field[key].selected + (form_field.decision.selected ? ` (${form_field.decision.selected})` : '')
          } else if (key === 'substance') {
            tableRow[key] = this.$store.state.initialData.display.substances[form_field[key].selected]
          } else if (key === 'source_party' || key === 'destination_party') {
            tableRow[key] = this.$store.state.initialData.display.countries[form_field[key].selected]
          } else if (key === 'reporting_period') {
            tableRow[key] = this.$store.state.initialData.display.periods[form_field[key].selected]
          } else if (key === 'transfer_type') {
            tableRow[key] = this.types[form_field[key].selected]
          } else {
            tableRow[key] = form_field[key].selected
          }
        })
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = form_field
          tableRow.index = this.tab_info.form_fields.indexOf(form_field)
          tableFields.push(tableRow)
        }
      })
      return tableFields
    },
    getTabInputFields() {
      return this.tab_info.input_fields
    },
    hasSubstances() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('substance')
    },
    hasBlends() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('blend')
    },
    tableCounter() {
      const counter = []
      if (this.hasSubstances) counter.push(1)
      if (this.hasBlends) counter.push(1)
      return counter.length
    }
  }
}
</script>
